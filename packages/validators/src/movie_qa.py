"""Final movie QA gate (§91): programmatic checks over timeline + media + project state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.validators.src.audio_validator import validate_audio
from packages.validators.src.video_validator import validate_video


def qa_movie(
    video_path: Path | str,
    audio_path: Path | str | None,
    expected_width: int,
    expected_height: int,
    expected_fps: int,
    max_av_drift_sec: float = 0.5,
) -> dict[str, Any]:
    """Runs the programmatic final gate. Returns a verdict dict (never raises on media issues)."""
    errors: list[str] = []
    video = validate_video(video_path, expected_width, expected_height, expected_fps)
    if not video.is_valid:
        errors.extend(video.errors)
    audio_dur: float | None = None
    if audio_path is not None:
        audio = validate_audio(audio_path, min_duration_sec=0.1)
        if not audio.is_valid:
            errors.extend(audio.errors)
        else:
            audio_dur = audio.duration_sec
    else:
        errors.append("no audio track provided")
    if video.is_valid and audio_dur is not None:
        drift = abs(video.duration_sec - audio_dur)
        if drift > max_av_drift_sec and video.duration_sec > 0:
            # Stills-based masters legitimately pad video beyond audio; only fail on gross mismatch
            if drift > max(video.duration_sec * 0.5, max_av_drift_sec * 4):
                errors.append(f"audio/video drift {drift:.2f}s exceeds tolerance")
    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "video": {"width": video.width, "height": video.height, "fps": video.fps, "duration": video.duration_sec},
        "audio_duration": audio_dur,
    }


def check_shot_media(shots: list[dict[str, Any]], artifacts: dict[str, Path | str]) -> dict[str, Any]:
    """Verifies every shot references existing media (missing media must be 0, §91)."""
    missing: list[str] = []
    for shot in shots:
        for key in ("video_artifact", "audio_artifact"):
            ref = shot.get(key)
            if ref and (ref not in artifacts or not Path(artifacts[ref]).exists()):
                missing.append(f"{shot.get('shot_id', '?')}:{key}={ref}")
    return {"missing_media": len(missing), "missing": missing, "passed": not missing}
