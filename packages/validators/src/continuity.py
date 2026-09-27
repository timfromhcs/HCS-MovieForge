"""Film continuity checks (§90): wardrobe/hair/time-of-day/location consistency per shot.

Only declared constraints are checked; no frame-by-frame comparison. Shots declare
`continuity_constraints` plus optional `inherits_from_shot`; violations reference the
declaring shot so artists can fix the editable project state.
"""

from __future__ import annotations

from typing import Any

TRACKED_KEYS = (
    "wardrobe",
    "hair",
    "time_of_day",
    "lighting",
    "weather",
    "location_id",
)


def check_continuity(shots: list[dict[str, Any]]) -> dict[str, Any]:
    """Compares each shot's declared constraints against its inherited shot."""
    by_id = {s["shot_id"]: s for s in shots if "shot_id" in s}
    violations: list[dict[str, Any]] = []
    checked = 0
    for shot in shots:
        parent_id = shot.get("inherits_from_shot")
        if not parent_id or parent_id not in by_id:
            continue
        parent = by_id[parent_id]
        constraints: dict[str, Any] = shot.get("continuity_constraints", {})
        for key in TRACKED_KEYS:
            if key in constraints:
                checked += 1
                expected = constraints[key]
                actual = shot.get(key, parent.get(key))
                if actual != expected:
                    violations.append(
                        {
                            "shot_id": shot["shot_id"],
                            "inherits_from": parent_id,
                            "key": key,
                            "expected": expected,
                            "actual": actual,
                        }
                    )
    return {"checked": checked, "violations": violations, "passed": not violations}
