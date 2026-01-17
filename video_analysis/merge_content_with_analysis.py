"""
merge_content_with_analysis.py

Utility module (no main) to merge video-analysis results into kittens.json
(the media manifest file), using `asset_key` as the join key.

Call this from project root, e.g.:

    from merge_content_with_analysis import merge_content_with_analysis

    stats = merge_content_with_analysis(
        kittens_path="kittens.json",
        analysis_path="video_analysis_results.by_asset_key.json",
        out_path="kittens.merged.json",
        overwrite_existing=False,  # default: do NOT overwrite existing story/details/analysis
    )

    print(stats)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, unquote


def _read_json(path: str | Path) -> Any:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _derive_asset_key_from_item(item: Dict[str, Any]) -> Optional[str]:
    """
    Prefer item["asset_key"].

    Fallbacks (for older entries without asset_key):
      - poster filename: .../<asset_key>-poster.jpg
      - src filename stem
    """
    k = item.get("asset_key")
    if isinstance(k, str) and k.strip():
        return k.strip()

    poster = item.get("poster")
    if isinstance(poster, str) and poster.strip():
        name = Path(unquote(urlparse(poster).path)).name
        low = name.lower()
        for suffix in ("-poster.jpg", "-poster.jpeg", "-poster.png", "-poster.webp"):
            if low.endswith(suffix):
                return name[: -len(suffix)]
        return Path(name).stem

    src = item.get("src")
    if isinstance(src, str) and src.strip():
        name = Path(unquote(urlparse(src).path)).name
        return Path(name).stem if name else None

    return None


def _pick_story_details_meta(
    rec: Dict[str, Any],
) -> tuple[str, List[str], Optional[Dict[str, Any]]]:
    """
    Supports both:
      - normalized: { story, details, meta, analysis:{main_story, kitten_details} }
      - older:      { analysis:{main_story, kitten_details}, ... }
    """
    story = ""
    details: List[str] = []

    if isinstance(rec.get("story"), str) and rec["story"].strip():
        story = rec["story"].strip()

    if isinstance(rec.get("details"), list):
        details = [str(x) for x in rec["details"] if str(x).strip()]

    a = rec.get("analysis")
    if isinstance(a, dict):
        if not story and isinstance(a.get("main_story"), str):
            story = a["main_story"].strip()
        if not details and isinstance(a.get("kitten_details"), list):
            details = [str(x) for x in a["kitten_details"] if str(x).strip()]
        if not details and isinstance(a.get("details"), list):  # older variants
            details = [str(x) for x in a["details"] if str(x).strip()]

    meta = rec.get("meta")
    if isinstance(meta, dict):
        return story, details, meta

    # fallback: if no separate meta, keep analysis dict as provenance
    if isinstance(a, dict):
        return story, details, a

    return story, details, None


def merge_content_with_analysis(
    *,
    content_path: str | Path,
    analysis_path: str | Path,
    out_path: str | Path,
    overwrite_existing: bool = False,
) -> Dict[str, int]:
    """
    Merge analysis into kittens.json by asset_key.

    Inputs:
      - kittens.json: list of media items (your website content)
      - analysis json: {"by_asset_key": {"<asset_key>": {...}, ...}}

    Updates ONLY existing kittens items (no new inserts):
      - ensures item["asset_key"] exists (derived if missing)
      - fills or overwrites item["story"], item["details"], item["analysis"]

    overwrite_existing:
      - False (default): only fills missing story/details/analysis
      - True: overwrites existing story/details/analysis on match

    Returns simple stats:
      {"matched": N, "skipped": M, "missing_key": K, "no_match": J}
    """
    content = _read_json(content_path)
    analysis_root = _read_json(analysis_path)

    if not isinstance(content, list):
        raise TypeError("kittens.json must be a JSON list")

    if not (
        isinstance(analysis_root, dict)
        and isinstance(analysis_root.get("by_asset_key"), dict)
    ):
        raise TypeError("analysis file must be a dict with key 'by_asset_key' (dict)")

    by_asset_key: Dict[str, Any] = analysis_root["by_asset_key"]

    matched = 0
    skipped = 0
    missing_key = 0
    no_match = 0

    for item in content:
        if item.get("type") not in ("video", "youtube"):
            skipped += 1
            continue

        asset_key = _derive_asset_key_from_item(item)
        if not asset_key:
            missing_key += 1
            continue

        rec = by_asset_key.get(asset_key)
        if not isinstance(rec, dict):
            no_match += 1
            continue

        story, details, meta = _pick_story_details_meta(rec)

        # Persist join key
        item["asset_key"] = asset_key

        # story
        if story and (
            overwrite_existing
            or "story" not in item
            or not str(item.get("story", "")).strip()
        ):
            item["story"] = story

        # details
        if details and (
            overwrite_existing
            or "details" not in item
            or not isinstance(item.get("details"), list)
            or len(item.get("details", [])) == 0
        ):
            item["details"] = details

        # analysis/provenance
        if meta and (
            overwrite_existing
            or "analysis" not in item
            or not isinstance(item.get("analysis"), dict)
            or len(item.get("analysis", {})) == 0
        ):
            item["analysis"] = meta

        matched += 1

    _write_json(out_path, content)

    return {
        "matched": matched,
        "skipped": skipped,
        "missing_key": missing_key,
        "no_match": no_match,
    }
