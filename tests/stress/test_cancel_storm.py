"""Stress H: queue many jobs, cancel a mix of queued/running jobs, verify no leaks."""

from engine.scheduler.scheduler import JobScheduler
from packages.contracts.src.job import JobStatus, ResourceEstimate
from packages.project_format.src.db import ProjectDB


def test_cancel_storm_no_leaks(tmp_path):
    db = ProjectDB(tmp_path / "storm.db")
    sched = JobScheduler(db, max_heavy_gpu=1)
    ids = [
        sched.submit_job(
            project_id="storm",
            job_type="image.generate",
            resource_estimate=ResourceEstimate(requires_heavy_gpu=bool(i % 2)),
        ).job_id
        for i in range(20)
    ]
    sched.update_job_status(ids[0], JobStatus.RUNNING)
    cancelled = 0
    for i, jid in enumerate(ids):
        if i % 3 == 0 and sched.request_cancel(jid):
            assert sched.confirm_cancel(jid)
            cancelled += 1
    assert cancelled > 0
    with db.get_connection() as conn:
        dangling = conn.execute("SELECT COUNT(*) c FROM jobs WHERE status = 'CANCEL_REQUESTED'").fetchone()["c"]
    assert dangling == 0
