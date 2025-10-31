#!/usr/bin/env python3
"""
Create image thumbnails and video poster frames.

Images:
  - Input:  JPG/PNG/WEBP (others Pillow supports)
  - Output: <name>-thumb.jpg, max width/height constrained

Videos:
  - Input:  MP4/MOV/M4V (anything ffmpeg can read)
  - Output: <name>-poster.jpg, grabbed at midpoint (or fallback time)

Skips outputs that already exist, unless --force is given.

Examples:
1) Process everything in ./media, write outputs next to originals (default)
python make_media_thumbs.py media

2) Process ./raw and write outputs to ./derived (mirrors subfolders)
python make_media_thumbs.py raw -o derived

3) Force-regenerate even if outputs exist
python make_media_thumbs.py media --force

4) Use a different size for image thumbs and posters
python make_media_thumbs.py media --thumb-size 700x700 --poster-width 1000

5) Grab poster at 1.5 seconds for all videos
python make_media_thumbs.py media --seek 1.5

"""
import os
import argparse

import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageOps


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}


def ensure_pillow():
    if Image is None:
        sys.exit(
            "Pillow not installed. Install with:  pip install Pillow\n"
            "Then re-run this script."
        )


def _is_outdated(src: Path, dst: Path) -> bool:
    """Return True if dst is missing or older than src."""
    if not dst.exists():
        return True
    try:
        return src.stat().st_mtime > dst.stat().st_mtime
    except Exception:
        return True


def make_image_thumb(
    src: Path,
    out_dir: Path,
    max_size: Tuple[int, int],
    quality: int = 82,
    force: bool = False,
) -> Optional[Path]:
    """
    Create <name>-thumb.jpg for an image with EXIF-aware orientation, LANCZOS
    downscale, and progressive/optimized JPEG. Returns output path or None if skipped.
    Skips when output exists and is newer unless force=True.
    """
    ensure_pillow()
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{src.stem}-thumb.jpg"

    if not force and not _is_outdated(src, dst):
        return None

    try:
        with Image.open(src) as im:
            # Normalize orientation first (handles common 90/180/270 EXIF rotations)
            im = ImageOps.exif_transpose(im)

            # Ensure 3-channels for JPEG
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            elif im.mode == "L":
                im = im.convert("RGB")

            # High-quality thumbnail
            im.thumbnail(max_size, resample=Image.Resampling.LANCZOS)

            # Save progressive, optimized JPEG (quality ~80-85 is a sweet spot)
            im.save(
                dst,
                "JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
                # subsampling values: 0=4:4:4 (sharper, bigger), 1=4:2:2, 2=4:2:0 (smaller)
                subsampling=1,
            )
        # Touch mtime to match src (optional; helpful for deterministic rebuilds)
        try:
            os.utime(dst, (src.stat().st_atime, src.stat().st_mtime))
        except Exception:
            pass
        return dst
    except Exception as e:
        print(f"[image] FAILED {src}: {e}")
        return None


# --------- video poster (ffmpeg) ----------


def have_cmd(cmd: str) -> bool:
    try:
        subprocess.run(
            [cmd, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return True
    except Exception:
        return False


def get_duration_seconds(path: Path) -> Optional[float]:
    """Use ffprobe to read duration; return None if unavailable."""
    try:
        res = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return float(res.stdout.strip())
    except Exception:
        pass
    return None


def get_rotation_degrees(path: Path) -> int:
    """
    Read rotation metadata (if any) using ffprobe.
    Returns 0 if none found. FFmpeg uses 'rotate' tag in degrees.
    """
    try:
        res = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream_tags=rotate",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return int(float(res.stdout.strip()))
    except Exception:
        pass
    return 0


def make_video_poster(
    src: Path,
    out_dir: Path,
    max_width: int,
    seek: Optional[float],
    quality: int = 82,  # kept for signature parity; mapped to q:v below
    force: bool = False,
) -> Optional[Path]:
    """
    Create <name>-poster.jpg by grabbing a frame with ffmpeg.
    - Picks midpoint if --seek not provided
    - Applies rotation if present in metadata
    - Limits width to max_width while preserving aspect
    - Skips when output newer than source unless force=True
    """
    if not have_cmd("ffmpeg"):
        sys.exit("ffmpeg not found. Install ffmpeg and ffprobe, then re-run.")
    out_dir.mkdir(parents=True, exist_ok=True)

    dst = out_dir / f"{src.stem}-poster.jpg"
    if not force and not _is_outdated(src, dst):
        return None

    # Timestamp selection
    t = seek
    if t is None:
        dur = get_duration_seconds(src)
        t = max(0.5, (dur / 2.0) if dur and dur > 0 else 2.0)

    # Rotation handling
    rot = get_rotation_degrees(src)
    vf_parts = []

    # Build scale first; ensure even height (-2)
    vf_parts.append(f"scale='min({max_width},iw)':'-2'")

    # If video has rotation metadata, bake it in (FFmpeg rotates counter-clockwise)
    # Common values: 90, 180, 270. Use transpose filters for 90/270; vflip/hflip for 180.
    if rot != 0:
        r = ((rot % 360) + 360) % 360
        if r == 90:
            vf_parts.append("transpose=1")  # clockwise
        elif r == 180:
            vf_parts.append("hflip,vflip")
        elif r == 270:
            vf_parts.append("transpose=2")  # counter-clockwise

    vf_chain = ",".join(vf_parts)

    # Map Pillow-like 1–100 quality to ffmpeg JPEG q:v (2–31, lower is better).
    # We'll target visually good output: q:v ~ 3–5
    q_v = 4

    # Fast seek: place -ss before -i (good enough for posters, much faster)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        str(t),
        "-i",
        str(src),
        "-frames:v",
        "1",
        "-vf",
        vf_chain,
        "-an",
        "-q:v",
        str(q_v),
        str(dst),
    ]

    try:
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        # Align times for incremental builds (optional)
        try:
            os.utime(dst, (src.stat().st_atime, src.stat().st_mtime))
        except Exception:
            pass
        return dst
    except subprocess.CalledProcessError as e:
        print(f"[video] FAILED {src}: ffmpeg error (code {e.returncode})")
        return None


# --------- walker ----------


def process_dir(
    root: Path,
    out: Path,
    img_size: Tuple[int, int],
    poster_width: int,
    seek: Optional[float],
    force: bool,
) -> None:
    count_img = count_vid = 0
    made_img = made_vid = 0

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()

        # choose output directory mirroring structure
        rel = p.parent.relative_to(root)
        out_dir = out / rel
        out_dir.mkdir(parents=True, exist_ok=True)

        if ext in IMAGE_EXTS:
            # skip if filename ends with "-poster" before extension
            if p.stem.endswith(("-poster", "-thumb")):
                continue

            count_img += 1
            res = make_image_thumb(p, out_dir, img_size, force=force)
            if res:
                made_img += 1
                print(f"[image] ✓ {p}  ->  {res}")
        elif ext in VIDEO_EXTS:
            count_vid += 1
            res = make_video_poster(p, out_dir, poster_width, seek, force=force)
            if res:
                made_vid += 1
                print(f"[video] ✓ {p}  ->  {res}")

    print("\nDone.")
    print(f"Images found: {count_img}  | thumbnails created: {made_img}")
    print(f"Videos found: {count_vid}  | posters created:   {made_vid}")


def main():
    ap = argparse.ArgumentParser(
        description="Create image thumbnails and video posters (skips if outputs exist)."
    )
    ap.add_argument("input", help="Input folder to scan (recursively).")
    ap.add_argument(
        "-o",
        "--out",
        default=None,
        help="Output base folder (default: write next to inputs, mirroring structure).",
    )
    ap.add_argument(
        "--thumb-size",
        default="800x800",
        help="Max thumbnail size WxH for images (default: 800x800).",
    )
    ap.add_argument(
        "--poster-width",
        type=int,
        default=800,
        help="Max width for video posters (default: 800).",
    )
    ap.add_argument(
        "--seek",
        type=float,
        default=None,
        help="Timestamp (in seconds) to grab poster frame. Default: midpoint.",
    )
    ap.add_argument("--force", action="store_true", help="Overwrite existing outputs.")
    args = ap.parse_args()

    root = Path(args.input).resolve()
    if not root.exists():
        sys.exit(f"Input path not found: {root}")

    # Parse thumb size
    try:
        w, h = args.thumb_size.lower().split("x")
        img_size = (int(w), int(h))
    except Exception:
        sys.exit("Invalid --thumb-size. Use format like 800x800")

    # Determine output
    out = Path(args.out).resolve() if args.out else root
    out.mkdir(parents=True, exist_ok=True)

    process_dir(root, out, img_size, args.poster_width, args.seek, args.force)


if __name__ == "__main__":
    main()
