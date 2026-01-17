"""
analyze_videos_with_gemini.py

Workflow:
- shrink original videos -> TEMP_DIR
- upload shrunk videos to Gemini Flash
- analyze with response_schema (Pydantic)
- write incremental results to LOG_FILE (resume-safe)

Design change:
- input is now an explicit list of video paths (caller controls which files to process)
- exposes a pipeline function instead of a main() CLI entrypoint
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional, List, Literal, Dict, Any, Sequence

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai

# from project
from video_analysis.video_utils import (
    shrink_video,
    wait_until_ready,
    load_existing_results,
    write_results,
)


# ----------------------------- Schema ------------------------------------


class VideoAnalysis(BaseModel):
    status: Literal["clear", "inconclusive", "multiple_subjects"] = Field(
        description=(
            "Classify whether the video content is clearly understandable. "
            "'clear' if the main subject/action is identifiable, "
            "'multiple_subjects' if there are several distinct focal subjects, "
            "'inconclusive' if the content cannot be determined from the video."
        )
    )
    main_story: str = Field(
        description=(
            "A warm, concise 2–3 sentence description of what happens in the video, "
            "including the mood and any notable moment. Do not assume details not visible."
        )
    )
    kitten_details: Optional[List[str]] = Field(
        default=None,
        description=(
            "Optional short bullet points of distinct visual details (e.g., colors, objects, "
            "clothing, animals, setting). Leave null if not applicable."
        ),
    )


# --------------------------- Configuration --------------------------------


@dataclass(frozen=True)
class Config:
    temp_dir: Path = Path("./temp_files")
    log_file: Path = Path("./site/assets/video_analysis_results.json")

    # Gemini model
    model_id: str = "gemini-3-flash-preview"

    # ffmpeg shrink settings
    shrink_width: int = 640
    shrink_fps: int = 1
    crf: int = 32
    preset: str = "ultrafast"
    audio_bitrate: str = "64k"

    # robustness
    ffmpeg_timeout_s: int = 60 * 30  # 30 min per file
    upload_poll_s: int = 5
    processing_max_wait_s: int = 60 * 10  # 10 min max processing wait
    delete_uploaded_files: bool = False  # set True if you want cleanup


def make_temp_name(original: Path) -> str:
    # stable + filesystem-safe
    return f"shrunk__{original.stem}.mp4"


def analyze_video(
    cfg: Config,
    client: genai.Client,
    shrunk_path: Path,
    original_path: Path,
) -> Dict[str, Any]:
    print(f"🧠 Analyzing: {original_path.name}")

    uploaded = client.files.upload(file=str(shrunk_path))
    uploaded = wait_until_ready(cfg, client, uploaded)

    prompt = (
        "You are helping write a kitten adoption gallery caption.\n"
        "Describe the video content in a warm, natural tone.\n"
        "Be concrete about what is visible; do not guess.\n"
        "If you can, note distinct kitten markings (paw colors, coats, stripes), setting, and mood.\n"
    )

    try:
        resp = client.models.generate_content(
            model=cfg.model_id,
            contents=[uploaded, prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": VideoAnalysis,
            },
        )

        value = resp.parsed  # do NOT annotate this

        if value is None:
            raise ValueError("Gemini returned no parsed content (resp.parsed is None).")

        if isinstance(value, VideoAnalysis):
            parsed: VideoAnalysis = value
        elif isinstance(value, dict):
            parsed = VideoAnalysis.model_validate(value)
        elif isinstance(value, BaseModel):
            # Sometimes SDK returns a BaseModel that isn't your class; try to coerce via dict
            parsed = VideoAnalysis.model_validate(value.model_dump())
        else:
            raise TypeError(f"Unexpected resp.parsed type: {type(value)}")

        return {
            "original_filename": original_path.name,
            "original_path": str(original_path),
            "shrunk_path": str(shrunk_path),
            "file_uri": getattr(uploaded, "uri", None),
            "timestamp": time.ctime(),
            "model_id": cfg.model_id,
            "analysis": parsed.model_dump(),
        }

    finally:
        if cfg.delete_uploaded_files:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass


def _normalize_paths(video_paths: Sequence[str | Path]) -> List[Path]:
    out: List[Path] = []
    for p in video_paths:
        pp = Path(p).expanduser()
        # keep relative paths relative to CWD (root caller), but normalize to absolute for logging/dedup
        out.append(pp.resolve())
    return out


def asset_key_from_path(p: Path) -> str:
    return Path(p.name).stem


def analyze_videos_with_gemini_pipeline(
    video_paths: Sequence[str | Path],
    cfg: Optional[Config] = None,
    *,
    client: Optional[genai.Client] = None,
    save_every: int = 1,
) -> Dict[str, Any]:
    """
    Analyze a set of videos using Gemini and persist results keyed by asset_key.

    This pipeline:
    - Accepts an explicit list of local video paths
    - Shrinks videos to temporary files as needed
    - Runs Gemini-based video analysis
    - Stores results in a dictionary keyed by `asset_key`
      (derived from the original filename stem)
    - Supports resuming from an existing log file without reprocessing
    - Writes results incrementally to disk for safety

    Args:
        video_paths:
            Sequence of video file paths to analyze.
        cfg:
            Optional Config override. Defaults are loaded from environment variables
            where available.
        client:
            Optional injected genai.Client. If not provided, a new client is created.
        save_every:
            Persist results to disk after processing every N videos.
            Default is 1 (safest).

    Returns:
        A dictionary of the form:
        {
            "by_asset_key": {
                "<asset_key>": {
                    "asset_key": str,
                    "analysis": {...} | None,
                    "error": str | None,
                    "meta": {...}
                },
                ...
            }
        }

    Notes:
        - `asset_key` is derived from the original filename (Path.stem) and is the
          primary join key for downstream merging (e.g., into kittens.json).
        - Results are deduplicated by asset_key, not by full file path.
        - This function is deterministic and safe to re-run.
    """
    load_dotenv()

    base_cfg = cfg or Config()
    cfg = replace(
        base_cfg,
        temp_dir=Path(os.getenv("TEMP_DIR", str(base_cfg.temp_dir))).resolve(),
        log_file=Path(os.getenv("LOG_FILE", str(base_cfg.log_file))).resolve(),
        model_id=os.getenv("MODEL_ID", base_cfg.model_id),
    )

    cfg.temp_dir.mkdir(parents=True, exist_ok=True)

    if client is None:
        client = genai.Client()

    # load / resume (NOW DICT)
    store = load_existing_results(cfg.log_file)
    by_asset_key: Dict[str, Any] = store.setdefault("by_asset_key", {})

    # dedupe by asset_key (NOT original_path)
    already_done = {
        k
        for k, r in by_asset_key.items()
        if isinstance(r, dict) and (r.get("analysis") or r.get("error"))
    }

    paths = _normalize_paths(video_paths)
    if not paths:
        print("⚠️ No video paths provided.")
        return store

    missing = [p for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Some input videos do not exist:\n" + "\n".join(str(p) for p in missing)
        )

    print(f"Will process {len(paths)} video(s)")
    print(f"Temp dir: {cfg.temp_dir}")
    print(f"Log file: {cfg.log_file}")
    print(f"Model: {cfg.model_id}\n")

    processed_since_save = 0

    for original_path in paths:
        asset_key = asset_key_from_path(Path(original_path))

        if asset_key in already_done:
            print(
                f"↩️ Skipping already-logged: {original_path.name} (asset_key={asset_key})"
            )
            continue

        shrunk_path = cfg.temp_dir / make_temp_name(original_path)

        try:
            if (
                shrunk_path.exists()
                and shrunk_path.stat().st_mtime >= original_path.stat().st_mtime
            ):
                print(f"📦 Using existing shrunk file: {shrunk_path.name}")
            else:
                shrink_video(cfg, original_path, shrunk_path)

            record = analyze_video(cfg, client, shrunk_path, original_path)

            # ✅ stamp asset_key so downstream merge is trivial
            if isinstance(record, dict):
                record["asset_key"] = asset_key

            # ✅ store by key
            by_asset_key[asset_key] = record
            processed_since_save += 1

            if processed_since_save >= save_every:
                write_results(cfg.log_file, store)
                processed_since_save = 0

            print(f"✅ Finished {original_path.name}\n")

        except Exception as e:
            err_record = {
                "asset_key": asset_key,
                "original_filename": original_path.name,
                "original_path": str(original_path),
                "shrunk_path": str(shrunk_path),
                "timestamp": time.ctime(),
                "model_id": cfg.model_id,
                "error": str(e),
            }
            by_asset_key[asset_key] = err_record
            write_results(cfg.log_file, store)
            print(f"❌ Error processing {original_path.name}: {e}\n")

    if processed_since_save:
        write_results(cfg.log_file, store)

    return store
