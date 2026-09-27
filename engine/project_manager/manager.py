"""Project manager coordinating project loading, persistence, snapshots, and recovery."""

import json
from datetime import UTC, datetime
from pathlib import Path

from packages.project_format.src.db import ProjectDB
from packages.project_format.src.project import (
    ProjectManifest,
    init_project_structure,
    validate_project_structure,
)


class ProjectManager:
    def __init__(self, projects_root: Path | str = "projects"):
        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def create_project(
        self,
        name: str,
        project_id: str,
        description: str = "",
        target_resolution: tuple[int, int] = (1920, 1080),
        target_fps: int = 24,
    ) -> Path:
        """Initializes a new project directory with manifest and SQLite WAL database."""
        project_dir = self.projects_root / project_id
        if project_dir.exists():
            raise FileExistsError(f"Project directory already exists: {project_dir}")

        now = datetime.now(UTC).isoformat()
        manifest = ProjectManifest(
            name=name,
            project_id=project_id,
            version="0.1.0",
            created_at=now,
            updated_at=now,
            target_resolution=target_resolution,
            target_fps=target_fps,
            description=description,
        )

        init_project_structure(project_dir, manifest)

        # Initialize WAL database
        db_path = project_dir / "movieforge.db"
        db = ProjectDB(db_path)
        if not db.check_integrity():
            raise RuntimeError("Project database failed initial integrity check.")

        return project_dir

    def open_project(self, project_dir: Path | str) -> tuple[ProjectManifest, ProjectDB]:
        """Loads and validates an existing project, returning its manifest and DB handle."""
        p_dir = Path(project_dir)
        is_valid, errors = validate_project_structure(p_dir)
        if not is_valid:
            raise ValueError(f"Invalid project format at {p_dir}: {errors}")

        manifest_path = p_dir / "manifest.json"
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
            manifest = ProjectManifest.model_validate(data)

        db_path = p_dir / "movieforge.db"
        db = ProjectDB(db_path)
        if not db.check_integrity():
            raise RuntimeError(f"Database integrity check failed for project at {p_dir}")

        return manifest, db

    def create_snapshot(self, project_dir: Path | str, reason: str = "manual") -> Path:
        """Creates an atomic SQLite backup / snapshot in .movieforge/snapshots."""
        p_dir = Path(project_dir)
        snapshots_dir = p_dir / ".movieforge" / "snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        snapshot_file = snapshots_dir / f"snapshot_{timestamp}_{reason}.db"

        db_path = p_dir / "movieforge.db"
        if db_path.exists():
            # Perform safe online SQLite backup
            import sqlite3

            src = sqlite3.connect(str(db_path))
            dst = sqlite3.connect(str(snapshot_file))
            with dst:
                src.backup(dst)
            dst.close()
            src.close()

        meta_path = snapshots_dir / f"snapshot_{timestamp}_{reason}.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": timestamp,
                    "reason": reason,
                    "snapshot_file": snapshot_file.name,
                },
                f,
                indent=2,
            )

        return snapshot_file
