"""Hardware contracts and resource budgeting models for HCS MovieForge."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class VulkanDeviceInfo(BaseModel):
    device_id: int = 0
    device_name: str = "Unknown"
    device_type: str = "INTEGRATED_GPU"
    driver_version: str = "Unknown"
    driver_name: str = "Unknown"
    api_version: str = "1.3"
    total_memory_mb: int = 0
    available_memory_mb: int = 0


class SystemMemoryInfo(BaseModel):
    total_ram_mb: int = 0
    available_ram_mb: int = 0
    used_ram_mb: int = 0
    swap_total_mb: int = 0
    swap_free_mb: int = 0


class StorageInfo(BaseModel):
    path: str
    filesystem: str = "NTFS"
    total_gb: float = 0.0
    free_gb: float = 0.0
    is_hdd: bool = True


class HardwareProfile(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    os_name: str = "Windows"
    os_version: str = "11 Pro"
    cpu_name: str = "AMD Ryzen"
    cpu_cores: int = 8
    cpu_threads: int = 16
    system_memory: SystemMemoryInfo = Field(default_factory=SystemMemoryInfo)
    vulkan_device: VulkanDeviceInfo = Field(default_factory=VulkanDeviceInfo)
    storage: StorageInfo = Field(default_factory=lambda: StorageInfo(path="."))
    is_uma: bool = True

    # Derived safe operational budgets in MB
    os_safety_reserve_mb: int = 3072  # Keep 3GB for Windows
    blender_reserve_mb: int = 2048  # Keep 2GB for Blender
    model_budget_mb: int = 6144  # Available budget for active models
    max_heavy_gpu_jobs: int = 1  # Enforce max 1 heavy GPU job concurrently
