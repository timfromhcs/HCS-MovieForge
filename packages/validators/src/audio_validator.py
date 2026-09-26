"""Audio artifact validation using ffprobe to check format, channels, and sample rate."""

import json
import subprocess
from pathlib import Path
from typing import Any


class AudioValidationResult:
    def __init__(
        self,
        is_valid: bool,
        errors: list[str],
        duration_sec: float = 0.0,
        sample_rate: int = 0,
        channels: int = 0,
        codec_name: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.duration_sec = duration_sec
        self.sample_rate = sample_rate
        self.channels = channels
        self.codec_name = codec_name
        self.metadata = metadata or {}


def validate_audio(
    audio_path: Path | str,
    min_duration_sec: float = 0.1,
    expected_sample_rate: int | None = None,
    min_size_bytes: int = 256,
) -> AudioValidationResult:
    """Validates an audio file using ffprobe."""
    path = Path(audio_path)
    errors = []

    if not path.is_file():
        return AudioValidationResult(False, [f"Audio file does not exist: {path}"])

    size = path.stat().st_size
    if size < min_size_bytes:
        return AudioValidationResult(
            False,
            [f"Audio file size too small ({size} bytes < {min_size_bytes} bytes)"]
        )

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        streams = data.get("streams", [])
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if not audio_stream:
            return AudioValidationResult(False, ["No audio stream found in media file."])

        codec = audio_stream.get("codec_name", "unknown")
        sample_rate = int(audio_stream.get("sample_rate", 0))
        channels = int(audio_stream.get("channels", 0))

        fmt = data.get("format", {})
        duration = float(fmt.get("duration", 0.0))

        if duration < min_duration_sec:
            errors.append(f"Audio duration {duration:.2f}s is less than min {min_duration_sec:.2f}s")

        if expected_sample_rate is not None and sample_rate != expected_sample_rate:
            errors.append(f"Sample rate {sample_rate} != expected {expected_sample_rate}")

        if channels < 1:
            errors.append("Invalid channel count (< 1)")

        return AudioValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            duration_sec=duration,
            sample_rate=sample_rate,
            channels=channels,
            codec_name=codec,
            metadata=fmt,
        )
    except Exception as e:
        return AudioValidationResult(False, [f"ffprobe validation failed: {e}"])
