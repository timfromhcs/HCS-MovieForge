"""Whisper.cpp integration worker for speech-to-text and voice command transcription."""

import json
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


class WhisperWorker(BaseWorker):
    def __init__(self, binary_path: Path | str = "bin/whisper-cpp/whisper-cli.exe", models_dir: Path | str = "models"):
        super().__init__(worker_id="worker_whisper", backend_name="whisper.cpp", backend_version="b5130")
        self.binary_path = Path(binary_path).resolve()
        self.models_dir = Path(models_dir).resolve()
        self._current_process: subprocess.Popen | None = None

    def health(self) -> dict[str, Any]:
        if not self.binary_path.exists():
            return {"status": "error", "message": f"Whisper binary not found at {self.binary_path}"}
        try:
            res = subprocess.run([str(self.binary_path), "--version"], capture_output=True, text=True, timeout=5)
            return {"status": "ok", "binary": str(self.binary_path)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def capabilities(self) -> WorkerCapabilities:
        return WorkerCapabilities(
            worker_id=self.worker_id,
            backend_name="whisper.cpp",
            backend_version=self.backend_version,
            supported_tasks=["stt.transcribe", "stt.voice_command"],
            compute_device="cpu",
            is_heavy_gpu=False,
            vulkan_capable=False,
            cpu_capable=True,
        )

    def estimate(self, request: WorkerRequest) -> dict[str, Any]:
        return {"estimated_ram_mb": 512, "estimated_vram_mb": 0, "estimated_duration_sec": 3.0}

    def prepare(self, request: WorkerRequest) -> None:
        pass

    def run(self, request: WorkerRequest) -> WorkerResponse:
        self.state = ServiceState.BUSY
        self.current_job_id = request.job_id
        start_time = time.time()

        params = request.parameters
        audio_file = params.get("audio_file")
        model_file = params.get("model_file")

        if not audio_file or not os.path.exists(audio_file):
            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                error=f"Audio file does not exist: {audio_file}",
            )

        if not model_file or not os.path.exists(model_file):
            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                error=f"Whisper model file does not exist: {model_file}",
            )

        output_json_base = audio_file + "_whisper_out"
        cmd = [
            str(self.binary_path),
            "-m", str(model_file),
            "-f", str(audio_file),
            "-oj",
            "-of", output_json_base,
            "-nt",
        ]

        try:
            self._current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = self._current_process.communicate(timeout=60)
            duration = time.time() - start_time

            json_file = Path(output_json_base + ".json")
            transcript_text = ""
            if json_file.exists():
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    transcript_text = data.get("transcription", [{}])[0].get("text", "").strip()
                json_file.unlink()

            telemetry = WorkerTelemetry(
                worker_id=self.worker_id,
                backend="whisper.cpp",
                state=ServiceState.READY,
                duration_sec=round(duration, 3),
            )

            self.state = ServiceState.READY
            return WorkerResponse(
                status=ServiceState.READY,
                job_id=request.job_id,
                artifacts=[{"text": transcript_text, "producer": "whisper.cpp"}],
                telemetry=telemetry,
            )

        except Exception as e:
            self.state = ServiceState.DEGRADED
            return WorkerResponse(
                status=ServiceState.DEGRADED,
                job_id=request.job_id,
                error=f"Whisper worker exception: {e}",
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
