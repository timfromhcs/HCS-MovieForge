"""Durable SQLite WAL job scheduler with model locality optimization and UMA heavy-GPU enforcement."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from packages.contracts.src.job import (
    JobPriority,
    JobRecord,
    JobStatus,
    ResourceEstimate,
    StructuredError,
)
from packages.project_format.src.db import ProjectDB


class JobScheduler:
    def __init__(self, db: ProjectDB, max_heavy_gpu: int = 1):
        self.db = db
        self.max_heavy_gpu = max_heavy_gpu

    def submit_job(
        self,
        project_id: str,
        job_type: str,
        model_id: str | None = None,
        model_revision: str | None = None,
        input_artifact_ids: list[str] | None = None,
        input_hashes: dict[str, str] | None = None,
        recipe_fingerprint: str | None = None,
        priority: JobPriority = JobPriority.NORMAL,
        resource_estimate: ResourceEstimate | None = None,
        parent_job: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> JobRecord:
        """Enqueues a new durable job into SQLite WAL queue."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        res_est = resource_estimate or ResourceEstimate()

        job = JobRecord(
            job_id=job_id,
            project_id=project_id,
            type=job_type,
            status=JobStatus.QUEUED,
            model_id=model_id,
            model_revision=model_revision,
            input_artifact_ids=input_artifact_ids or [],
            input_hashes=input_hashes or {},
            recipe_fingerprint=recipe_fingerprint,
            priority=priority,
            retry_count=0,
            max_retries=2,
            resource_estimate=res_est,
            created_at=now,
            updated_at=now,
            parent_job=parent_job,
            payload=payload or {},
        )

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, project_id, type, status, model_id, model_revision,
                    input_artifact_ids, input_hashes, recipe_fingerprint, priority,
                    retry_count, max_retries, resource_estimate, created_at, updated_at,
                    parent_job, child_jobs, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.project_id,
                    job.type,
                    job.status.value,
                    job.model_id,
                    job.model_revision,
                    json.dumps(job.input_artifact_ids),
                    json.dumps(job.input_hashes),
                    job.recipe_fingerprint,
                    job.priority.value,
                    job.retry_count,
                    job.max_retries,
                    job.resource_estimate.model_dump_json(),
                    job.created_at,
                    job.updated_at,
                    job.parent_job,
                    json.dumps(job.child_jobs),
                    json.dumps(job.payload),
                ),
            )
            conn.commit()

        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        """Retrieves a single job by ID."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_job(row)

    def get_next_job(self, currently_active_model: str | None = None) -> JobRecord | None:
        """Pick next eligible job with locality-aware order, keeping dependencies intact."""
        with self.db.get_connection() as conn:
            # Check currently running heavy GPU jobs count
            cursor = conn.execute("SELECT COUNT(*) as count FROM jobs WHERE status = 'RUNNING'")
            running_count = cursor.fetchone()["count"]

            # Fetch candidates ordered by priority desc, creation asc
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status IN ('QUEUED', 'WAITING_RESOURCE') "
                "ORDER BY priority DESC, created_at ASC"
            )
            rows = cursor.fetchall()
            if not rows:
                return None

            candidates = [self._row_to_job(r) for r in rows]

            # Filter out jobs whose parent jobs have not yet succeeded
            ready_candidates = []
            for c in candidates:
                if c.parent_job:
                    p_cursor = conn.execute("SELECT status FROM jobs WHERE job_id = ?", (c.parent_job,))
                    p_row = p_cursor.fetchone()
                    if not p_row or p_row["status"] != JobStatus.SUCCEEDED.value:
                        continue
                ready_candidates.append(c)

            if not ready_candidates:
                return None

            # If heavy GPU is currently busy, skip heavy GPU candidates
            if running_count >= self.max_heavy_gpu:
                light_candidates = [c for c in ready_candidates if not c.resource_estimate.requires_heavy_gpu]
                if not light_candidates:
                    return None
                selected = light_candidates[0]
            else:
                # Model locality optimization:
                # If currently_active_model is set, check if an independent candidate uses the same model
                matched_locality = None
                if currently_active_model:
                    for c in ready_candidates:
                        if c.model_id == currently_active_model:
                            matched_locality = c
                            break
                selected = matched_locality if matched_locality else ready_candidates[0]

            return selected

    def request_cancel(self, job_id: str) -> bool:
        """Marks a cancellable job CANCEL_REQUESTED (cooperative first step)."""
        job = self.get_job(job_id)
        if job is None:
            return False
        if job.status in (
            JobStatus.QUEUED,
            JobStatus.WAITING_RESOURCE,
            JobStatus.PREPARING,
            JobStatus.PRELOADING,
            JobStatus.RUNNING,
        ):
            self.update_job_status(job_id, JobStatus.CANCEL_REQUESTED)
            return True
        return False

    def confirm_cancel(self, job_id: str) -> bool:
        """Moves a CANCEL_REQUESTED job to CANCELLED after the worker stopped safely."""
        job = self.get_job(job_id)
        if job is None or job.status != JobStatus.CANCEL_REQUESTED:
            return False
        self.update_job_status(job_id, JobStatus.CANCELLED)
        return True

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        worker_id: str | None = None,
        output_artifact_ids: list[str] | None = None,
        error: StructuredError | None = None,
    ) -> None:
        """Transitions job state safely."""
        now = datetime.now(UTC).isoformat()
        with self.db.get_connection() as conn:
            updates = ["status = ?", "updated_at = ?"]
            params: list[Any] = [status.value, now]

            if worker_id is not None:
                updates.append("worker_id = ?")
                params.append(worker_id)
            if output_artifact_ids is not None:
                updates.append("output_artifact_ids = ?")
                params.append(json.dumps(output_artifact_ids))
            if error is not None:
                updates.append("error = ?")
                params.append(error.model_dump_json())

            if status == JobStatus.RUNNING:
                updates.append("started_at = ?")
                params.append(now)
            elif status in (JobStatus.SUCCEEDED, JobStatus.FAILED_FINAL, JobStatus.CANCELLED):
                updates.append("completed_at = ?")
                params.append(now)

            params.append(job_id)
            query = f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?"
            conn.execute(query, params)
            conn.commit()

    def _row_to_job(self, row: Any) -> JobRecord:
        raw_est = row["resource_estimate"]
        res_est = ResourceEstimate.model_validate_json(raw_est) if raw_est else ResourceEstimate()
        err = StructuredError.model_validate_json(row["error"]) if row["error"] else None
        return JobRecord(
            job_id=row["job_id"],
            project_id=row["project_id"],
            type=row["type"],
            status=JobStatus(row["status"]),
            model_id=row["model_id"],
            model_revision=row["model_revision"],
            input_artifact_ids=json.loads(row["input_artifact_ids"] or "[]"),
            input_hashes=json.loads(row["input_hashes"] or "{}"),
            recipe_fingerprint=row["recipe_fingerprint"],
            priority=JobPriority(row["priority"]),
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            resource_estimate=res_est,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            parent_job=row["parent_job"],
            child_jobs=json.loads(row["child_jobs"] or "[]"),
            worker_id=row["worker_id"],
            output_artifact_ids=json.loads(row["output_artifact_ids"] or "[]"),
            error=err,
            payload=json.loads(row["payload"] or "{}"),
        )
