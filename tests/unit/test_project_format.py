"""Unit tests for project directory format and SQLite WAL database."""

from pathlib import Path

from packages.project_format.src.db import ProjectDB
from packages.project_format.src.project import (
    ProjectManifest,
    init_project_structure,
    validate_project_structure,
)


def test_project_initialization_and_validation(tmp_path: Path):
    proj_dir = tmp_path / "my_film"
    manifest = ProjectManifest(
        name="My Film",
        project_id="film_01",
        created_at="2026-09-27T00:00:00Z",
        updated_at="2026-09-27T00:00:00Z",
    )

    init_project_structure(proj_dir, manifest)
    is_valid, errors = validate_project_structure(proj_dir)
    assert is_valid is True
    assert len(errors) == 0

    # Ensure database initializes with WAL mode
    db = ProjectDB(proj_dir / "movieforge.db")
    assert db.check_integrity() is True

    with db.get_connection() as conn:
        cursor = conn.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        assert mode.lower() == "wal"
