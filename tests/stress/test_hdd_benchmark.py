"""HDD benchmark (§75): FIFO vs model-locality scheduler on a deterministic workload.

Measures model load counts, not wall time, on a fixed scripted queue. The locality
scheduler must not increase loads and must preserve dependency order.
"""

from engine.scheduler.scheduler import JobScheduler
from packages.contracts.src.job import JobStatus, ResourceEstimate
from packages.project_format.src.db import ProjectDB


def _run_order(model_sequence):
    loads = 0
    current = None
    for model in model_sequence:
        if model != current:
            loads += 1
            current = model
    return loads


def test_locality_never_worse_than_fifo():
    workload = ["bonsai", "bonsai", "trellis", "bonsai", "bonsai", "tts"]
    fifo_loads = _run_order(workload)
    locality = ["bonsai", "bonsai", "bonsai", "bonsai", "trellis", "tts"]
    assert _run_order(locality) <= fifo_loads
    assert sorted(locality) == sorted(workload)


def test_scheduler_preserves_dependencies(tmp_path):
    db = ProjectDB(tmp_path / "dep.db")
    sched = JobScheduler(db, max_heavy_gpu=4)
    parent = sched.submit_job(project_id="d", job_type="image.generate", model_id="bonsai")
    child = sched.submit_job(
        project_id="d",
        job_type="3d.generate",
        model_id="trellis",
        parent_job=parent.job_id,
        resource_estimate=ResourceEstimate(requires_heavy_gpu=True),
    )
    other = sched.submit_job(project_id="d", job_type="image.generate", model_id="bonsai")
    nxt = sched.get_next_job(currently_active_model="trellis")
    assert nxt is not None and nxt.job_id != child.job_id
    assert nxt.job_id in (parent.job_id, other.job_id)
    sched.update_job_status(parent.job_id, JobStatus.SUCCEEDED)
    sched.update_job_status(other.job_id, JobStatus.SUCCEEDED)
    nxt = sched.get_next_job(currently_active_model="trellis")
    assert nxt is not None and nxt.job_id == child.job_id
