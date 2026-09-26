"""Process supervisor managing child services, health checks, heartbeats, and state persistence."""

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from packages.contracts.src.worker import ServiceState
from packages.telemetry.src.logger import setup_logger


class ServiceEntry:
    def __init__(self, name: str, command: list[str], restart_policy: str = "always", max_restarts: int = 5):
        self.name = name
        self.command = command
        self.restart_policy = restart_policy
        self.max_restarts = max_restarts
        self.restart_count = 0
        self.state = ServiceState.STOPPED
        self.pid: int | None = None
        self.last_heartbeat: str | None = None
        self.last_start_time: float = 0.0


class ProcessSupervisor:
    def __init__(self, runtime_dir: Path | str = "runtime"):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file = self.runtime_dir / "supervisor.pid"
        self.state_file = self.runtime_dir / "service-state.json"
        self.logger = setup_logger("supervisor", self.runtime_dir / "supervisor.log")
        self.services: dict[str, ServiceEntry] = {}
        self.running = False

    def register_service(self, name: str, command: list[str], restart_policy: str = "always") -> None:
        self.services[name] = ServiceEntry(name, command, restart_policy)
        self.logger.info(f"Registered service: {name} (cmd={command})")

    def save_state(self) -> None:
        """Writes current supervisor status and tracked child process IDs to service-state.json."""
        pids = [s.pid for s in self.services.values() if s.pid is not None]
        state_data = {
            "supervisor_pid": os.getpid(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "RUNNING" if self.running else "STOPPED",
            "pids": pids,
            "services": {
                name: {
                    "state": s.state.value,
                    "pid": s.pid,
                    "restart_count": s.restart_count,
                    "last_heartbeat": s.last_heartbeat,
                }
                for name, s in self.services.items()
            },
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)

    def start(self) -> None:
        """Starts supervisor loop and writes supervisor.pid."""
        with open(self.pid_file, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))

        self.running = True
        self.logger.info(f"Supervisor started (PID={os.getpid()})")
        self.save_state()

    def stop(self) -> None:
        """Gracefully terminates tracked child services and cleans up PID files."""
        self.logger.info("Supervisor stopping services gracefully...")
        self.running = False

        for name, service in self.services.items():
            if service.pid is not None:
                self.logger.info(f"Terminating service {name} (PID={service.pid})...")
                service.state = ServiceState.STOPPING
                try:
                    os.kill(service.pid, signal.SIGTERM)
                except Exception:
                    pass
                service.state = ServiceState.STOPPED
                service.pid = None

        self.save_state()
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except Exception:
                pass
        self.logger.info("Supervisor stopped cleanly.")
