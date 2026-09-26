"""Hardware and system probing for HCS MovieForge."""

import os
import platform
import shutil
import subprocess
from packages.contracts.src.hardware import (
    HardwareProfile,
    StorageInfo,
    SystemMemoryInfo,
    VulkanDeviceInfo,
)
import psutil


def probe_vulkan() -> VulkanDeviceInfo:
    """Probes Vulkan device info using vulkaninfo."""
    device = VulkanDeviceInfo()
    try:
        # Run vulkaninfo --summary
        res = subprocess.run(
            ["vulkaninfo", "--summary"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = res.stdout
        for line in output.splitlines():
            line = line.strip()
            if "deviceName" in line and "=" in line:
                device.device_name = line.split("=", 1)[1].strip()
            elif "driverInfo" in line and "=" in line:
                device.driver_version = line.split("=", 1)[1].strip()
            elif "driverName" in line and "=" in line:
                device.driver_name = line.split("=", 1)[1].strip()
            elif "deviceType" in line and "=" in line:
                device.device_type = line.split("=", 1)[1].strip()
            elif "apiVersion" in line and "=" in line:
                device.api_version = line.split("=", 1)[1].strip()
    except Exception:
        # Fallback to defaults if vulkaninfo is unavailable
        device.device_name = "Vulkan Device"
    return device


def probe_hardware(target_path: str = ".") -> HardwareProfile:
    """Collects real system hardware telemetry, memory, storage, and safe budgets."""
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    cpu_freq = psutil.cpu_freq()

    sys_mem = SystemMemoryInfo(
        total_ram_mb=int(vm.total / (1024 * 1024)),
        available_ram_mb=int(vm.available / (1024 * 1024)),
        used_ram_mb=int(vm.used / (1024 * 1024)),
        swap_total_mb=int(swap.total / (1024 * 1024)),
        swap_free_mb=int(swap.free / (1024 * 1024)),
    )

    usage = shutil.disk_usage(target_path)
    storage = StorageInfo(
        path=os.path.abspath(target_path),
        total_gb=round(usage.total / (1024**3), 2),
        free_gb=round(usage.free / (1024**3), 2),
        is_hdd=True,
    )

    vulkan = probe_vulkan()

    # Calculate safe UMA budgets:
    # Reserve 3.5GB for OS/system, 2GB for Blender, and allocate remaining to models
    total_mb = sys_mem.total_ram_mb
    os_reserve = 3584
    blender_reserve = 2048
    safe_model_budget = max(2048, total_mb - os_reserve - blender_reserve)

    return HardwareProfile(
        os_name=platform.system(),
        os_version=platform.version(),
        cpu_name=platform.processor() or "AMD Ryzen",
        cpu_cores=psutil.cpu_count(logical=False) or 8,
        cpu_threads=psutil.cpu_count(logical=True) or 16,
        system_memory=sys_mem,
        vulkan_device=vulkan,
        storage=storage,
        is_uma=True,
        os_safety_reserve_mb=os_reserve,
        blender_reserve_mb=blender_reserve,
        model_budget_mb=safe_model_budget,
        max_heavy_gpu_jobs=1,
    )
