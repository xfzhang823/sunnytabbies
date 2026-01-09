"""
file_scan_utils.py

Example:
python file_scan_utils.py \
  --dir "/mnt/h/Nikon D7500 pics and videos" \
  --out "/mnt/h/nikon_media_scan.csv" \
  --ext .mp4 .mov .jpg .nef \
  --ffprobe-timeout 5 \
  --progress-every 200 \
  --log "/mnt/h/nikon_media_scan_errors.log"

python file_scan_utils.py \
  --dir "/mnt/h/Osmo pics and videos" \
  --out "/mnt/h/osmo_media_scan.csv" \
  --ext .mp4 .mov .jpg .nef \
  --ffprobe-timeout 5 \
  --progress-every 200 \
  --log "/mnt/h/osmo_media_scan_errors.log"
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import argparse
import subprocess
from typing import Optional, Sequence

import pandas as pd


VIDEO_EXTS_DEFAULT = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".wmv"}


def get_fps_ffprobe(path: Path, timeout_s: int) -> Optional[float]:
    """
    Use ffprobe to read avg_frame_rate and return fps as float.

    Key safety feature: timeout to prevent hanging on corrupt/bad files.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=avg_frame_rate",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_s,
        )

        rate = (result.stdout or "").strip()  # e.g. "60/1" or "30000/1001"
        if not rate:
            return None

        if "/" in rate:
            num_s, den_s = rate.split("/", 1)
            num = float(num_s)
            den = float(den_s)
            if den == 0:
                return None
            return num / den

        return float(rate)

    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None


def scan_files(
    dir_path: str | Path,
    exts: Sequence[str],
    ffprobe_timeout_s: int = 5,
    progress_every: int = 0,
    log_path: Optional[str | Path] = None,
    video_exts: Optional[set[str]] = None,
) -> pd.DataFrame:
    """
    Scan directory recursively and return DataFrame with:
    - path (full path)
    - name
    - ext
    - modified_time (mtime)   # used as "shoot time" proxy if file untouched
    - size_bytes
    - fps (videos only; None otherwise or on failure/timeout)
    - ffprobe_status ("ok" | "skip" | "timeout_or_error")
    """
    dir_path = Path(dir_path)
    video_exts = video_exts or set(VIDEO_EXTS_DEFAULT)

    # Normalize extensions: allow "mp4" or ".mp4"
    norm_exts: list[str] = []
    for e in exts:
        e = e.lower()
        if not e.startswith("."):
            e = "." + e
        norm_exts.append(e)

    log_f = None
    if log_path:
        log_path = Path(log_path)
        log_f = log_path.open("a", encoding="utf-8")

    def log(msg: str) -> None:
        if log_f:
            log_f.write(msg.rstrip() + "\n")
            log_f.flush()

    rows = []
    scanned = 0
    matched = 0

    try:
        for p in dir_path.rglob("*"):
            scanned += 1
            if progress_every and (scanned % progress_every == 0):
                print(f"[progress] scanned={scanned:,} matched={matched:,} last={p}")

            if not p.is_file():
                continue

            ext = p.suffix.lower()
            if ext not in norm_exts:
                continue

            matched += 1

            # Fast metadata
            st = p.stat()
            modified_time = datetime.fromtimestamp(st.st_mtime)
            size_bytes = st.st_size

            fps = None
            ffprobe_status = "skip"

            # Only run ffprobe on video-like extensions
            if ext in video_exts:
                fps = get_fps_ffprobe(p, timeout_s=ffprobe_timeout_s)
                ffprobe_status = "ok" if fps is not None else "timeout_or_error"
                if ffprobe_status != "ok":
                    log(
                        f"[ffprobe_fail] {p} (ext={ext}, size={size_bytes}, mtime={modified_time})"
                    )

            rows.append(
                {
                    "path": str(p),
                    "name": p.name,
                    "ext": ext,
                    "modified_time": modified_time,
                    "size_bytes": size_bytes,
                    "fps": fps,
                    "ffprobe_status": ffprobe_status,
                }
            )

    finally:
        if log_f:
            log_f.close()

    df = pd.DataFrame(rows)

    # Optional: stable sort so diffs are nicer
    if not df.empty:
        df = df.sort_values(
            ["ext", "modified_time", "name"], kind="stable"
        ).reset_index(drop=True)

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Scan directory for file modified timestamps + video FPS (safe: no hangs)."
    )
    parser.add_argument("--dir", required=True, help="Directory to scan.")
    parser.add_argument(
        "--ext",
        nargs="+",
        required=True,
        help="One or more file extensions (e.g., --ext .mp4 .mov .jpg .nef).",
    )
    parser.add_argument("--out", required=True, help="Output CSV filename.")
    parser.add_argument(
        "--ffprobe-timeout",
        type=int,
        default=5,
        help="Seconds before ffprobe is killed (prevents hangs). Default: 5",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=0,
        help="Print progress every N scanned paths (0 disables).",
    )
    parser.add_argument(
        "--log",
        default="",
        help="Optional log file for ffprobe failures/timeouts.",
    )

    args = parser.parse_args()

    df = scan_files(
        args.dir,
        args.ext,
        ffprobe_timeout_s=args.ffprobe_timeout,
        progress_every=args.progress_every,
        log_path=args.log or None,
    )
    df.to_csv(args.out, index=False)
    print(f"Saved {len(df)} records to {args.out}")


if __name__ == "__main__":
    main()
