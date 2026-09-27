"""Deterministic cinematography contracts: camera/lighting/FX presets, action library, motion plans.

All presets are plain validated parameter dicts. A Blender-side applier script consumes
them; nothing here claims rendering by itself (verified by golden tests + visual review).
"""

from __future__ import annotations

import re
from typing import Any

CAMERA_PRESETS: dict[str, dict[str, Any]] = {
    "static": {"lens_mm": 50, "movement": "none", "dof": False},
    "push_in": {"lens_mm": 50, "movement": "dolly_forward", "speed_ms": 0.4, "dof": False},
    "pull_out": {"lens_mm": 35, "movement": "dolly_backward", "speed_ms": 0.4, "dof": False},
    "dolly": {"lens_mm": 50, "movement": "dolly_forward", "speed_ms": 0.6, "dof": False},
    "truck": {"lens_mm": 50, "movement": "lateral", "speed_ms": 0.6, "dof": False},
    "orbit": {"lens_mm": 35, "movement": "orbit", "speed_ms": 0.5, "dof": False},
    "arc": {"lens_mm": 35, "movement": "arc", "speed_ms": 0.5, "dof": False},
    "crane": {"lens_mm": 28, "movement": "vertical", "speed_ms": 0.5, "dof": False},
    "pan": {"lens_mm": 50, "movement": "pan", "speed_ms": 0.5, "dof": False},
    "tilt": {"lens_mm": 50, "movement": "tilt", "speed_ms": 0.5, "dof": False},
    "rack_focus": {"lens_mm": 85, "movement": "none", "dof": True},
    "tracking": {"lens_mm": 35, "movement": "tracking", "speed_ms": 0.8, "dof": False},
    "pov": {"lens_mm": 28, "movement": "handheld_light", "dof": False},
    "handheld": {"lens_mm": 35, "movement": "handheld", "dof": False},
    "over_shoulder": {"lens_mm": 85, "movement": "none", "dof": True},
}

LIGHTING_PRESETS: dict[str, dict[str, Any]] = {
    "day": {"key_energy": 5.0, "key_color": (1.0, 0.98, 0.95), "world_energy": 1.0, "fog": 0.0},
    "night": {"key_energy": 0.6, "key_color": (0.5, 0.6, 1.0), "world_energy": 0.05, "fog": 0.0},
    "sunset": {"key_energy": 3.0, "key_color": (1.0, 0.55, 0.3), "world_energy": 0.4, "fog": 0.0},
    "moon": {"key_energy": 0.4, "key_color": (0.6, 0.7, 1.0), "world_energy": 0.03, "fog": 0.0},
    "neon": {"key_energy": 1.2, "key_color": (0.4, 0.8, 1.0), "world_energy": 0.1, "fog": 0.0},
    "interior": {"key_energy": 2.5, "key_color": (1.0, 0.95, 0.85), "world_energy": 0.3, "fog": 0.0},
    "rain": {"key_energy": 1.5, "key_color": (0.7, 0.8, 1.0), "world_energy": 0.2, "fog": 0.3},
    "warm": {"key_energy": 3.5, "key_color": (1.0, 0.75, 0.5), "world_energy": 0.6, "fog": 0.0},
    "cold": {"key_energy": 2.5, "key_color": (0.6, 0.75, 1.0), "world_energy": 0.5, "fog": 0.0},
    "dramatic": {"key_energy": 4.0, "key_color": (1.0, 0.9, 0.8), "world_energy": 0.05, "fog": 0.0},
    "sci-fi": {"key_energy": 1.8, "key_color": (0.5, 0.9, 1.0), "world_energy": 0.15, "fog": 0.1},
}

FX_SYSTEMS: dict[str, dict[str, Any]] = {
    "fog": {"type": "volume_scatter", "density": 0.05},
    "rain": {"type": "particles", "count": 5000, "physics": "newton"},
    "snow": {"type": "particles", "count": 3000, "physics": "newton"},
    "dust": {"type": "particles", "count": 1000, "physics": "boids_lite"},
    "smoke": {"type": "smoke_domain", "resolution": 32},
    "fire": {"type": "fire_domain", "resolution": 32},
    "sparks": {"type": "particles", "count": 2000, "physics": "newton"},
    "debris": {"type": "particles", "count": 500, "physics": "rigid_body_lite"},
    "lightning": {"type": "emissive_planes", "flashes": 3},
    "hologram": {"type": "emission_shader", "color": (0.3, 0.9, 1.0)},
    "energy": {"type": "emission_shader", "color": (0.5, 0.3, 1.0)},
    "wind": {"type": "force_field", "strength": 5.0},
}

ACTION_LIBRARY: dict[str, dict[str, Any]] = {
    "idle": {"duration_sec": 2.0, "loopable": True, "root_motion": False},
    "walk": {"duration_sec": 1.2, "loopable": True, "root_motion": True},
    "run": {"duration_sec": 0.8, "loopable": True, "root_motion": True},
    "sprint": {"duration_sec": 0.7, "loopable": True, "root_motion": True},
    "sit": {"duration_sec": 1.5, "loopable": False, "root_motion": False},
    "stand": {"duration_sec": 1.0, "loopable": False, "root_motion": False},
    "turn": {"duration_sec": 1.0, "loopable": False, "root_motion": False},
    "look": {"duration_sec": 0.8, "loopable": False, "root_motion": False},
    "wave": {"duration_sec": 1.2, "loopable": False, "root_motion": False},
    "point": {"duration_sec": 1.0, "loopable": False, "root_motion": False},
    "pick_up": {"duration_sec": 1.5, "loopable": False, "root_motion": False},
    "drop": {"duration_sec": 0.8, "loopable": False, "root_motion": False},
    "reach": {"duration_sec": 1.0, "loopable": False, "root_motion": False},
    "push": {"duration_sec": 1.5, "loopable": True, "root_motion": True},
    "pull": {"duration_sec": 1.5, "loopable": True, "root_motion": True},
    "jump": {"duration_sec": 0.9, "loopable": False, "root_motion": True},
    "fall": {"duration_sec": 1.0, "loopable": False, "root_motion": True},
    "fight": {"duration_sec": 2.0, "loopable": True, "root_motion": False},
}

POSE_MATRIX: list[str] = [
    "neutral",
    "t_pose",
    "a_pose",
    "arms_up",
    "arms_forward",
    "squat",
    "kneel",
    "walk_pose",
    "run_pose",
    "left_bend",
    "right_bend",
    "head_turn",
    "look_up",
    "look_down",
]


def validate_camera_preset(name: str, params: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validates camera parameters against physical ranges. Returns (ok, errors)."""
    errors: list[str] = []
    if name not in CAMERA_PRESETS:
        return False, [f"unknown camera preset: {name}"]
    lens = params.get("lens_mm", CAMERA_PRESETS[name]["lens_mm"])
    if not 12 <= float(lens) <= 300:
        errors.append(f"lens_mm {lens} out of range 12..300")
    speed = params.get("speed_ms", 0.5)
    if not 0 <= float(speed) <= 5:
        errors.append(f"speed_ms {speed} out of range 0..5")
    return (len(errors) == 0, errors)


def validate_lighting_preset(name: str, params: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validates lighting parameters. Returns (ok, errors)."""
    errors: list[str] = []
    if name not in LIGHTING_PRESETS:
        return False, [f"unknown lighting preset: {name}"]
    energy = params.get("key_energy", LIGHTING_PRESETS[name]["key_energy"])
    if not 0 <= float(energy) <= 20:
        errors.append(f"key_energy {energy} out of range 0..20")
    return (len(errors) == 0, errors)


def parse_motion_plan(text: str) -> list[dict[str, Any]]:
    """Translates a plain-text direction into structured motion steps (deterministic).

    Example: "Anna walks four meters, slows down, stops, and looks left."
    """
    lowered = text.lower()
    steps: list[dict[str, Any]] = []
    number_words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
    distance = 2.0
    m = re.search(r"(\d+(?:\.\d+)?|one|two|three|four|five|six)\s*meters?", lowered)
    if m:
        token = m.group(1)
        distance = float(number_words.get(token, token))
    if "walk" in lowered:
        steps.append({"action": "walk", "distance_m": distance})
    if "run" in lowered:
        steps.append({"action": "run", "distance_m": distance})
    if "slow" in lowered or "decelerate" in lowered:
        steps.append({"action": "decelerate"})
    if "stop" in lowered:
        steps.append({"action": "stop"})
    if "look" in lowered:
        if "left" in lowered:
            steps.append({"action": "head_turn", "direction": "left"})
        elif "right" in lowered:
            steps.append({"action": "head_turn", "direction": "right"})
        elif "up" in lowered:
            steps.append({"action": "head_turn", "direction": "up"})
        elif "down" in lowered:
            steps.append({"action": "head_turn", "direction": "down"})
    if "wave" in lowered:
        steps.append({"action": "wave"})
    if "sit" in lowered:
        steps.append({"action": "sit"})
    if "jump" in lowered:
        steps.append({"action": "jump"})
    return steps
