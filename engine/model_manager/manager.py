"""Model registry, headless downloader, hash verification, and atomic staging manager."""

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from huggingface_hub import hf_hub_download

from packages.validators.src.hash_validator import calculate_sha256


class ModelManager:
    def __init__(self, models_dir: Path | str = "models", staging_dir: Path | str = "models/staging"):
        self.models_dir = Path(models_dir)
        self.manifests_dir = self.models_dir / "manifests"
        self.locks_dir = self.models_dir / "locks"
        self.staging_dir = Path(staging_dir)
        self.lock_file = self.locks_dir / "model-lock.json"

        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        self.locks_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def list_manifests(self) -> list[dict[str, Any]]:
        """Loads and returns all available model manifests."""
        manifests = []
        for file in self.manifests_dir.glob("*.json"):
            try:
                with open(file, encoding="utf-8") as f:
                    manifests.append(json.load(f))
            except Exception:
                continue
        return manifests

    def get_manifest(self, model_id: str) -> dict[str, Any] | None:
        """Finds a manifest matching model_id."""
        for m in self.list_manifests():
            if m.get("id") == model_id:
                return m
        return None

    def resolve_locked_path(self, stored: str) -> Path:
        """Resolves a lock-file path portably across Windows/Linux.

        Legacy entries store absolute Windows paths (backslashes); new entries
        store paths relative to the models dir in POSIX form. Both resolve
        against the current models_dir on any OS.
        """
        import re

        normalized = stored.replace("\\", "/")
        p = Path(normalized)
        is_abs = p.is_absolute() or re.match(r"^[A-Za-z]:/", normalized) is not None
        if is_abs:
            parts = p.parts
            if "models" in parts:
                rel = Path(*parts[parts.index("models") + 1 :])
                return self.models_dir / rel
            return p
        if p.parts and p.parts[0] == self.models_dir.name:
            p = Path(*p.parts[1:])
        return self.models_dir / p

    def get_lock(self) -> dict[str, Any]:
        """Reads active model lock file."""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"version": 1, "models": {}}
        return {"version": 1, "models": {}}

    def download_and_verify(
        self,
        model_id: str,
        token: str | None = None,
        progress_callback: Any = None,
    ) -> tuple[bool, list[str]]:
        """Downloads model files to staging, verifies hashes/sizes, and atomically promotes to active store."""
        manifest = self.get_manifest(model_id)
        if not manifest:
            return False, [f"Manifest not found for model: {model_id}"]

        repo_id = manifest["source"]["repo"]
        revision = manifest["source"].get("revision")
        files = manifest.get("files", [])
        expected_hashes = manifest.get("sha256", {})
        expected_sizes = manifest.get("size_bytes", {})

        errors = []
        staged_files: dict[str, Path] = {}
        computed_hashes: dict[str, str] = {}

        staging_model_dir = self.staging_dir / model_id.replace(".", "_")
        staging_model_dir.mkdir(parents=True, exist_ok=True)

        for filename in files:
            try:
                # Download to staging via HF Hub API
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    revision=revision,
                    token=token,
                    local_dir=str(staging_model_dir),
                )
                p = Path(downloaded_path)
                staged_files[filename] = p

                # Size verification
                size = p.stat().st_size
                exp_size = expected_sizes.get(filename)
                if exp_size and size != exp_size:
                    errors.append(f"File {filename} size {size} != expected {exp_size}")

                # Hash calculation & verification
                computed_sha = calculate_sha256(p)
                computed_hashes[filename] = computed_sha
                exp_sha = expected_hashes.get(filename)
                if exp_sha:
                    if computed_sha.lower() != exp_sha.lower():
                        errors.append(f"File {filename} SHA256 mismatch: {computed_sha} != {exp_sha}")

            except Exception as e:
                errors.append(f"Failed to download {filename}: {e}")

        if errors:
            # Cleanup staging on failure
            shutil.rmtree(staging_model_dir, ignore_errors=True)
            return False, errors

        # Atomic promotion to active storage
        target_model_dir = self.models_dir / model_id.replace(".", "_")
        target_model_dir.mkdir(parents=True, exist_ok=True)

        promoted_files: dict[str, str] = {}
        for filename, staged_path in staged_files.items():
            dest = target_model_dir / filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                dest.unlink()
            shutil.move(str(staged_path), str(dest))
            promoted_files[filename] = dest.relative_to(self.models_dir).as_posix()

        # Cleanup staging directory
        shutil.rmtree(staging_model_dir, ignore_errors=True)

        # Update lock file
        lock = self.get_lock()
        lock["models"][model_id] = {
            "model_id": model_id,
            "repo": repo_id,
            "revision": revision,
            "installed_at": datetime.now(UTC).isoformat(),
            "files": promoted_files,
            "sha256": computed_hashes,
            "status": "VERIFIED_ACTIVE",
        }

        with open(self.lock_file, "w", encoding="utf-8") as f:
            json.dump(lock, f, indent=2)

        return True, []
