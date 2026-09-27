"""Unit tests for the verification-driven status vocabulary."""

from packages.ui_kit.src.status import backend_label, blocked_label


def test_verified_needs_runtime_and_certified():
    assert backend_label({"local_runtime_verified": True, "release_certified": True})["label"] == "VERIFIED"
    assert backend_label({"local_runtime_verified": True})["label"] == "READY"
    assert backend_label({"experimental": True})["label"] == "EXPERIMENTAL"
    assert backend_label({"local_built": True})["label"] == "DEGRADED"
    assert backend_label({})["label"] == "UNAVAILABLE"


def test_blocked_carries_reason():
    lbl = blocked_label("trellis Vulkan uncertified")
    assert lbl["label"] == "BLOCKED" and "trellis" in lbl["text"]
    assert lbl["text"].startswith("[BLOCKED]")
