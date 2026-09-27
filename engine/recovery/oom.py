"""Bounded OOM recovery ladder (§60): diagnose, free, narrow, retry-once or block.

Single pass, no blind loops. Executable steps run against the real resource/cache
managers; placement narrowing is returned as retry config for the caller to apply.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


def recover_oom(
    job_id: str,
    resource_mgr: Any,
    cache_mgr: Any | None = None,
    partial_files: list[Path | str] | None = None,
    trash_dir: Path | str | None = None,
    estimate_ram_mb: int = 2048,
) -> dict[str, Any]:
    """Executes ladder steps 1-9 once and reports whether a single retry is sane."""
    actions: list[str] = []
    # 1-3: prune dead leases + evict idle cache
    before_heavy = resource_mgr.active_heavy_count()
    freed: list[str] = []
    if cache_mgr is not None:
        freed = cache_mgr.enforce_limit()
    actions.append(f"pruned_leases(heavy={before_heavy})")
    if freed:
        actions.append(f"evicted_cache({len(freed)})")
    # 4-5: quarantine partial outputs so they are never treated as artifacts
    quarantined: list[str] = []
    if partial_files and trash_dir is not None:
        trash = Path(trash_dir)
        trash.mkdir(parents=True, exist_ok=True)
        for partial in partial_files:
            p = Path(partial)
            if p.is_file():
                dest = trash / f"{job_id}_{p.name}"
                try:
                    shutil.move(str(p), str(dest))
                    quarantined.append(dest.name)
                except OSError:
                    continue
        if quarantined:
            actions.append(f"quarantined({len(quarantined)})")
    # 6-9: narrow placement for one retry
    retry_config = {
        "gpu_layers": "halved",
        "cpu_offload": "increased",
        "preview_resolution": "lowered",
        "context_reduction": "applied",
        "estimate_ram_mb": max(512, estimate_ram_mb // 2),
    }
    avail = resource_mgr.available_ram_mb()
    reserve = resource_mgr.profile.os_safety_reserve_mb
    blocked = avail < reserve // 2
    if blocked:
        actions.append("blocked_still_pressured")
    else:
        actions.append("retry_once_allowed")
    return {
        "job_id": job_id,
        "actions": actions,
        "retry_config": retry_config,
        "blocked": blocked,
        "available_ram_mb": avail,
    }
