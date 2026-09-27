"""Short soak: bounded mixed light workload proving harness mechanics + memory trend.

The multi-hour profile (§74-I) is recorded as pending hardware certification; this test
runs a 60s representative loop and fails on memory growth or restart storms.
"""

import time

import psutil

from engine.scheduler.scheduler import JobScheduler
from integrations.blender.worker import BlenderWorker
from integrations.piper.worker import PiperWorker
from integrations.whisper_cpp.worker import WhisperWorker
from packages.contracts.src.job import JobStatus
from packages.project_format.src.db import ProjectDB


def test_soak_short_bounded(tmp_path):
    db = ProjectDB(tmp_path / "soak.db")
    sched = JobScheduler(db, max_heavy_gpu=1)
    workers = [BlenderWorker(), WhisperWorker(), PiperWorker()]
    proc = psutil.Process()
    rss_start = proc.memory_info().rss
    restarts = 0
    deadline = time.time() + 60
    cycles = 0
    while time.time() < deadline:
        for w in workers:
            h = w.health()
            if h.get("status") != "ok":
                restarts += 1
        job = sched.submit_job(project_id="soak", job_type="health.ping")
        sched.update_job_status(job.job_id, JobStatus.RUNNING)
        sched.update_job_status(job.job_id, JobStatus.SUCCEEDED)
        cycles += 1
        time.sleep(1)
    rss_end = proc.memory_info().rss
    growth_mb = (rss_end - rss_start) / (1024 * 1024)
    assert cycles >= 15
    assert restarts == 0
    assert growth_mb < 150, f"soak memory growth {growth_mb:.1f}MB"
