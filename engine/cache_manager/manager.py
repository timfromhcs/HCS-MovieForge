"""Bounded LRU cache manager guarding the HDD-backed model/artifact staging area."""

import json
import shutil
import time
from pathlib import Path
from typing import Any


class CacheManager:
    def __init__(self, cache_dir: Path | str = "cache", size_limit_mb: int = 8192) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir = self.cache_dir / "tmp"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.size_limit_mb = size_limit_mb
        self.index_path = self.cache_dir / "index.json"
        self.pinned: set[str] = set()

    def _load_index(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"entries": {}}
        try:
            with open(self.index_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"entries": {}}

    def _save_index(self, data: dict[str, Any]) -> None:
        tmp = self.index_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(self.index_path)

    def size_bytes(self) -> int:
        """Measures real cache size on disk in bytes."""
        total = 0
        for p in self.cache_dir.rglob("*"):
            try:
                if p.is_file() and p.name not in ("index.json", "index.tmp"):
                    total += p.stat().st_size
            except OSError:
                continue
        return total

    def size_mb(self) -> float:
        """Measures real cache size on disk in MB."""
        return round(self.size_bytes() / (1024 * 1024), 2)

    def put(self, key: str, src: Path | str) -> Path:
        """Copies a file into the cache under key, enforcing the size limit first."""
        src_path = Path(src)
        if not src_path.is_file():
            raise FileNotFoundError(f"cache source missing: {src_path}")
        needed_mb = src_path.stat().st_size / (1024 * 1024)
        self.enforce_limit(needed_mb)
        dest = self.cache_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest)
        data = self._load_index()
        data["entries"][key] = {"size_mb": needed_mb, "last_access": time.time(), "pinned": key in self.pinned}
        self._save_index(data)
        return dest

    def get(self, key: str) -> Path | None:
        """Resolves a cached key, refreshing LRU timestamp, or None when absent."""
        dest = self.cache_dir / key
        if not dest.is_file():
            return None
        data = self._load_index()
        if key in data["entries"]:
            data["entries"][key]["last_access"] = time.time()
            self._save_index(data)
        return dest

    def pin(self, key: str) -> None:
        """Protects a key from LRU eviction while a job needs it."""
        self.pinned.add(key)

    def unpin(self, key: str) -> None:
        """Removes eviction protection from a key."""
        self.pinned.discard(key)

    def enforce_limit(self, incoming_mb: float = 0.0) -> list[str]:
        """Evicts oldest unpinned entries until size fits the limit. Returns evicted keys."""
        evicted: list[str] = []
        limit_bytes = self.size_limit_mb * 1024 * 1024
        incoming_bytes = int(incoming_mb * 1024 * 1024)
        while self.size_bytes() + incoming_bytes > limit_bytes:
            data = self._load_index()
            entries = data.get("entries", {})
            candidates = sorted(
                ((k, v) for k, v in entries.items() if k not in self.pinned),
                key=lambda kv: kv[1].get("last_access", 0),
            )
            if not candidates:
                break
            oldest = candidates[0][0]
            target = self.cache_dir / oldest
            try:
                if target.is_file():
                    target.unlink()
                else:
                    shutil.rmtree(target, ignore_errors=True)
            except OSError:
                break
            del entries[oldest]
            self._save_index(data)
            evicted.append(oldest)
        return evicted

    def cleanup_orphans(self, valid_keys: set[str]) -> list[str]:
        """Deletes cached top-level entries not in valid_keys and not pinned."""
        removed: list[str] = []
        for child in self.cache_dir.iterdir():
            if child.name in ("tmp", "index.json"):
                continue
            if child.name not in valid_keys and child.name not in self.pinned:
                try:
                    if child.is_file():
                        child.unlink()
                    else:
                        shutil.rmtree(child, ignore_errors=True)
                    removed.append(child.name)
                except OSError:
                    continue
        data = self._load_index()
        for key in removed:
            data["entries"].pop(key, None)
        self._save_index(data)
        return removed
