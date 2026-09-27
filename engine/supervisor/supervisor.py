"""Process supervisor managing child services, health checks, heartbeats, and state persistence."""

import json
import os
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

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
        self.process: subprocess.Popen | None = None
        self.restart_timestamps: list[float] = []


class ProcessSupervisor:
    def __init__(self, runtime_dir: Path | str = "runtime"):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file = self.runtime_dir / "supervisor.pid"
        self.state_file = self.runtime_dir / "service-state.json"
        self.logger = setup_logger("supervisor", self.runtime_dir / "supervisor.log")
        self.services: dict[str, ServiceEntry] = {}
        self.running = False

    def register_service(
        self, name: str, command: list[str], restart_policy: str = "always", max_restarts: int = 5
    ) -> None:
        self.services[name] = ServiceEntry(name, command, restart_policy, max_restarts)
        self.logger.info(f"Registered service: {name} (cmd={command})")

    def save_state(self) -> None:
        """Writes current supervisor status and tracked child process IDs to service-state.json."""
        pids = [s.pid for s in self.services.values() if s.pid is not None]
        state_data = {
            "supervisor_pid": os.getpid(),
            "timestamp": datetime.now(UTC).isoformat(),
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

    def launch_service(self, name: str) -> bool:
        """Spawns a registered service as a tracked child process with log routing."""
        service = self.services.get(name)
        if service is None:
            return False
        logs_dir = self.runtime_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"{name}.log"
        try:
            log_file = open(log_path, "ab")  # noqa: PTH123 - intentional append-binary routing
            service.process = subprocess.Popen(
                service.command, stdout=log_file, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL
            )
        except Exception as e:
            self.logger.info(f"Service {name} failed to launch: {e}")
            service.state = ServiceState.CRASHED
            return False
        service.pid = service.process.pid
        service.state = ServiceState.STARTING
        service.last_start_time = time.time()
        self.heartbeat(name)
        self.logger.info(f"Service {name} launched (PID={service.pid})")
        self.save_state()
        return True

    def heartbeat(self, name: str) -> None:
        """Records a heartbeat for a service."""
        service = self.services.get(name)
        if service is not None:
            service.last_heartbeat = datetime.now(UTC).isoformat()

    def backoff_delay(self, name: str) -> float:
        """Exponential backoff delay in seconds, capped at 30s."""
        service = self.services[name]
        return min(2.0**service.restart_count, 30.0)

    def poll_services(self) -> dict[str, str]:
        """Reaps child states; restarts crashed restartable services within rate limits."""
        report: dict[str, str] = {}
        now = time.time()
        for name, service in self.services.items():
            proc = service.process
            if proc is None:
                report[name] = service.state.value
                continue
            ret = proc.poll()
            if ret is None:
                if service.state == ServiceState.STARTING:
                    service.state = ServiceState.READY
                report[name] = service.state.value
                continue
            # Process exited
            if ret == 0 and service.state in (ServiceState.STOPPING, ServiceState.STOPPED):
                report[name] = service.state.value
                continue
            service.state = ServiceState.CRASHED
            service.pid = None
            service.process = None
            if service.restart_policy == "never":
                report[name] = service.state.value
                continue
            window = [t for t in service.restart_timestamps if now - t < 300]
            service.restart_timestamps = window
            if len(window) >= service.max_restarts:
                service.state = ServiceState.DISABLED
                self.logger.info(f"Service {name} exceeded restart rate; DISABLED.")
                report[name] = service.state.value
                continue
            delay = self.backoff_delay(name)
            self.logger.info(f"Service {name} crashed; restarting in {delay:.1f}s.")
            time.sleep(min(delay, 2.0))
            service.restart_count += 1
            service.restart_timestamps.append(time.time())
            service.state = ServiceState.RECOVERING
            self.launch_service(name)
            report[name] = service.state.value
        self.save_state()
        return report

    def terminate_service(self, name: str) -> bool:
        """Terminates only the known tracked child process for a service."""
        service = self.services.get(name)
        if service is None or service.process is None:
            return False
        service.state = ServiceState.STOPPING
        try:
            service.process.terminate()
            service.process.wait(timeout=10)
        except Exception:
            try:
                service.process.kill()
            except Exception:
                pass
        service.state = ServiceState.STOPPED
        service.pid = None
        service.process = None
        self.save_state()
        return True

    def stop(self) -> None:
        """Gracefully terminates tracked child services and cleans up PID files."""
        self.logger.info("Supervisor stopping services gracefully...")
        self.running = False

        for name, service in self.services.items():
            if service.process is not None:
                self.terminate_service(name)
            elif service.pid is not None:
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
