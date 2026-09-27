"""Self-contained status vocabulary for the public Space demo.

Mirrors packages/ui_kit/src/status.py::backend_label so the Space has zero
repo dependencies (the Space repo only contains this folder's files).
Source of truth for label semantics remains the main repository.
"""


def backend_label(verification: dict) -> dict[str, str]:
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
