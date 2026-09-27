"""TRELLIS.cpp worker executing native C++/GGML image-to-3D pipeline via Vulkan."""

import os
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
from packages.validators.src.mesh_validator import validate_glb


class TrellisWorker(BaseWorker):
    def __init__(
        self,
        binary_path: Path | str = "bin/trellis-cpp/trellis-cli.exe",
        models_dir: Path | str = "models/3d_trellis2_q4",
    ):
        super().__init__(worker_id="worker_trellis", backend_name="trellis.cpp", backend_version="0.8.1")
        self.binary_path = Path(binary_path).resolve()
        self.models_dir = Path(models_dir).resolve()
        self._current_process: subprocess.Popen | None = None

    def health(self) -> dict[str, Any]:
        if not self.binary_path.exists():
            return {"status": "error", "message": f"Trellis binary not found at {self.binary_path}"}
        try:
            subprocess.run([str(self.binary_path), "--help"], capture_output=True, text=True, timeout=5)
            return {"status": "ok", "binary": str(self.binary_path)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def capabilities(self) -> WorkerCapabilities:
        return WorkerCapabilities(
            worker_id=self.worker_id,
            backend_name="trellis.cpp",
            backend_version=self.backend_version,
            supported_tasks=["3d.image_to_3d", "image.remove_background"],
            compute_device="vulkan",
            is_heavy_gpu=True,
            vulkan_capable=True,
            cpu_capable=True,
        )

    def estimate(self, request: WorkerRequest) -> dict[str, Any]:
        res = request.parameters.get("resolution", 512)
        vram = 6144 if res == 512 else 8192
        return {"estimated_ram_mb": 4096, "estimated_vram_mb": vram, "estimated_duration_sec": 30.0}

    def prepare(self, request: WorkerRequest) -> None:
        pass

    def run(self, request: WorkerRequest) -> WorkerResponse:
        self.state = ServiceState.BUSY
        self.current_job_id = request.job_id
        start_time = time.time()

        params = request.parameters
        image_path = params.get("image_path")
        output_glb = params.get("output_glb")
        resolution = params.get("resolution", 512)
        steps = params.get("steps", 12)
        bg_removal = params.get("bg_removal", "auto")
        models_p = Path(params.get("models_dir", str(self.models_dir)))
        if (models_p / "q4").exists() and not (models_p / "dinov3.gguf").exists():
            models_p = models_p / "q4"

        if not image_path or not os.path.exists(image_path):
            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                error=f"Input image does not exist: {image_path}",
            )

        if not output_glb:
            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                error="Output GLB path was not specified.",
            )

        Path(output_glb).parent.mkdir(parents=True, exist_ok=True)

        backend = params.get("backend", "CPU")
        box_uv = params.get("box_uv", True)
        no_texture = params.get("no_texture", False)
        seed = params.get("seed", 42)

        cmd = [
            str(self.binary_path),
            "--image",
            str(image_path),
            "--output",
            str(output_glb),
            "-m",
            str(models_p),
            "--res",
            str(resolution),
            "--steps",
            str(steps),
            "--backend",
            backend,
            "-s",
            str(seed),
        ]

        if box_uv:
            cmd.append("--box-uv")
        if no_texture:
            cmd.append("--no-texture")
        if bg_removal == "birefnet" and (models_p / "birefnet.gguf").exists():
            cmd.append("--birefnet")

        try:
            self._current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = self._current_process.communicate(timeout=params.get("timeout_sec", 600))
            duration = time.time() - start_time

            if self._current_process.returncode != 0:
                # If Vulkan failed, attempt automatic CPU fallback if not already on CPU
                if backend.upper() == "VULKAN":
                    cmd_cpu = [c if c != "Vulkan" else "CPU" for c in cmd]
                    self._current_process = subprocess.Popen(
                        cmd_cpu, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    timeout = params.get("timeout_sec", 600)
                    stdout, stderr = self._current_process.communicate(timeout=timeout)
                    duration = time.time() - start_time
                    if self._current_process.returncode != 0:
                        self.state = ServiceState.READY
                        return WorkerResponse(
                            status=ServiceState.READY,
                            job_id=request.job_id,
                            error=(
                                f"trellis-cli failed on Vulkan+CPU (code {self._current_process.returncode}): "
                                f"{stderr[-500:]}"
                            ),
                        )
                else:
                    self.state = ServiceState.READY
                    return WorkerResponse(
                        status=ServiceState.READY,
                        job_id=request.job_id,
                        error=(f"trellis-cli failed (code {self._current_process.returncode}): {stderr[-500:]}"),
                    )

            # Validate generated GLB
            val_res = validate_glb(output_glb)
            if not val_res.is_valid:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"Generated GLB failed validation: {val_res.errors}",
                )

            telemetry = WorkerTelemetry(
                worker_id=self.worker_id,
                backend="trellis.cpp",
                state=ServiceState.READY,
                duration_sec=round(duration, 3),
            )

            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                artifacts=[
                    {
                        "path": output_glb,
                        "kind": "MESH_RAW",
                        "vertex_count": val_res.vertex_count,
                        "face_count": val_res.face_count,
                        "producer": "trellis.cpp",
                    }
                ],
                telemetry=telemetry,
            )

        except Exception as e:
            self.state = ServiceState.DEGRADED
            return WorkerResponse(
                status=ServiceState.DEGRADED,
                job_id=request.job_id,
                error=f"Trellis worker exception: {e}",
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
