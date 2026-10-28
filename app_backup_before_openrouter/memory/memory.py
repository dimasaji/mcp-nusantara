"""
Memory Engine - Short-term dan Long-term memory.
"""
from __future__ import annotations

import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryStore:
    """
    Memory store sederhana dengan TTL dan namespace.
    """

    def __init__(self, namespace: str = "default", data_dir: Optional[Path] = None):
        self.namespace = namespace
        self.data_dir = data_dir or Path.home() / ".nusantara" / "memory"
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}

    def save(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Simpan item ke memori."""
        self._memory[key] = value
        if ttl_seconds:
            self._timestamps[key] = time.time() + ttl_seconds
        else:
            self._timestamps.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        """Ambil item dari memori."""
        if key not in self._memory:
            return None

        if self._is_expired(key):
            self.delete(key)
            return None

        return self._memory[key]

    def _is_expired(self, key: str) -> bool:
        """Cek apakah item kedaluwarsa."""
        if key not in self._timestamps:
            return False
        return time.time() > self._timestamps[key]

    def delete(self, key: str) -> bool:
        """Hapus item dari memori."""
        if key in self._memory:
            del self._memory[key]
            if key in self._timestamps:
                del self._timestamps[key]
            return True
        return False

    def clear_session(self, session_id: str) -> int:
        """Hapus semua item dalam sesi tertentu."""
        keys_to_delete = [k for k in self._memory if k.startswith(f"session:{session_id}:")]
        for key in keys_to_delete:
            self.delete(key)
        return len(keys_to_delete)

    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Dapatkan metadata item."""
        if key in self._memory:
            val = self._memory[key]
            if isinstance(val, dict) and "_metadata" in val:
                return val["_metadata"]
        return None

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List semua kunci, opsional dengan prefix."""
        if prefix:
            return [k for k in self._memory if k.startswith(prefix)]
        return list(self._memory.keys())

    def clear_expired(self) -> int:
        """Hapus semua item yang sudah kedaluwarsa."""
        expired = [k for k in self._memory if self._is_expired(k)]
        for key in expired:
            self.delete(key)
        return len(expired)

    def clear_all(self) -> int:
        """Hapus semua item."""
        count = len(self._memory)
        self._memory.clear()
        self._timestamps.clear()
        return count


class LongTermMemory:
    """
    Long-term memory: item yang persist di filesystem.
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path.home() / ".nusantara" / "long_term_memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Simpan ke long-term memory."""
        item = {
            "key": key,
            "value": value,
            "saved_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        path = self.data_dir / f"{key}.pkl"
        with open(path, "wb") as f:
            pickle.dump(item, f)

    def get(self, key: str) -> Optional[Any]:
        """Ambil dari long-term memory."""
        path = self.data_dir / f"{key}.pkl"
        if not path.exists():
            return None
        with open(path, "rb") as f:
            item = pickle.load(f)
        return item.get("value")

    def delete(self, key: str) -> bool:
        """Hapus dari long-term memory."""
        path = self.data_dir / f"{key}.pkl"
        if path.exists():
            path.unlink()
            return True
        return False

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List semua kunci long-term memory."""
        keys = []
        for p in self.data_dir.glob("*.pkl"):
            key = p.stem
            if prefix is None or key.startswith(prefix):
                keys.append(key)
        return keys

    def clear_all(self) -> int:
        """Hapus semua long-term memory."""
        count = 0
        for p in self.data_dir.glob("*.pkl"):
            p.unlink()
            count += 1
        return count


_default_memory = MemoryStore()
_default_long_term = LongTermMemory()


def create_memory_store(namespace: str = "default") -> MemoryStore:
    return MemoryStore(namespace=namespace)


def create_long_term_memory(data_dir: Path = None) -> LongTermMemory:
    return LongTermMemory(data_dir=data_dir)
