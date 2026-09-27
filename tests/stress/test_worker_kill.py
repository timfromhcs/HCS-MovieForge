"""Stress C: kill a worker mid-load; supervisor must recover, project DB stays intact."""

import sys
import time

from engine.supervisor.supervisor import ProcessSupervisor
from packages.contracts.src.worker import ServiceState
from packages.project_format.src.db import ProjectDB


def test_worker_kill_recovery(tmp_path):
    db_path = tmp_path / "proj.db"
    db = ProjectDB(db_path)
    assert db.check_integrity()
    sup = ProcessSupervisor(runtime_dir=tmp_path / "runtime")
    sup.register_service(
        "loader", [sys.executable, "-c", "import time; time.sleep(60)"], restart_policy="always", max_restarts=5
    )
    assert sup.launch_service("loader")
    victim = sup.services["loader"]
    assert victim.process is not None
    victim.process.kill()  # uncontrolled kill during 'load'
    deadline = time.time() + 15
    recovered = False
    while time.time() < deadline:
        sup.poll_services()
        if sup.services["loader"].state in (ServiceState.READY, ServiceState.RECOVERING, ServiceState.STARTING):
            recovered = True
            break
        time.sleep(0.5)
    assert recovered
    assert db.check_integrity()
    sup.stop()
