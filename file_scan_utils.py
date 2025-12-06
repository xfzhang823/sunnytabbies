"""
file_scan_utils.py

Example:
python file_scan_utils.py \
  --dir "/mnt/h/Nikon D7500 pics and videos" \
  --out "/mnt/h/nikon_video_image_creation_date.csv" \
  --ext ".mp4,.mov,.jpg"

"""

from pathlib import Path
from datetime import datetime
import argparse
import subprocess
from typing import Optional, Sequence

import pandas as pd


def get_fps_ffprobe(path: Path) -> Optional[float]:
    """
    Use ffprobe to read avg_frame_rate and return fps as float.
    Requires ffmpeg/ffprobe to be installed.
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
        )
        rate = result.stdout.strip()  # e.g. "60/1" or "30000/1001"
        if "/" in rate:
            num, den = rate.split("/")
            num = float(num)
            den = float(den)
            if den == 0:
                return None
            return num / den
        return float(rate) if rate else None
    except Exception:
        return None


def scan_files(dir_path: str | Path, exts: Sequence[str]) -> pd.DataFrame:
    """
    Scan directory recursively and return DataFrame with:
    - name
    - created
    - fps (for video files, if available)
    """
    dir_path = Path(dir_path)

    # Normalize extensions: allow "mp4" or ".mp4"
    norm_exts = []
    for e in exts:
        e = e.lower()
        if not e.startswith("."):
            e = "." + e
        norm_exts.append(e)

    rows = []
    for p in dir_path.rglob("*"):
        if p.is_file() and p.suffix.lower() in norm_exts:
            created = datetime.fromtimestamp(p.stat().st_mtime)
            fps = get_fps_ffprobe(p)
            rows.append(
                {
                    "name": p.name,
                    "created": created,
                    "fps": fps,
                }
            )

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Scan directory for files and save created timestamps + FPS to CSV."
    )
    parser.add_argument("--dir", required=True, help="Directory to scan.")
    parser.add_argument(
        "--ext",
        nargs="+",
        required=True,
        help="One or more file extensions (e.g., --ext .mp4 .mov).",
    )
    parser.add_argument("--out", required=True, help="Output CSV filename.")

    args = parser.parse_args()

    df = scan_files(args.dir, args.ext)
    df.to_csv(args.out, index=False)
    print(f"Saved {len(df)} records to {args.out}")


if __name__ == "__main__":
    main()
