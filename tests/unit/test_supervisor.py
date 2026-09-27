"""Unit tests for supervisor launch, heartbeat, backoff, and bounded restarts."""

import sys
import time

from engine.supervisor.supervisor import ProcessSupervisor
from packages.contracts.src.worker import ServiceState


def test_launch_and_terminate_tracked_child(tmp_path):
    sup = ProcessSupervisor(runtime_dir=tmp_path / "runtime")
    sup.register_service("sleeper", [sys.executable, "-c", "import time; time.sleep(60)"], restart_policy="never")
    assert sup.launch_service("sleeper")
    assert sup.services["sleeper"].pid is not None
    report = sup.poll_services()
    assert report["sleeper"] == ServiceState.READY.value
    assert sup.terminate_service("sleeper")
    assert sup.services["sleeper"].state == ServiceState.STOPPED
    assert sup.services["sleeper"].pid is None


def test_crash_restart_bounded_then_disabled(tmp_path):
    sup = ProcessSupervisor(runtime_dir=tmp_path / "runtime")
    sup.register_service("crasher", [sys.executable, "-c", "exit(1)"], restart_policy="always", max_restarts=2)
    assert sup.launch_service("crasher")
    for _ in range(6):
        sup.poll_services()
        time.sleep(0.3)
        if sup.services["crasher"].state == ServiceState.DISABLED:
            break
    assert sup.services["crasher"].state == ServiceState.DISABLED
    assert sup.services["crasher"].restart_count <= 3


def test_backoff_grows_and_caps(tmp_path):
    sup = ProcessSupervisor(runtime_dir=tmp_path / "runtime")
    sup.register_service("x", [sys.executable, "-c", "exit(0)"], restart_policy="never")
    assert sup.backoff_delay("x") == 1.0
    sup.services["x"].restart_count = 10
    assert sup.backoff_delay("x") == 30.0
