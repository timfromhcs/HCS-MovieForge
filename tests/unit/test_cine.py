"""Unit tests for deterministic cine contracts (no Blender needed)."""

from integrations.blender.cine import (
    ACTION_LIBRARY,
    CAMERA_PRESETS,
    FX_SYSTEMS,
    LIGHTING_PRESETS,
    POSE_MATRIX,
    parse_motion_plan,
    validate_camera_preset,
    validate_lighting_preset,
)


def test_preset_catalogs_complete():
    assert len(CAMERA_PRESETS) == 15
    assert len(LIGHTING_PRESETS) == 11
    assert len(FX_SYSTEMS) == 12
    assert len(ACTION_LIBRARY) == 18
    assert len(POSE_MATRIX) == 14


def test_camera_validation_ranges():
    ok, _ = validate_camera_preset("orbit", {"lens_mm": 35, "speed_ms": 0.5})
    assert ok
    ok, errors = validate_camera_preset("orbit", {"lens_mm": 500, "speed_ms": 0.5})
    assert not ok and errors
    ok, errors = validate_camera_preset("nope", {})
    assert not ok and errors


def test_lighting_validation_ranges():
    ok, _ = validate_lighting_preset("night", {"key_energy": 0.6})
    assert ok
    ok, errors = validate_lighting_preset("night", {"key_energy": 99})
    assert not ok and errors


def test_motion_plan_example_from_spec():
    steps = parse_motion_plan("Anna walks four meters, slows down, stops, and looks left.")
    assert steps[0] == {"action": "walk", "distance_m": 4.0}
    assert {"action": "decelerate"} in steps
    assert {"action": "stop"} in steps
    assert {"action": "head_turn", "direction": "left"} in steps
