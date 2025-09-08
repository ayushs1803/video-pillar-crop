#!/usr/bin/env python3
"""
video_pillar_crop.py

Detect black vertical "pillar" bars (letterboxing or pillarboxing) in a video and compute crop attributes
(useful for metadata fields like iTunes/compressor crop values).

Requirements:
 - Python 3.8+
 - Pillow (PIL): pip install Pillow
 - ffmpeg must be installed and on PATH (https://ffmpeg.org/download.html)

How it works:
 - Samples N frames from the video (configurable; default 2 fps up to a max)
 - Scales each sampled frame to a manageable width for speed (default 800px wide)
 - Computes per-column mean brightness (grayscale)
 - Marks columns as "black" if their mean is <= threshold (default 16 / 0-255)
 - Keeps columns that are black across >= frame_pct of sampled frames (default 0.90)
 - Determines left and right pillar widths (pixels) and suggests a crop box
 - Outputs pixel and normalized crop values (left,top,width,height) and additional diagnostics

Example:
    python video_pillar_crop.py "movie.mp4" --sample-fps 2 --threshold 12 --frame-pct 0.95

Outputs JSON to stdout and writes a .crop.json next to the source video.

Notes for Windows users:
 - Install ffmpeg (add to PATH) and ensure `ffmpeg -version` runs in cmd or PowerShell.
 - Run the script from the same folder as your video or provide full paths.
"""

import argparse, json, sys, subprocess, tempfile, os, math, shutil
from pathlib import Path
from PIL import Image
import numpy as np

def run_ffmpeg_extract_frames(video_path, out_dir, sample_fps=2, scale_width=800):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-vf", f"fps={sample_fps},scale={scale_width}:-2",
        "-q:v", "2",
        str(out_dir / "frame_%06d.png")
    ]
    subprocess.check_call(cmd)
    frames = sorted(out_dir.glob("frame_*.png"))
    return frames

def column_blackness(img, threshold=16):
    arr = np.array(img, dtype=np.uint8)
    means = arr.mean(axis=0)
    return means <= threshold, means

def analyze_frames(frames, threshold=16, frame_pct=0.9):
    counts = None
    col_means_store = []
    n = 0
    for p in frames:
        img = Image.open(p).convert("L")
        bw, means = column_blackness(img, threshold=threshold)
        col_means_store.append(means.tolist())
        if counts is None:
            counts = bw.astype(int)
            width = img.width
            height = img.height
        else:
            if img.width != width:
                raise RuntimeError("Extracted frame widths vary; unexpected.")
            counts += bw.astype(int)
        n += 1
    required = math.ceil(frame_pct * n)
    black_cols = counts >= required
    return {
        "n_frames": n,
        "width": width,
        "height": height,
        "counts": counts.tolist(),
        "black_cols": black_cols.tolist(),
        "col_means": col_means_store
    }

def find_pillars(black_cols_bool):
    W = len(black_cols_bool)
    left = 0
    while left < W and black_cols_bool[left]:
        left += 1
    right = 0
    while right < W and black_cols_bool[W-1-right]:
        right += 1
    left = min(left, W//2)
    right = min(right, W//2)
    return left, right

def to_norm(left, right, W, H):
    x = left
    y = 0
    w = max(0, W - left - right)
    h = H
    return {
        "x": x, "y": y, "w": w, "h": h,
        "nx": round(x / W, 6),
        "ny": round(y / H, 6),
        "nw": round(w / W, 6),
        "nh": round(h / H, 6)
    }

def main():
    p = argparse.ArgumentParser(description="Detect black pillar bars in video and compute crop attributes.")
    p.add_argument("video", help="input video path")
    p.add_argument("--sample-fps", type=float, default=2.0, help="frames per second to sample (default 2.0)")
    p.add_argument("--scale-width", type=int, default=800, help="scale width for analysis speed (default 800px)")
    p.add_argument("--threshold", type=int, default=16, help="grayscale mean threshold (0-255) to consider a column black (default 16)")
    p.add_argument("--frame-pct", type=float, default=0.90, help="fraction of sampled frames a column must be black to count (default 0.90)")
    p.add_argument("--out-json", default=None, help="write output JSON file next to video")
    p.add_argument("--keep-frames", action='store_true', help="do not delete temporary extracted frames (for debugging)")
    args = p.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print("ERROR: input video not found:", video_path, file=sys.stderr)
        sys.exit(2)

    tmpd = Path(tempfile.mkdtemp(prefix="vpillar_"))
    try:
        frames = run_ffmpeg_extract_frames(video_path, tmpd, sample_fps=args.sample_fps, scale_width=args.scale_width)
        if len(frames) == 0:
            print("ERROR: no frames extracted (ffmpeg may have failed).", file=sys.stderr)
            sys.exit(3)
        analysis = analyze_frames(frames, threshold=args.threshold, frame_pct=args.frame_pct)
        left, right = find_pillars(analysis["black_cols"])
        crop = to_norm(left, right, analysis["width"], analysis["height"])

        out = {
            "video": str(video_path),
            "video_size_used_for_analysis": [analysis["width"], analysis["height"]],
            "n_sampled_frames": analysis["n_frames"],
            "threshold": args.threshold,
            "frame_pct": args.frame_pct,
            "left_pillar_px": left,
            "right_pillar_px": right,
            "pillar_percent_left": round(left / analysis["width"], 6),
            "pillar_percent_right": round(right / analysis["width"], 6),
            "crop": crop
        }
        s = json.dumps(out, indent=2)
        sys.stdout.write(s + "\n")
        if args.out_json:
            outp = Path(args.out_json)
        else:
            outp = video_path.with_suffix(video_path.suffix + ".crop.json")
        with open(outp, "w") as f:
            f.write(s)
        if not args.keep_frames:
            shutil.rmtree(tmpd)
        else:
            print("Temporary frames retained at:", tmpd, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print("ERROR: ffmpeg failed. Make sure ffmpeg is installed and on PATH.", file=sys.stderr)
        print(e, file=sys.stderr)
        shutil.rmtree(tmpd, ignore_errors=True)
        sys.exit(4)
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        shutil.rmtree(tmpd, ignore_errors=True)
        sys.exit(5)

if __name__ == "__main__":
    main()
