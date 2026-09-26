"""Unit tests for ArtifactManager registration, hashing, and quarantine."""

from pathlib import Path
import pytest
from engine.artifact_manager.manager import ArtifactManager
from packages.contracts.src.artifact import ArtifactKind, QAStatus
from packages.project_format.src.db import ProjectDB


def test_artifact_manager_registration_and_retrieval(tmp_path: Path):
    proj_dir = tmp_path / "test_proj"
    proj_dir.mkdir(parents=True)
    db = ProjectDB(proj_dir / "movieforge.db")
    mgr = ArtifactManager(proj_dir, db)

    # Create dummy artifact file in renders/
    renders_dir = proj_dir / "renders"
    renders_dir.mkdir()
    sample_file = renders_dir / "shot_001.png"
    sample_file.write_bytes(b"PNG_SAMPLE_DATA_123456789")

    record = mgr.register_artifact(
        project_id="p1",
        kind=ArtifactKind.IMAGE,
        file_path=sample_file,
        producer="test_worker",
    )

    assert record.artifact_id.startswith("art_")
    assert record.size == len(b"PNG_SAMPLE_DATA_123456789")
    assert len(record.sha256) == 64

    # Retrieve from DB
    retrieved = mgr.get_artifact(record.artifact_id)
    assert retrieved is not None
    assert retrieved.artifact_id == record.artifact_id
    assert retrieved.sha256 == record.sha256
    assert retrieved.relative_path == "renders/shot_001.png"


def test_artifact_quarantine(tmp_path: Path):
    proj_dir = tmp_path / "test_proj"
    proj_dir.mkdir(parents=True)
    db = ProjectDB(proj_dir / "movieforge.db")
    mgr = ArtifactManager(proj_dir, db)

    corrupt_file = proj_dir / "corrupted.glb"
    corrupt_file.write_text("corrupted content", encoding="utf-8")

    quarantined = mgr.quarantine_file(corrupt_file, reason="Invalid GLB magic bytes")
    assert not corrupt_file.exists()
    assert quarantined.exists()
    assert quarantined.parent == proj_dir / ".movieforge" / "trash"
