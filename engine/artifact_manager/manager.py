"""Artifact manager handling immutable artifact records, hashing, quarantine, and persistence."""

import json
import mimetypes
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from packages.contracts.src.artifact import ArtifactKind, ArtifactRecord, QAStatus
from packages.project_format.src.db import ProjectDB
from packages.validators.src.hash_validator import calculate_sha256


class ArtifactManager:
    def __init__(self, project_root: Path | str, db: ProjectDB):
        self.project_root = Path(project_root)
        self.db = db
        self.trash_dir = self.project_root / ".movieforge" / "trash"
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    def register_artifact(
        self,
        project_id: str,
        kind: ArtifactKind,
        file_path: Path | str,
        producer: str,
        producer_version: str = "0.1.0",
        model_id: str | None = None,
        model_revision: str | None = None,
        source_artifacts: list[str] | None = None,
        recipe_fingerprint: str | None = None,
        canonical: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactRecord:
        """Calculates hash, relative path, persists immutable record in SQLite DB, and returns record."""
        p = Path(file_path).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Cannot register non-existent file: {p}")

        root_resolved = self.project_root.resolve()
        try:
            rel_path = str(p.relative_to(root_resolved)).replace("\\", "/")
        except ValueError:
            # File is outside project root; copy to appropriate subdirectory
            subfolder = kind.value.lower().split("_")[0] + "s"
            dest_dir = self.project_root / subfolder
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f"{uuid.uuid4().hex[:8]}_{p.name}"
            shutil.copy2(str(p), str(dest))
            p = dest.resolve()
            rel_path = str(p.relative_to(root_resolved)).replace("\\", "/")

        size = p.stat().st_size
        sha256 = calculate_sha256(p)
        mime, _ = mimetypes.guess_type(str(p))
        if not mime:
            mime = "application/octet-stream"

        artifact_id = f"art_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        record = ArtifactRecord(
            artifact_id=artifact_id,
            project_id=project_id,
            kind=kind,
            path=str(p),
            relative_path=rel_path,
            size=size,
            sha256=sha256,
            mime=mime,
            created_at=now,
            producer=producer,
            producer_version=producer_version,
            model_id=model_id,
            model_revision=model_revision,
            source_artifacts=source_artifacts or [],
            recipe_fingerprint=recipe_fingerprint,
            qa_status=QAStatus.UNINSPECTED,
            canonical=canonical,
            metadata=metadata or {},
        )

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (
                    artifact_id, project_id, kind, path, relative_path, size, sha256,
                    mime, created_at, producer, producer_version, model_id, model_revision,
                    source_artifacts, recipe_fingerprint, qa_status, canonical, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.artifact_id,
                    record.project_id,
                    record.kind.value,
                    record.path,
                    record.relative_path,
                    record.size,
                    record.sha256,
                    record.mime,
                    record.created_at,
                    record.producer,
                    record.producer_version,
                    record.model_id,
                    record.model_revision,
                    json.dumps(record.source_artifacts),
                    record.recipe_fingerprint,
                    record.qa_status.value,
                    1 if record.canonical else 0,
                    json.dumps(record.metadata),
                ),
            )
            conn.commit()

        return record

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        """Retrieves an artifact record by ID."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ArtifactRecord(
                artifact_id=row["artifact_id"],
                project_id=row["project_id"],
                kind=ArtifactKind(row["kind"]),
                path=row["path"],
                relative_path=row["relative_path"],
                size=row["size"],
                sha256=row["sha256"],
                mime=row["mime"],
                created_at=row["created_at"],
                producer=row["producer"],
                producer_version=row["producer_version"],
                model_id=row["model_id"],
                model_revision=row["model_revision"],
                source_artifacts=json.loads(row["source_artifacts"] or "[]"),
                recipe_fingerprint=row["recipe_fingerprint"],
                qa_status=QAStatus(row["qa_status"]),
                canonical=bool(row["canonical"]),
                metadata=json.loads(row["metadata"] or "{}"),
            )

    def quarantine_file(self, file_path: Path | str, reason: str) -> Path:
        """Moves corrupted or partial files to .movieforge/trash with reason metadata."""
        p = Path(file_path)
        if not p.exists():
            return p

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = self.trash_dir / f"{timestamp}_{p.name}"
        shutil.move(str(p), str(dest))

        info_path = self.trash_dir / f"{timestamp}_{p.name}.meta.json"
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump({"original_path": str(p), "reason": reason, "timestamp": timestamp}, f, indent=2)

        return dest
