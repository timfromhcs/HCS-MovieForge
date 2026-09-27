"""Worker contracts, service states, and execution protocol for HCS MovieForge."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ServiceState(StrEnum):
    STARTING = "STARTING"
    READY = "READY"
    BUSY = "BUSY"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    CRASHED = "CRASHED"
    RECOVERING = "RECOVERING"
    DISABLED = "DISABLED"


class WorkerTelemetry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    job_id: str | None = None
    worker_id: str
    model_id: str | None = None
    backend: str
    state: ServiceState
    duration_sec: float = 0.0
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_peak_mb: float = 0.0
    gpu_used_mb: float = 0.0
    gpu_peak_mb: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    artifact_id: str | None = None
    error_class: str | None = None


class WorkerCapabilities(BaseModel):
    worker_id: str
    backend_name: str
    backend_version: str
    supported_tasks: list[str] = Field(default_factory=list)
    compute_device: str = "vulkan"
    is_heavy_gpu: bool = False
    vulkan_capable: bool = True
    cpu_capable: bool = True


class WorkerRequest(BaseModel):
    job_id: str
    project_id: str
    task_type: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    input_artifacts: list[str] = Field(default_factory=list)
    priority: int = 20


class WorkerResponse(BaseModel):
    status: ServiceState
    job_id: str
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    telemetry: WorkerTelemetry | None = None
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
