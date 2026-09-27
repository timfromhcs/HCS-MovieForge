"""Unit tests for the bounded OOM recovery ladder and cooperative cancellation."""

from engine.cache_manager.manager import CacheManager
from engine.recovery.oom import recover_oom
from engine.resource_manager.manager import ResourceManager
from engine.scheduler.scheduler import JobScheduler
from packages.contracts.src.job import JobStatus, ResourceEstimate
from packages.project_format.src.db import ProjectDB


def test_oom_ladder_quarantines_and_allows_retry(tmp_path):
    res = ResourceManager(runtime_dir=tmp_path / "runtime")
    cache = CacheManager(cache_dir=tmp_path / "cache", size_limit_mb=64)
    partial = tmp_path / "half.png"
    partial.write_bytes(b"partial-bytes")
    out = recover_oom(
        "job_oom",
        res,
        cache_mgr=cache,
        partial_files=[partial],
        trash_dir=tmp_path / "trash",
    )
    assert not partial.exists()
    assert any("quarantined" in a for a in out["actions"])
    assert out["retry_config"]["estimate_ram_mb"] <= 1024
    assert isinstance(out["blocked"], bool)


def test_oom_ladder_no_cache_no_partials(tmp_path):
    res = ResourceManager(runtime_dir=tmp_path / "runtime")
    out = recover_oom("job_x", res)
    assert out["job_id"] == "job_x"
    assert "retry_config" in out


def test_cooperative_cancel_flow(tmp_path):
    db = ProjectDB(tmp_path / "jobs.db")
    sched = JobScheduler(db)
    job = sched.submit_job(
        project_id="p1",
        job_type="image.generate",
        resource_estimate=ResourceEstimate(requires_heavy_gpu=True),
    )
    assert sched.request_cancel(job.job_id)
    assert sched.get_job(job.job_id).status == JobStatus.CANCEL_REQUESTED
    assert sched.confirm_cancel(job.job_id)
    assert sched.get_job(job.job_id).status == JobStatus.CANCELLED
    assert not sched.request_cancel(job.job_id)
    assert not sched.confirm_cancel(job.job_id)
