"""Deterministic timeline math: frame-exact clip ops for the VSE-authoritative timeline.

All durations are integer frames at the project FPS. Ops are pure functions over clip
dicts so they are unit-testable without Blender; `assemble_timeline.py` consumes the
resulting ordered clip list.
"""

from __future__ import annotations

from typing import Any


def seconds_to_frames(seconds: float, fps: int) -> int:
    """Converts seconds to integer frames (round half up)."""
    if fps <= 0:
        raise ValueError(f"fps must be > 0, got {fps}")
    if seconds < 0:
        raise ValueError(f"seconds must be >= 0, got {seconds}")
    return int(seconds * fps + 0.5)


def split_clip(clip: dict[str, Any], at_frame: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Splits a clip into two at an interior frame boundary."""
    start, end = int(clip["start_frame"]), int(clip["end_frame"])
    if not start < at_frame < end:
        raise ValueError(f"split frame {at_frame} outside ({start}, {end})")
    left = dict(clip)
    right = dict(clip)
    left["end_frame"] = at_frame
    right["start_frame"] = at_frame
    right["clip_id"] = f"{clip['clip_id']}_b"
    return left, right


def trim_clip(clip: dict[str, Any], new_start: int | None = None, new_end: int | None = None) -> dict[str, Any]:
    """Trims a clip to the given frame bounds (must stay non-empty)."""
    out = dict(clip)
    if new_start is not None:
        out["start_frame"] = new_start
    if new_end is not None:
        out["end_frame"] = new_end
    if out["end_frame"] <= out["start_frame"]:
        raise ValueError("trim produced empty clip")
    return out


def move_clip(clip: dict[str, Any], delta_frames: int) -> dict[str, Any]:
    """Shifts a clip in time; start must stay >= 1."""
    out = dict(clip)
    out["start_frame"] = int(clip["start_frame"]) + delta_frames
    out["end_frame"] = int(clip["end_frame"]) + delta_frames
    if out["start_frame"] < 1:
        raise ValueError("move produced start_frame < 1")
    return out


def set_speed(clip: dict[str, Any], speed: float) -> dict[str, Any]:
    """Retimes a clip; source duration stays fixed, playback length scales by 1/speed."""
    if speed <= 0:
        raise ValueError(f"speed must be > 0, got {speed}")
    out = dict(clip)
    source_len = int(clip["end_frame"]) - int(clip["start_frame"])
    out["end_frame"] = int(clip["start_frame"]) + max(1, int(source_len / speed + 0.5))
    out["speed"] = speed
    return out


def add_fade(clip: dict[str, Any], fade_in_frames: int = 0, fade_out_frames: int = 0) -> dict[str, Any]:
    """Attaches fade handles; fades must fit inside the clip."""
    out = dict(clip)
    length = int(clip["end_frame"]) - int(clip["start_frame"])
    if fade_in_frames < 0 or fade_out_frames < 0 or fade_in_frames + fade_out_frames > length:
        raise ValueError("fade handles exceed clip length")
    out["fade_in_frames"] = fade_in_frames
    out["fade_out_frames"] = fade_out_frames
    return out


def validate_timeline(clips: list[dict[str, Any]], fps: int) -> tuple[bool, list[str]]:
    """Checks fps consistency, non-empty clips, and reports gaps/overlaps (gaps warn, not fail)."""
    errors: list[str] = []
    if fps <= 0:
        return False, ["fps must be > 0"]
    ordered = sorted(clips, key=lambda c: int(c["start_frame"]))
    for clip in ordered:
        if int(clip["end_frame"]) <= int(clip["start_frame"]):
            errors.append(f"clip {clip['clip_id']} is empty")
        if int(clip.get("fps", fps)) != fps:
            errors.append(f"clip {clip['clip_id']} fps {clip.get('fps')} != timeline {fps}")
    for prev, nxt in zip(ordered, ordered[1:]):
        if int(nxt["start_frame"]) < int(prev["end_frame"]):
            errors.append(f"overlap: {prev['clip_id']} into {nxt['clip_id']}")
    return (len(errors) == 0, errors)


def timeline_duration_frames(clips: list[dict[str, Any]]) -> int:
    """Returns the last occupied frame (0 when empty)."""
    if not clips:
        return 0
    return max(int(c["end_frame"]) for c in clips)
