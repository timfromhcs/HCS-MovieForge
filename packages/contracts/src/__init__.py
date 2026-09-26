"""Contracts package for HCS MovieForge."""

from packages.contracts.src.artifact import ArtifactKind, ArtifactRecord, QAStatus
from packages.contracts.src.hardware import (
    HardwareProfile,
    StorageInfo,
    SystemMemoryInfo,
    VulkanDeviceInfo,
)
from packages.contracts.src.job import (
    JobPriority,
    JobRecord,
    JobStatus,
    ResourceEstimate,
    StructuredError,
)
from packages.contracts.src.worker import (
    ServiceState,
    WorkerCapabilities,
    WorkerRequest,
    WorkerResponse,
    WorkerTelemetry,
)

__all__ = [
    "ArtifactKind",
    "ArtifactRecord",
    "QAStatus",
    "JobPriority",
    "JobRecord",
    "JobStatus",
    "ResourceEstimate",
    "StructuredError",
    "ServiceState",
    "WorkerCapabilities",
    "WorkerRequest",
    "WorkerResponse",
    "WorkerTelemetry",
    "HardwareProfile",
    "StorageInfo",
    "SystemMemoryInfo",
    "VulkanDeviceInfo",
]
