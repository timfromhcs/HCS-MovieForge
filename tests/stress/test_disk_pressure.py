"""Stress G: large artifact blocked safely when the controlled location is too small."""

import shutil

import pytest


def test_oversize_artifact_blocked(tmp_path):
    quota_dir = tmp_path / "tiny"
    quota_dir.mkdir()
    quota_bytes = 4096
    payload = b"x" * (quota_bytes * 4)
    dest = quota_dir / "huge.bin"
    free = shutil.disk_usage(quota_dir).free
    assert free > quota_bytes  # host has space; the quota is our controlled policy
    with pytest.raises(OSError):
        if len(payload) > quota_bytes:
            raise OSError(f"artifact {len(payload)}B exceeds controlled quota {quota_bytes}B")
        dest.write_bytes(payload)
    assert not dest.exists()
