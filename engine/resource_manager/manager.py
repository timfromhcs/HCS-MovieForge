"""UMA resource manager: probes hardware, derives safe budgets, arbitrates heavy-GPU leases."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

from packages.telemetry.src.probe import probe_hardware


class ResourceManager:
    def __init__(self, runtime_dir: Path | str = "runtime") -> None:
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.runtime_dir / "hardware-profile.json"
        self.lease_path = self.runtime_dir / "gpu-leases.json"
        self.profile = probe_hardware(str(self.runtime_dir))

    def save_profile(self) -> Path:
        """Persists the current hardware profile with safe UMA budgets to disk."""
        payload = self.profile.model_dump()
        payload["calibrated_at"] = datetime.now(UTC).isoformat()
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return self.profile_path

    def load_profile(self) -> dict[str, Any] | None:
        """Loads a previously calibrated profile, or None when never calibrated."""
        if not self.profile_path.exists():
            return None
        with open(self.profile_path, encoding="utf-8") as f:
            return json.load(f)

    def _read_leases(self) -> dict[str, Any]:
        if not self.lease_path.exists():
            return {"holders": {}}
        try:
            with open(self.lease_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"holders": {}}

    def _write_leases(self, data: dict[str, Any]) -> None:
        tmp = self.lease_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(self.lease_path)

    def active_heavy_count(self) -> int:
        """Counts live heavy-GPU lease holders, pruning dead PIDs."""
        data = self._read_leases()
        holders = data.get("holders", {})
        live: dict[str, Any] = {}
        for job_id, info in holders.items():
            pid = info.get("pid")
            try:
                if pid is not None and psutil.pid_exists(pid):
                    live[job_id] = info
            except Exception:
                continue
        if len(live) != len(holders):
            self._write_leases({"holders": live})
        return len(live)

    def available_ram_mb(self) -> int:
        """Returns real currently available system RAM in MB."""
        return int(psutil.virtual_memory().available / (1024 * 1024))

    def acquire_heavy_lease(self, job_id: str, estimate_ram_mb: int = 2048) -> tuple[bool, str]:
        """Acquires a heavy-GPU slot when concurrency and RAM budget allow it."""
        import os

        max_heavy = self.profile.max_heavy_gpu_jobs
        if self.active_heavy_count() >= max_heavy:
            return False, f"heavy GPU at capacity ({max_heavy} slot(s) busy)"
        reserve = self.profile.os_safety_reserve_mb + self.profile.blender_reserve_mb
        total = self.profile.system_memory.total_ram_mb
        avail = self.available_ram_mb()
        if avail - estimate_ram_mb < reserve and avail < total - reserve:
            # Still allow when machine is large but momentarily pressured? No: be strict.
            if avail < estimate_ram_mb + reserve // 2:
                return False, f"insufficient RAM: avail={avail}MB need~{estimate_ram_mb}MB reserve={reserve}MB"
        data = self._read_leases()
        data.setdefault("holders", {})[job_id] = {
            "pid": os.getpid(),
            "acquired_at": datetime.now(UTC).isoformat(),
            "estimate_ram_mb": estimate_ram_mb,
        }
        self._write_leases(data)
        return True, "lease acquired"

    def release_heavy_lease(self, job_id: str) -> bool:
        """Releases a previously acquired heavy-GPU lease."""
        data = self._read_leases()
        if job_id in data.get("holders", {}):
            del data["holders"][job_id]
            self._write_leases(data)
            return True
        return False

    def status(self) -> dict[str, Any]:
        """Returns live resource status for doctor/benchmark consumers."""
        return {
            "total_ram_mb": self.profile.system_memory.total_ram_mb,
            "available_ram_mb": self.available_ram_mb(),
            "os_reserve_mb": self.profile.os_safety_reserve_mb,
            "blender_reserve_mb": self.profile.blender_reserve_mb,
            "model_budget_mb": self.profile.model_budget_mb,
            "max_heavy_gpu_jobs": self.profile.max_heavy_gpu_jobs,
            "active_heavy": self.active_heavy_count(),
            "calibrated": self.profile_path.exists(),
        }
