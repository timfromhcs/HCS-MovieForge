"""Unit tests for JobScheduler durable queuing, locality ordering, and concurrency limits."""

from pathlib import Path
import pytest
from engine.scheduler.scheduler import JobScheduler
from packages.contracts.src.job import JobPriority, JobStatus, ResourceEstimate
from packages.project_format.src.db import ProjectDB


def test_scheduler_queue_and_locality(tmp_path: Path):
    db_path = tmp_path / "test.db"
    db = ProjectDB(db_path)
    scheduler = JobScheduler(db, max_heavy_gpu=1)

    # Submit job 1: Bonsai (heavy)
    j1 = scheduler.submit_job(
        project_id="proj_1",
        job_type="image.generate",
        model_id="bonsai",
        resource_estimate=ResourceEstimate(requires_heavy_gpu=True),
    )

    # Submit job 2: Trellis (heavy)
    j2 = scheduler.submit_job(
        project_id="proj_1",
        job_type="3d.generate",
        model_id="trellis",
        resource_estimate=ResourceEstimate(requires_heavy_gpu=True),
    )

    # Submit job 3: Bonsai (heavy)
    j3 = scheduler.submit_job(
        project_id="proj_1",
        job_type="image.generate",
        model_id="bonsai",
        resource_estimate=ResourceEstimate(requires_heavy_gpu=True),
    )

    # If active model is "bonsai", locality scheduling should prefer job 1 or job 3 over job 2
    next_job = scheduler.get_next_job(currently_active_model="bonsai")
    assert next_job is not None
    assert next_job.model_id == "bonsai"

    # Start job 1
    scheduler.update_job_status(j1.job_id, JobStatus.RUNNING)

    # Now heavy GPU is at capacity (1) -> next heavy GPU job should NOT be picked
    next_after_running = scheduler.get_next_job()
    assert next_after_running is None

    # Submit a light job (e.g. STT Whisper)
    j_light = scheduler.submit_job(
        project_id="proj_1",
        job_type="stt.transcribe",
        model_id="whisper",
        resource_estimate=ResourceEstimate(requires_heavy_gpu=False),
    )

    # Light job can run even while heavy GPU is busy
    next_light = scheduler.get_next_job()
    assert next_light is not None
    assert next_light.job_id == j_light.job_id
