"""Stress E: corrupt an output file before validation; validator must reject, no false success."""

from PIL import Image

from packages.validators.src.image_validator import validate_image


def test_corrupt_png_rejected(tmp_path):
    good = tmp_path / "good.png"
    Image.new("RGB", (64, 64), (10, 200, 90)).save(good)
    assert validate_image(str(good)).is_valid
    evil = tmp_path / "evil.png"
    evil.write_bytes(good.read_bytes()[:100] + b"\x00\xffCORRUPT" * 64)
    assert not validate_image(str(evil)).is_valid
