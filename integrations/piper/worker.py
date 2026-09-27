"""Piper neural TTS worker generating local, low-latency dialogue audio from text."""

import os
import subprocess
import sys
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
from packages.validators.src.audio_validator import validate_audio


class PiperWorker(BaseWorker):
    def __init__(self, models_dir: Path | str = "models", runtime_dir: Path | str = "runtime"):
        super().__init__(worker_id="worker_piper", backend_name="piper", backend_version="1.8.0")
        self.models_dir = Path(models_dir).resolve()
        self.runtime_dir = Path(runtime_dir).resolve()
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._current_process: subprocess.Popen | None = None

    def health(self) -> dict[str, Any]:
        try:
            res = subprocess.run([sys.executable, "-m", "piper", "--help"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return {"status": "ok", "version": "1.8.0"}
            return {"status": "error", "message": res.stderr}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def capabilities(self) -> WorkerCapabilities:
        return WorkerCapabilities(
            worker_id=self.worker_id,
            backend_name="piper",
            backend_version=self.backend_version,
            supported_tasks=["audio.synthesize_speech", "voice.generate"],
            compute_device="cpu",
            is_heavy_gpu=False,
            vulkan_capable=False,
            cpu_capable=True,
        )

    def estimate(self, request: WorkerRequest) -> dict[str, Any]:
        text_len = len(request.parameters.get("text", ""))
        sec = max(text_len / 40.0, 0.5)
        return {"estimated_ram_mb": 512, "estimated_vram_mb": 0, "estimated_duration_sec": sec}

    def prepare(self, request: WorkerRequest) -> None:
        pass

    def run(self, request: WorkerRequest) -> WorkerResponse:
        self.state = ServiceState.BUSY
        self.current_job_id = request.job_id
        start_time = time.time()

        params = request.parameters
        text = params.get("text") or params.get("prompt")
        model_path = params.get("model_path")
        config_path = params.get("config_path")
        output_wav = params.get("output_wav", str(self.runtime_dir / f"{request.job_id}.wav"))
        speaker = params.get("speaker", 0)

        if not text:
            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                error="Piper worker requires 'text' parameter.",
            )

        if not model_path or not os.path.exists(model_path):
            # Look in models directory for default piper onnx
            candidates = list(self.models_dir.glob("**/en_US-lessac-medium.onnx"))
            if candidates:
                model_path = str(candidates[0])
            else:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"Piper voice model not found: {model_path}",
                )

        if not config_path or not os.path.exists(config_path):
            cfg_candidate = Path(str(model_path) + ".json")
            if cfg_candidate.exists():
                config_path = str(cfg_candidate)

        output_p = Path(output_wav).resolve()
        output_p.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            "-m",
            "piper",
            "-m",
            str(model_path),
            "-f",
            str(output_p),
            "-s",
            str(speaker),
        ]
        if config_path and os.path.exists(config_path):
            cmd.extend(["-c", str(config_path)])

        try:
            self._current_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = self._current_process.communicate(input=text, timeout=params.get("timeout_sec", 60))
            duration = time.time() - start_time

            if self._current_process.returncode != 0:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"piper execution failed (code {self._current_process.returncode}): {stderr[-500:]}",
                )

            if not output_p.exists():
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error="Piper completed with code 0 but output WAV was not created.",
                )

            # Validate generated WAV
            val_res = validate_audio(str(output_p))
            if not val_res.is_valid:
                self.state = ServiceState.READY
                return WorkerResponse(
                    status=ServiceState.READY,
                    job_id=request.job_id,
                    error=f"Generated audio failed validation: {val_res.errors}",
                )

            telemetry = WorkerTelemetry(
                worker_id=self.worker_id,
                backend="piper",
                state=ServiceState.READY,
                duration_sec=round(duration, 3),
            )

            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                artifacts=[
                    {
                        "path": str(output_p),
                        "kind": "AUDIO_WAV",
                        "duration_sec": val_res.duration_sec,
                        "sample_rate": val_res.sample_rate,
                        "channels": val_res.channels,
                        "producer": "piper",
                    }
                ],
                telemetry=telemetry,
            )

        except Exception as e:
            self.state = ServiceState.DEGRADED
            return WorkerResponse(
                status=ServiceState.DEGRADED,
                job_id=request.job_id,
                error=f"Piper worker exception: {e}",
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
