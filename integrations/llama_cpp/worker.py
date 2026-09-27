"""llama.cpp integration worker running Qwen3-VL 8B Instruct with Vulkan acceleration."""

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


class LlamaWorker(BaseWorker):
    def __init__(
        self,
        binary_path: Path | str = "bin/llama-cpp/llama-cli.exe",
        mtmd_binary_path: Path | str = "bin/llama-cpp/llama-mtmd-cli.exe",
        models_dir: Path | str = "models",
    ):
        super().__init__(worker_id="worker_llama", backend_name="llama.cpp", backend_version="b11205")
        self.binary_path = Path(binary_path).resolve()
        self.mtmd_binary_path = Path(mtmd_binary_path).resolve()
        self.models_dir = Path(models_dir).resolve()
        self._current_process: subprocess.Popen | None = None

    def health(self) -> dict[str, Any]:
        if not self.binary_path.exists() and not self.mtmd_binary_path.exists():
            return {"status": "error", "message": f"llama binaries not found at {self.binary_path}"}
        try:
            bin_to_check = self.mtmd_binary_path if self.mtmd_binary_path.exists() else self.binary_path
            res = subprocess.run([str(bin_to_check), "--version"], capture_output=True, text=True, timeout=5)
            version_line = res.stdout.splitlines()[0] if res.stdout else "b11205"
            return {"status": "ok", "version": version_line}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def capabilities(self) -> WorkerCapabilities:
        return WorkerCapabilities(
            worker_id=self.worker_id,
            backend_name="llama.cpp",
            backend_version=self.backend_version,
            supported_tasks=["agent.prompt", "agent.inspect_image", "agent.plan", "story.write_dialogue"],
            compute_device="vulkan",
            is_heavy_gpu=False,
            vulkan_capable=True,
            cpu_capable=True,
        )

    def estimate(self, request: WorkerRequest) -> dict[str, Any]:
        return {"estimated_ram_mb": 3072, "estimated_vram_mb": 5120, "estimated_duration_sec": 8.0}

    def prepare(self, request: WorkerRequest) -> None:
        pass

    def run(self, request: WorkerRequest) -> WorkerResponse:
        self.state = ServiceState.BUSY
        self.current_job_id = request.job_id
        start_time = time.time()

        params = request.parameters
        prompt = params.get("prompt", "")
        model_file = params.get("model_file")
        mmproj_file = params.get("mmproj_file")
        image_file = params.get("image_file")
        ctx_size = params.get("ctx_size", 2048)
        temp = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 512)
        n_gpu_layers = params.get("n_gpu_layers", 33)

        # Auto-discover models in model repository if not explicitly passed
        if not model_file or not os.path.exists(model_file):
            candidates = list(self.models_dir.glob("**/Qwen3VL-8B-Instruct-Q4_K_M.gguf"))
            if candidates:
                model_file = str(candidates[0])
            else:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"Model file does not exist: {model_file}",
                )

        if image_file and (not mmproj_file or not os.path.exists(mmproj_file)):
            mm_candidates = list(self.models_dir.glob("**/mmproj-Qwen3VL-8B-Instruct-F16.gguf"))
            if mm_candidates:
                mmproj_file = str(mm_candidates[0])

        is_multimodal = bool(image_file and mmproj_file and os.path.exists(mmproj_file))
        exec_bin = self.mtmd_binary_path if is_multimodal and self.mtmd_binary_path.exists() else self.binary_path

        cmd = [
            str(exec_bin),
            "-m",
            str(model_file),
            "-p",
            prompt,
            "-c",
            str(ctx_size),
            "-n",
            str(max_tokens),
            "--temp",
            str(temp),
            "--no-warmup",
            "-ngl",
            str(n_gpu_layers),
        ]

        if is_multimodal:
            cmd.extend(["--mmproj", str(mmproj_file), "--image", str(image_file)])

        try:
            self._current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = self._current_process.communicate(timeout=params.get("timeout_sec", 120))
            duration = time.time() - start_time

            if self._current_process.returncode != 0:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=(f"llama failed (code {self._current_process.returncode}): {stderr[-500:]}"),
                )

            # Extract clean output text (filter debug log lines)
            clean_lines = [
                line
                for line in stdout.splitlines()
                if not line.startswith("<") and not line.startswith("0.") and line.strip()
            ]
            response_text = "\n".join(clean_lines).strip()

            telemetry = WorkerTelemetry(
                worker_id=self.worker_id,
                backend="llama.cpp",
                state=ServiceState.READY,
                duration_sec=round(duration, 3),
            )

            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                artifacts=[{"text": response_text, "raw": stdout, "producer": "llama.cpp"}],
                telemetry=telemetry,
            )

        except Exception as e:
            self.state = ServiceState.DEGRADED
            return WorkerResponse(
                status=ServiceState.DEGRADED,
                job_id=request.job_id,
                error=f"llama worker exception: {e}",
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
