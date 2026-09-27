"""Two-part visual verification: ffmpeg frame sampling + PIL contact sheets + thresholds.

AI outputs are compared with structural thresholds (brightness/histogram), never with
brittle pixel-exact equality (§66). Known-bad fixtures: fully black, fully white,
or undecodable frames are rejected.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


def sample_frames(video_path: Path | str, out_dir: Path | str, count: int = 3) -> list[Path]:
    """Extracts `count` evenly spaced frames via ffmpeg. Raises on failure."""
    src = Path(video_path)
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    if not src.is_file():
        raise FileNotFoundError(f"video missing: {src}")
    if count < 1:
        raise ValueError("count must be >= 1")
    pattern = str(dest / "sample_%02d.png")
    # fps filter tuned so short clips still yield `count` frames; pad by duration probe
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
        capture_output=True,
        text=True,
        check=True,
    )
    duration = max(0.5, float(probe.stdout.strip() or 0.5))
    fps = count / duration
    proc = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", f"fps={fps}:round=up", "-frames:v", str(count), pattern],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"frame sampling failed: {proc.stderr[-500:]}")
    frames = sorted(dest.glob("sample_*.png"))
    if not frames:
        raise RuntimeError("frame sampling produced no images")
    return frames


def frame_brightness(image_path: Path | str) -> float:
    """Returns mean grayscale brightness 0..255."""
    with Image.open(image_path).convert("L") as img:
        return ImageStat.Stat(img).mean[0]


def detect_known_bad(image_path: Path | str) -> list[str]:
    """Flags fully black / fully white / tiny frames."""
    problems: list[str] = []
    try:
        with Image.open(image_path) as img:
            if img.size[0] < 16 or img.size[1] < 16:
                problems.append("frame_too_small")
                return problems
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            mean = stat.mean[0]
            extrema = gray.getextrema()
    except Exception as e:
        return [f"undecodable: {e}"]
    if mean < 2.0:
        problems.append("fully_black")
    if mean > 253.0:
        problems.append("fully_white")
    if extrema == (0, 0) or extrema == (255, 255):
        problems.append("zero_variance")
    return problems


def contact_sheet(images: list[Path | str], out_path: Path | str, columns: int = 3) -> Path:
    """Tiles images into a labeled contact sheet."""
    if not images:
        raise ValueError("no images for contact sheet")
    tiles = [Image.open(p).convert("RGB") for p in images]
    tw, th = tiles[0].size
    tiles = [t.resize((tw, th)) if t.size != (tw, th) else t for t in tiles]
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tw, rows * th), (20, 20, 20))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % columns) * tw, (i // columns) * th))
    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest)
    return dest


def histogram_distance(a: Path | str, b: Path | str) -> float:
    """Mean-absolute histogram distance 0..1 across RGB channels (size-normalized)."""
    with Image.open(a).convert("RGB") as ia, Image.open(b).convert("RGB") as ib:
        ha, hb = ia.histogram(), ib.histogram()
    total = sum(ha) or 1
    return sum(abs(x - y) for x, y in zip(ha, hb)) / (2 * total)


def check_result(images: list[Path | str]) -> dict[str, Any]:
    """Runs known-bad detection over sampled frames."""
    flagged: dict[str, list[str]] = {}
    for img in images:
        problems = detect_known_bad(img)
        if problems:
            flagged[str(img)] = problems
    return {"frames": len(images), "flagged": flagged, "passed": not flagged}
