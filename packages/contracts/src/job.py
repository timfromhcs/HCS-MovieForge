"""Job contracts and state models for HCS MovieForge."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    WAITING_RESOURCE = "WAITING_RESOURCE"
    PREPARING = "PREPARING"
    PRELOADING = "PRELOADING"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    COMMITTING = "COMMITTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    ORPHANED = "ORPHANED"
    RECOVERING = "RECOVERING"


class JobPriority(int, Enum):
    LOW = 10
    NORMAL = 20
    HIGH = 30
    URGENT = 40


class ResourceEstimate(BaseModel):
    estimated_ram_mb: int = Field(default=2048, description="Estimated system RAM in MB")
    estimated_vram_mb: int = Field(default=4096, description="Estimated GPU/VRAM in MB")
    estimated_duration_sec: float = Field(default=30.0, description="Estimated duration in seconds")
    requires_heavy_gpu: bool = Field(default=False, description="Whether this job counts as heavy GPU job")


class StructuredError(BaseModel):
    error_class: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    recoverable: bool = False


class JobRecord(BaseModel):
    job_id: str
    project_id: str
    type: str
    status: JobStatus = JobStatus.CREATED
    model_id: str | None = None
    model_revision: str | None = None
    input_artifact_ids: list[str] = Field(default_factory=list)
    input_hashes: dict[str, str] = Field(default_factory=dict)
    recipe_fingerprint: str | None = None
    priority: JobPriority = JobPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 2
    resource_estimate: ResourceEstimate = Field(default_factory=ResourceEstimate)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    parent_job: str | None = None
    child_jobs: list[str] = Field(default_factory=list)
    worker_id: str | None = None
    output_artifact_ids: list[str] = Field(default_factory=list)
    error: StructuredError | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
