"""Verification-state status vocabulary (§128): labels come from evidence, not hard-coded text.

Each label carries a non-color text marker for accessibility (§138): status is never
color-only. Tones are hints; `text` is authoritative.
"""

from __future__ import annotations

LABELS = ("READY", "VERIFIED", "EXPERIMENTAL", "UNAVAILABLE", "DEGRADED", "BLOCKED")


def backend_label(verification: dict) -> dict[str, str]:
    """Maps a verification record to a UI status label.

    verification keys: local_built, local_runtime_verified, release_certified (bools),
    experimental (bool). Missing keys count as False (UNKNOWN -> not ready).
    """
    built = bool(verification.get("local_built"))
    runtime = bool(verification.get("local_runtime_verified"))
    certified = bool(verification.get("release_certified"))
    if certified and runtime:
        return {"label": "VERIFIED", "tone": "ok", "text": "[VERIFIED] certified on this hardware"}
    if runtime:
        return {"label": "READY", "tone": "ok", "text": "[READY] verified locally, release pending"}
    if verification.get("experimental"):
        return {"label": "EXPERIMENTAL", "tone": "warn", "text": "[EXPERIMENTAL] unverified path"}
    if built:
        return {"label": "DEGRADED", "tone": "warn", "text": "[DEGRADED] built but not runtime-verified"}
    return {"label": "UNAVAILABLE", "tone": "muted", "text": "[UNAVAILABLE] no verified backend"}


def blocked_label(reason: str) -> dict[str, str]:
    """Explicit failure-path label with reason (never a bare error)."""
    return {"label": "BLOCKED", "tone": "fail", "text": f"[BLOCKED] {reason}"}
