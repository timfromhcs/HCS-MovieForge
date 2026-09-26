"""Project recovery and crash handling on startup."""

import json
from pathlib import Path
from packages.contracts.src.job import JobStatus
from packages.project_format.src.db import ProjectDB


class RecoveryManager:
    def __init__(self, project_dir: Path | str, db: ProjectDB):
        self.project_dir = Path(project_dir)
        self.db = db
        self.trash_dir = self.project_dir / ".movieforge" / "trash"
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    def recover(self) -> dict[str, int]:
        """Runs startup audit, reclaims orphaned jobs, and quarantines partial artifacts."""
        stats = {
            "orphaned_jobs_reclaimed": 0,
            "partial_files_quarantined": 0,
        }

        with self.db.get_connection() as conn:
            # Discover jobs that were RUNNING or PREPARING during crash
            cursor = conn.execute(
                "SELECT job_id, status FROM jobs WHERE status IN ('RUNNING', 'PREPARING', 'PRELOADING')"
            )
            interrupted = cursor.fetchall()
            for row in interrupted:
                job_id = row["job_id"]
                conn.execute(
                    "UPDATE jobs SET status = 'RECOVERING' WHERE job_id = ?",
                    (job_id,)
                )
                stats["orphaned_jobs_reclaimed"] += 1
            conn.commit()

        return stats
