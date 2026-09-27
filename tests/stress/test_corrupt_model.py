"""Stress F: corrupt a staged model file; hash check must fail so it is never promoted."""

from engine.model_manager.manager import ModelManager
from packages.validators.src.hash_validator import calculate_sha256


def test_staged_corruption_detected(tmp_path):
    mgr = ModelManager(models_dir=tmp_path / "models", staging_dir=tmp_path / "staging")
    staged = tmp_path / "staging" / "weights.bin"
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_bytes(b"model-bytes-v1")
    pinned = calculate_sha256(staged)
    staged.write_bytes(b"model-bytes-CORRUPTED")
    assert calculate_sha256(staged) != pinned
    assert mgr.get_lock() == {"version": 1, "models": {}}
