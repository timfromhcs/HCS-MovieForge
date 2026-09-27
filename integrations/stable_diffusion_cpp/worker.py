"""stable-diffusion.cpp worker running Bonsai FLUX.2 Klein GGUF via Vulkan backend."""

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
from packages.validators.src.image_validator import validate_image


class StableDiffusionWorker(BaseWorker):
    def __init__(
        self,
        binary_path: Path | str = "bin/stable-diffusion-cpp/sd-cli.exe",
        models_dir: Path | str = "models",
    ):
        super().__init__(
            worker_id="worker_stable_diffusion",
            backend_name="stable-diffusion.cpp",
            backend_version="master-920",
        )
        self.binary_path = Path(binary_path).resolve()
        self.models_dir = Path(models_dir).resolve()
        self._current_process: subprocess.Popen | None = None

    def health(self) -> dict[str, Any]:
        if not self.binary_path.exists():
            return {"status": "error", "message": f"sd-cli binary not found at {self.binary_path}"}
        try:
            subprocess.run([str(self.binary_path), "--help"], capture_output=True, text=True, timeout=5)
            return {"status": "ok", "binary": str(self.binary_path)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def capabilities(self) -> WorkerCapabilities:
        return WorkerCapabilities(
            worker_id=self.worker_id,
            backend_name="stable-diffusion.cpp",
            backend_version=self.backend_version,
            supported_tasks=["image.generate", "image.edit", "character.generate_references"],
            compute_device="vulkan",
            is_heavy_gpu=True,
            vulkan_capable=True,
            cpu_capable=True,
        )

    def estimate(self, request: WorkerRequest) -> dict[str, Any]:
        return {"estimated_ram_mb": 2048, "estimated_vram_mb": 4096, "estimated_duration_sec": 15.0}

    def prepare(self, request: WorkerRequest) -> None:
        pass

    def run(self, request: WorkerRequest) -> WorkerResponse:
        self.state = ServiceState.BUSY
        self.current_job_id = request.job_id
        start_time = time.time()

        params = request.parameters
        prompt = params.get("prompt", "")
        negative_prompt = params.get("negative_prompt", "")
        model_file = params.get("model_file")
        vae_file = params.get("vae_file")
        clip_file = params.get("clip_file")
        output_image = params.get("output_image")
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        steps = params.get("steps", 20)
        cfg_scale = params.get("cfg_scale", 1.0)
        seed = params.get("seed", 42)

        # Auto-discover models in model store if not explicitly passed
        if not model_file or not os.path.exists(model_file):
            candidates = list(self.models_dir.glob("**/bonsai-flux2-klein-ternary-q2_k.gguf"))
            if candidates:
                model_file = str(candidates[0])
            else:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"Model file does not exist: {model_file}",
                )

        if not vae_file or not os.path.exists(vae_file):
            vae_candidates = list(self.models_dir.glob("**/flux2-vae.safetensors"))
            if vae_candidates:
                vae_file = str(vae_candidates[0])

        if not clip_file or not os.path.exists(clip_file):
            clip_candidates = list(self.models_dir.glob("**/Qwen3-4B-Q2_K.gguf"))
            if clip_candidates:
                clip_file = str(clip_candidates[0])

        if not output_image:
            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                error="Output image path was not specified.",
            )

        Path(output_image).parent.mkdir(parents=True, exist_ok=True)

        is_flux2 = "flux2" in str(model_file).lower() or "bonsai" in str(model_file).lower()

        if is_flux2:
            cmd = [
                str(self.binary_path),
                "--diffusion-model",
                str(model_file),
                "-p",
                prompt,
                "-o",
                str(output_image),
                "-W",
                str(width),
                "-H",
                str(height),
                "--steps",
                str(steps),
                "--cfg-scale",
                str(cfg_scale),
                "-s",
                str(seed),
                "--offload-to-cpu",
                "--diffusion-fa",
                "--vae-tiling",
            ]
            if vae_file and os.path.exists(vae_file):
                cmd.extend(["--vae", str(vae_file)])
            if clip_file and os.path.exists(clip_file):
                cmd.extend(["--llm", str(clip_file)])
        else:
            cmd = [
                str(self.binary_path),
                "-m",
                str(model_file),
                "-p",
                prompt,
                "-o",
                str(output_image),
                "-W",
                str(width),
                "-H",
                str(height),
                "--steps",
                str(steps),
                "--cfg-scale",
                str(cfg_scale),
                "-s",
                str(seed),
            ]
            if vae_file and os.path.exists(vae_file):
                cmd.extend(["--vae", str(vae_file)])
            if clip_file and os.path.exists(clip_file):
                cmd.extend(["--clip_l", str(clip_file)])
            if negative_prompt:
                cmd.extend(["-n", negative_prompt])

        try:
            self._current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = self._current_process.communicate(timeout=params.get("timeout_sec", 600))
            duration = time.time() - start_time

            if self._current_process.returncode != 0:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"sd-cli execution failed (code {self._current_process.returncode}): {stderr[-500:]}",
                )

            # Validate generated image
            val_res = validate_image(output_image, expected_width=width, expected_height=height)
            if not val_res.is_valid:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"Generated image failed validation: {val_res.errors}",
                )

            telemetry = WorkerTelemetry(
                worker_id=self.worker_id,
                backend="stable-diffusion.cpp",
                state=ServiceState.READY,
                duration_sec=round(duration, 3),
            )

            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                artifacts=[
                    {
                        "path": output_image,
                        "kind": "IMAGE",
                        "width": val_res.width,
                        "height": val_res.height,
                        "producer": "stable-diffusion.cpp",
                    }
                ],
                telemetry=telemetry,
            )

        except Exception as e:
            self.state = ServiceState.DEGRADED
            return WorkerResponse(
                status=ServiceState.DEGRADED,
                job_id=request.job_id,
                error=f"stable-diffusion worker exception: {e}",
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
