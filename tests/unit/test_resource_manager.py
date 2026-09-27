"""Unit tests for ResourceManager UMA budgeting and heavy-GPU lease arbitration."""

from engine.resource_manager.manager import ResourceManager


def test_profile_budgets_sane(tmp_path):
    mgr = ResourceManager(runtime_dir=tmp_path / "runtime")
    assert mgr.profile.system_memory.total_ram_mb > 0
    assert mgr.profile.os_safety_reserve_mb >= 2048
    assert mgr.profile.blender_reserve_mb >= 1024
    assert mgr.profile.max_heavy_gpu_jobs == 1


def test_save_and_load_profile(tmp_path):
    mgr = ResourceManager(runtime_dir=tmp_path / "runtime")
    saved = mgr.save_profile()
    assert saved.exists()
    loaded = mgr.load_profile()
    assert loaded is not None
    assert loaded["max_heavy_gpu_jobs"] == 1


def test_heavy_lease_acquire_release(tmp_path):
    mgr = ResourceManager(runtime_dir=tmp_path / "runtime")
    ok, _ = mgr.acquire_heavy_lease("job_a", estimate_ram_mb=64)
    assert ok
    assert mgr.active_heavy_count() == 1
    ok2, _ = mgr.acquire_heavy_lease("job_b", estimate_ram_mb=64)
    assert not ok2
    assert mgr.release_heavy_lease("job_a")
    assert mgr.active_heavy_count() == 0


def test_status_reports_live_ram(tmp_path):
    mgr = ResourceManager(runtime_dir=tmp_path / "runtime")
    status = mgr.status()
    assert status["available_ram_mb"] > 0
    assert status["total_ram_mb"] >= status["available_ram_mb"]
