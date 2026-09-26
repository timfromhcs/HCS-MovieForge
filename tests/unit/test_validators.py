"""Unit tests for hashing, image validation, and mesh structural validation."""

import io
from pathlib import Path
import pytest
from PIL import Image
from packages.validators.src.hash_validator import calculate_sha256, verify_sha256
from packages.validators.src.image_validator import validate_image
from packages.validators.src.mesh_validator import validate_glb


def test_hash_validator(tmp_path: Path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("HCS MovieForge Deterministic Test String", encoding="utf-8")

    digest = calculate_sha256(test_file)
    assert len(digest) == 64
    assert verify_sha256(test_file, digest) is True
    assert verify_sha256(test_file, "wrong_hash") is False


def test_image_validator(tmp_path: Path):
    img_file = tmp_path / "frame.png"
    # Create valid RGB image
    img = Image.new("RGB", (1920, 1080), color=(10, 20, 30))
    img.save(img_file, format="PNG")

    res = validate_image(img_file, expected_width=1920, expected_height=1080)
    assert res.is_valid is True
    assert res.width == 1920
    assert res.height == 1080
    assert res.format_name == "PNG"

    # Dimension mismatch check
    res_mismatch = validate_image(img_file, expected_width=1280, expected_height=720)
    assert res_mismatch.is_valid is False
    assert len(res_mismatch.errors) == 2


def test_mesh_validator_nonexistent():
    res = validate_glb("nonexistent.glb")
    assert res.is_valid is False
    assert "does not exist" in res.errors[0]
