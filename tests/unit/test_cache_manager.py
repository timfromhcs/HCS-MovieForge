"""Unit tests for CacheManager bounded LRU eviction and orphan cleanup."""

from engine.cache_manager.manager import CacheManager


def test_put_get_roundtrip(tmp_path):
    mgr = CacheManager(cache_dir=tmp_path / "cache", size_limit_mb=64)
    src = tmp_path / "blob.bin"
    src.write_bytes(b"x" * 1024)
    dest = mgr.put("blob.bin", src)
    assert dest.exists()
    assert mgr.get("blob.bin") == dest
    assert mgr.get("missing.bin") is None


def test_lru_eviction_respects_pin(tmp_path):
    mgr = CacheManager(cache_dir=tmp_path / "cache", size_limit_mb=64)
    payload = b"y" * (1024 * 1024)
    for name in ("a.bin", "b.bin"):
        src = tmp_path / name
        src.write_bytes(payload)
        mgr.put(name, src)
    mgr.pin("a.bin")
    # Shrink limit below current 2MB so eviction must drop b.bin but keep pinned a.bin
    mgr.size_limit_mb = 1
    evicted = mgr.enforce_limit()
    assert "b.bin" in evicted
    assert mgr.get("a.bin") is not None


def test_cleanup_orphans(tmp_path):
    mgr = CacheManager(cache_dir=tmp_path / "cache", size_limit_mb=64)
    src = tmp_path / "keep.bin"
    src.write_bytes(b"z" * 512)
    mgr.put("keep.bin", src)
    stray = tmp_path / "cache" / "stray.bin"
    stray.write_bytes(b"q" * 512)
    removed = mgr.cleanup_orphans({"keep.bin"})
    assert "stray.bin" in removed
    assert mgr.get("keep.bin") is not None


def test_size_mb_measures_disk(tmp_path):
    mgr = CacheManager(cache_dir=tmp_path / "cache", size_limit_mb=64)
    assert mgr.size_mb() == 0.0
    src = tmp_path / "one.bin"
    src.write_bytes(b"w" * (1024 * 1024))
    mgr.put("one.bin", src)
    assert mgr.size_mb() >= 0.9
