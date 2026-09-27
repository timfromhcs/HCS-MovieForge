"""Blender headless worker executing Python automation scripts for rendering, rigging, and assembly."""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any
from engine.workers.base import BaseWorker
from packages.contracts.src.worker import (
    ServiceState,
    WorkerCapabilities,
    WorkerRequest,
    WorkerResponse,
    WorkerTelemetry,
)


class BlenderWorker(BaseWorker):
    def __init__(self, blender_path: str | None = None, runtime_dir: Path | str = "runtime"):
        super().__init__(worker_id="worker_blender", backend_name="blender", backend_version="5.1.2")
        self.blender_path = blender_path or self._find_blender()
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._current_process: subprocess.Popen | None = None

    def _find_blender(self) -> str:
        found = shutil.which("blender")
        if found:
            return found
        default_path = Path("C:/Program Files/Blender Foundation/Blender 5.1/blender.exe")
        if default_path.exists():
            return str(default_path)
        return "blender"

    def health(self) -> dict[str, Any]:
        if not os.path.exists(self.blender_path):
            return {"status": "error", "message": f"Blender executable not found at {self.blender_path}"}
        try:
            res = subprocess.run([self.blender_path, "--version"], capture_output=True, text=True, timeout=5)
            version_str = res.stdout.splitlines()[0] if res.stdout else "unknown"
            return {"status": "ok", "version": version_str}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def capabilities(self) -> WorkerCapabilities:
        return WorkerCapabilities(
            worker_id=self.worker_id,
            backend_name="blender",
            backend_version=self.backend_version,
            supported_tasks=[
                "blender.import_asset",
                "blender.create_scene",
                "blender.render_turntable",
                "blender.render_shot",
                "blender.vse_timeline",
            ],
            compute_device="vulkan_or_cpu",
            is_heavy_gpu=False,
            vulkan_capable=True,
            cpu_capable=True,
        )

    def estimate(self, request: WorkerRequest) -> dict[str, Any]:
        return {"estimated_ram_mb": 2048, "estimated_vram_mb": 2048, "estimated_duration_sec": 5.0}

    def prepare(self, request: WorkerRequest) -> None:
        pass

    def run(self, request: WorkerRequest) -> WorkerResponse:
        self.state = ServiceState.BUSY
        self.current_job_id = request.job_id
        start_time = time.time()

        task_type = request.task_type
        params = request.parameters
        script_content = params.get("script")
        output_path = params.get("output_path", str(self.runtime_dir / f"{request.job_id}_render.png"))

        if not script_content:
            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                error="Blender task requires 'script' parameter containing Python script.",
            )

        script_file = self.runtime_dir / f"blender_job_{request.job_id}.py"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)

        cmd = [self.blender_path, "-b", "--python", str(script_file)]

        try:
            self._current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = self._current_process.communicate(timeout= params.get("timeout_sec", 60))
            duration = time.time() - start_time

            if script_file.exists():
                script_file.unlink()

            if self._current_process.returncode != 0:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"Blender script execution failed (code {self._current_process.returncode}): {stderr[-500:]}",
                )

            artifacts = []
            if os.path.exists(output_path):
                artifacts.append({"path": output_path, "producer": "blender"})

            telemetry = WorkerTelemetry(
                worker_id=self.worker_id,
                backend="blender",
                state=ServiceState.READY,
                duration_sec=round(duration, 3),
            )

            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                artifacts=artifacts,
                telemetry=telemetry,
            )

        except Exception as e:
            self.state = ServiceState.DEGRADED
            return WorkerResponse(
                status=ServiceState.DEGRADED,
                job_id=request.job_id,
                error=f"Blender worker exception: {e}",
            )
        finally:
            self._current_process = None

    def cancel(self, job_id: str) -> bool:
        if self._current_process and self.current_job_id == job_id:
            self._current_process.terminate()
            return True
        return False

    def cleanup(self) -> None:
        pass

    def shutdown(self) -> None:
        if self._current_process:
            self._current_process.terminate()
        self.state = ServiceState.STOPPED
