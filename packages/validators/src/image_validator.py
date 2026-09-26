"""Image artifact validation using Pillow and structural checks."""

from pathlib import Path
from typing import Any
from PIL import Image


class ImageValidationResult:
    def __init__(
        self,
        is_valid: bool,
        errors: list[str],
        width: int = 0,
        height: int = 0,
        format_name: str = "",
        mode: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.width = width
        self.height = height
        self.format_name = format_name
        self.mode = mode
        self.metadata = metadata or {}


def validate_image(
    image_path: Path | str,
    expected_width: int | None = None,
    expected_height: int | None = None,
    min_size_bytes: int = 128,
) -> ImageValidationResult:
    """Validates an image file for integrity, dimensions, and readability."""
    path = Path(image_path)
    errors = []

    if not path.is_file():
        return ImageValidationResult(False, [f"Image file does not exist: {path}"])

    size = path.stat().st_size
    if size < min_size_bytes:
        return ImageValidationResult(
            False,
            [f"Image file size too small ({size} bytes < minimum {min_size_bytes} bytes)"]
        )

    try:
        with Image.open(path) as img:
            img.verify()  # Verifies file integrity without decoding full raster

        # Reopen to inspect dimensions and actual decode
        with Image.open(path) as img:
            w, h = img.size
            fmt = img.format or "UNKNOWN"
            mode = img.mode

            if expected_width is not None and w != expected_width:
                errors.append(f"Image width {w} != expected {expected_width}")
            if expected_height is not None and h != expected_height:
                errors.append(f"Image height {h} != expected {expected_height}")

            # Ensure we can read the raw raster data
            img.load()

            meta = {
                "file_size": size,
                "width": w,
                "height": h,
                "format": fmt,
                "mode": mode,
            }

            return ImageValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                width=w,
                height=h,
                format_name=fmt,
                mode=mode,
                metadata=meta,
            )
    except Exception as e:
        return ImageValidationResult(
            is_valid=False,
            errors=[f"Failed to decode or verify image: {e}"]
        )
