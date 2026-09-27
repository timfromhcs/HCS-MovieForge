"""Video artifact validation using ffprobe to check resolution, FPS, and codecs."""

import json
import subprocess
from pathlib import Path
from typing import Any


class VideoValidationResult:
    def __init__(
        self,
        is_valid: bool,
        errors: list[str],
        width: int = 0,
        height: int = 0,
        fps: float = 0.0,
        duration_sec: float = 0.0,
        video_codec: str = "",
        has_audio: bool = False,
        audio_codec: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.width = width
        self.height = height
        self.fps = fps
        self.duration_sec = duration_sec
        self.video_codec = video_codec
        self.has_audio = has_audio
        self.audio_codec = audio_codec
        self.metadata = metadata or {}


def validate_video(
    video_path: Path | str,
    expected_width: int | None = 1920,
    expected_height: int | None = 1080,
    expected_fps: float | None = None,
    require_audio: bool = False,
    min_size_bytes: int = 1024,
) -> VideoValidationResult:
    """Validates video resolution, frame rate, streams, and duration via ffprobe."""
    path = Path(video_path)
    errors = []

    if not path.is_file():
        return VideoValidationResult(False, [f"Video file does not exist: {path}"])

    size = path.stat().st_size
    if size < min_size_bytes:
        return VideoValidationResult(False, [f"Video file size too small ({size} bytes < {min_size_bytes} bytes)"])

    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        streams = data.get("streams", [])
        v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        if not v_stream:
            return VideoValidationResult(False, ["No video stream found in container."])

        w = int(v_stream.get("width", 0))
        h = int(v_stream.get("height", 0))
        v_codec = v_stream.get("codec_name", "unknown")

        # Parse FPS fraction e.g. "24/1" or "30000/1001"
        fps_str = v_stream.get("r_frame_rate", "0/1")
        try:
            num, den = map(float, fps_str.split("/"))
            fps = num / den if den != 0 else 0.0
        except Exception:
            fps = 0.0

        fmt = data.get("format", {})
        duration = float(fmt.get("duration", 0.0))

        if expected_width is not None and w != expected_width:
            errors.append(f"Width {w} != expected {expected_width}")
        if expected_height is not None and h != expected_height:
            errors.append(f"Height {h} != expected {expected_height}")
        if expected_fps is not None and abs(fps - expected_fps) > 0.1:
            errors.append(f"FPS {fps:.2f} != expected {expected_fps:.2f}")

        a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
        has_audio = a_stream is not None
        a_codec = a_stream.get("codec_name", "") if a_stream else ""

        if require_audio and not has_audio:
            errors.append("Video file requires audio track, but none was found.")

        return VideoValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            width=w,
            height=h,
            fps=fps,
            duration_sec=duration,
            video_codec=v_codec,
            has_audio=has_audio,
            audio_codec=a_codec,
            metadata=fmt,
        )
    except Exception as e:
        return VideoValidationResult(False, [f"ffprobe video validation failed: {e}"])
