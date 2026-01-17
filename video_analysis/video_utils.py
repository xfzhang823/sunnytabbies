"""
video_analysis/video_utils.py

Small, reusable helpers for the video description pipeline:
- ffmpeg execution + shrinking
- incremental JSON persistence (resume-safe)
- Gemini upload polling until ready
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

from google import genai


# ----------------------------- ffmpeg helpers -----------------------------


def run_ffmpeg(cmd: List[str], timeout_s: int) -> None:
    """Run ffmpeg and raise a clear error if it fails."""
    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"ffmpeg timed out after {timeout_s}s") from e
    except subprocess.CalledProcessError as e:
        # Include a bit of stderr to make debugging possible.
        stderr = (e.stderr or "").strip()
        tail = "\n".join(stderr.splitlines()[-20:]) if stderr else ""
        msg = f"ffmpeg failed with exit code {e.returncode}"
        if tail:
            msg += f"\nffmpeg stderr (tail):\n{tail}"
        raise RuntimeError(msg) from e


def shrink_video(cfg: Any, input_path: Path, output_path: Path) -> None:
    """
    Shrink a video while keeping audio:
    - scale to cfg.shrink_width (preserve aspect)
    - fps=cfg.shrink_fps
    - h264 + aac audio

    Note: cfg is typed as Any to avoid circular imports; it just needs
    the expected attributes (shrink_width, shrink_fps, crf, preset, audio_bitrate, ffmpeg_timeout_s).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        f"scale={cfg.shrink_width}:-2,fps={cfg.shrink_fps}",
        "-c:v",
        "libx264",
        "-crf",
        str(cfg.crf),
        "-preset",
        str(cfg.preset),
        "-c:a",
        "aac",
        "-b:a",
        str(cfg.audio_bitrate),
        str(output_path),
    ]

    print(f"📦 Shrinking (with audio): {input_path.name} -> {output_path.name}")
    run_ffmpeg(cmd, timeout_s=int(cfg.ffmpeg_timeout_s))


# ----------------------------- JSON persistence ---------------------------


def load_existing_results(log_file: Path) -> Dict[str, Any]:
    if not log_file.exists():
        return {"by_asset_key": {}}

    data = json.loads(log_file.read_text(encoding="utf-8"))

    # New format
    if isinstance(data, dict) and isinstance(data.get("by_asset_key"), dict):
        return data

    # Old format (list) -> convert
    if isinstance(data, list):
        by_asset_key: Dict[str, Any] = {}
        for r in data:
            if not isinstance(r, dict):
                continue
            # Prefer explicit asset_key if present, else derive from filename
            k = r.get("asset_key") or Path(r.get("original_filename", "")).stem
            if k:
                by_asset_key[k] = r
        return {"by_asset_key": by_asset_key, "migrated_from_list": True}

    # Unknown -> start fresh
    return {"by_asset_key": {}}


def write_results(log_file: Path, data: Dict[str, Any]) -> None:
    """
    Atomically-ish write results JSON (simple overwrite).
    Ensures parent directory exists.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# ----------------------------- Gemini polling -----------------------------


def wait_until_ready(cfg: Any, client: genai.Client, uploaded_file: Any) -> Any:
    """
    Poll Gemini file state until ready or failed, with a max wait.

    Note: cfg is typed as Any to avoid circular imports; it just needs:
      - upload_poll_s
      - processing_max_wait_s
    """
    start = time.time()

    while True:
        state = getattr(uploaded_file, "state", None)
        state_name = getattr(state, "name", None)

        # Some SDKs might represent state differently; fall back to string.
        if state_name is None and state is not None:
            state_name = str(state)

        if state_name and str(state_name).upper() == "FAILED":
            raise RuntimeError(f"❌ Video processing failed: state={state_name}")

        # If not processing, consider it ready.
        if state_name and str(state_name).upper() != "PROCESSING":
            return uploaded_file

        if time.time() - start > float(cfg.processing_max_wait_s):
            raise RuntimeError(
                f"❌ Upload processing exceeded max wait ({cfg.processing_max_wait_s}s)"
            )

        print("⏳ Processing video frames...", end="\r")
        time.sleep(float(cfg.upload_poll_s))
        uploaded_file = client.files.get(name=uploaded_file.name)
