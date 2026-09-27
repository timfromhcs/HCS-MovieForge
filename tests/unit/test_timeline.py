"""Unit tests for deterministic timeline math (frame-exact, no Blender)."""

import pytest

from packages.project_format.src.timeline import (
    add_fade,
    move_clip,
    seconds_to_frames,
    set_speed,
    split_clip,
    timeline_duration_frames,
    trim_clip,
    validate_timeline,
)


def _clip(cid="c1", start=1, end=73, fps=24):
    return {"clip_id": cid, "start_frame": start, "end_frame": end, "fps": fps}


def test_seconds_to_frames():
    assert seconds_to_frames(3.0, 24) == 72
    assert seconds_to_frames(0.0, 24) == 0
    with pytest.raises(ValueError):
        seconds_to_frames(1.0, 0)
    with pytest.raises(ValueError):
        seconds_to_frames(-1.0, 24)


def test_split_trim_move_speed_fade():
    left, right = split_clip(_clip(), 25)
    assert (left["start_frame"], left["end_frame"]) == (1, 25)
    assert (right["start_frame"], right["end_frame"]) == (25, 73)
    assert right["clip_id"] == "c1_b"
    with pytest.raises(ValueError):
        split_clip(_clip(), 1)
    trimmed = trim_clip(_clip(), new_start=10, new_end=50)
    assert (trimmed["start_frame"], trimmed["end_frame"]) == (10, 50)
    with pytest.raises(ValueError):
        trim_clip(_clip(), new_start=10, new_end=10)
    moved = move_clip(_clip(), 24)
    assert (moved["start_frame"], moved["end_frame"]) == (25, 97)
    with pytest.raises(ValueError):
        move_clip(_clip(), -5)
    fast = set_speed(_clip(), 2.0)
    assert fast["end_frame"] - fast["start_frame"] == 36
    with pytest.raises(ValueError):
        set_speed(_clip(), 0)
    faded = add_fade(_clip(), fade_in_frames=12, fade_out_frames=12)
    assert faded["fade_in_frames"] == 12
    with pytest.raises(ValueError):
        add_fade(_clip(), fade_in_frames=40, fade_out_frames=40)


def test_validate_timeline():
    ok, _ = validate_timeline([_clip("a", 1, 73), _clip("b", 73, 145)], 24)
    assert ok
    ok, errors = validate_timeline([_clip("a", 1, 100), _clip("b", 73, 145)], 24)
    assert not ok and any("overlap" in e for e in errors)
    ok, errors = validate_timeline([_clip("a", 1, 73, fps=30)], 24)
    assert not ok and errors
    assert timeline_duration_frames([_clip("a", 1, 73), _clip("b", 73, 145)]) == 145
    assert timeline_duration_frames([]) == 0
