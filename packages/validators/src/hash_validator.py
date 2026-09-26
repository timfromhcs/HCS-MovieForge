"""Cryptographic hashing and integrity verification utilities."""

import hashlib
from pathlib import Path


def calculate_sha256(file_path: Path | str, chunk_size: int = 65536) -> str:
    """Computes SHA256 hexadecimal digest of a file in chunks."""
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_sha256(file_path: Path | str, expected_hash: str) -> bool:
    """Verifies whether the file's SHA256 matches expected_hash (case-insensitive)."""
    computed = calculate_sha256(file_path)
    return computed.lower() == expected_hash.strip().lower()
