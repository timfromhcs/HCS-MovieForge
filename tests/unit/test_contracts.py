"""Unit tests for core contracts and state schemas."""

import pytest
from packages.contracts.src.artifact import ArtifactKind, ArtifactRecord, QAStatus
from packages.contracts.src.hardware import HardwareProfile, SystemMemoryInfo, VulkanDeviceInfo
from packages.contracts.src.job import (
    JobPriority,
    JobRecord,
    JobStatus,
    ResourceEstimate,
    StructuredError,
)
from packages.contracts.src.worker import ServiceState, WorkerCapabilities, WorkerTelemetry


def test_job_record_creation():
    job = JobRecord(
        job_id="job_test123",
        project_id="proj_1",
        type="image.generate",
        status=JobStatus.QUEUED,
        priority=JobPriority.HIGH,
        resource_estimate=ResourceEstimate(
            estimated_ram_mb=4096,
            estimated_vram_mb=6144,
            requires_heavy_gpu=True,
        ),
    )
    assert job.job_id == "job_test123"
    assert job.status == JobStatus.QUEUED
    assert job.priority == JobPriority.HIGH
    assert job.resource_estimate.requires_heavy_gpu is True


def test_artifact_record_immutable_fields():
    art = ArtifactRecord(
        artifact_id="art_1",
        project_id="proj_1",
        kind=ArtifactKind.IMAGE,
        path="/path/to/img.png",
        relative_path="renders/img.png",
        size=1024,
        sha256="abc123def456",
        mime="image/png",
        producer="bonsai_worker",
    )
    assert art.artifact_id == "art_1"
    assert art.qa_status == QAStatus.UNINSPECTED
    assert art.canonical is False


def test_hardware_profile_budgets():
    profile = HardwareProfile(
        system_memory=SystemMemoryInfo(total_ram_mb=16384, available_ram_mb=8192),
        vulkan_device=VulkanDeviceInfo(device_name="AMD Radeon Graphics", api_version="1.4"),
        is_uma=True,
    )
    assert profile.is_uma is True
    assert profile.max_heavy_gpu_jobs == 1
