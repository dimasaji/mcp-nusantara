"""Audit trail append-only dengan hash chain (tamper-evident)."""
from __future__ import annotations

import hashlib
import json
import threading
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.observability.logging import redact

_GENESIS = "0" * 64


@contextmanager
def _file_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + '.lock').open('a+b') as lock:
        lock.seek(0, 2)
        if not lock.tell():
            lock.write(b'0'); lock.flush()
        lock.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == 'nt':
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


class AuditTrail:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else None
        self._lock = threading.Lock()
        self._entries: list[dict[str, Any]] = []
        if self.path and self.path.exists():
            self._entries = [json.loads(x) for x in self.path.read_text("utf-8").splitlines() if x.strip()]

    @staticmethod
    def _digest(entry: dict[str, Any]) -> str:
        body = {k: v for k, v in entry.items() if k != "hash"}
        return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()

    def record(self, event: str, **fields: Any) -> dict[str, Any]:
        if self.path:
            with self._lock, _file_lock(self.path):
                self._entries = ([json.loads(x) for x in self.path.read_text('utf-8').splitlines() if x.strip()]
                                 if self.path.exists() else [])
                if not self._valid(self._entries):
                    raise ValueError('audit integrity failure; append refused')
                return self._append(event, fields)
        with self._lock:
            return self._append(event, fields)

    def _append(self, event, fields):
        prev = self._entries[-1]['hash'] if self._entries else _GENESIS
        entry = {'seq': len(self._entries) + 1, 'ts': datetime.now(timezone.utc).isoformat(),
                 'event': event, 'data': redact(fields), 'prev': prev}
        entry['hash'] = self._digest(entry)
        if self.path:
            with self.path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(entry, sort_keys=True, default=str) + '\n')
                f.flush()
                os.fsync(f.fileno())
        self._entries.append(entry)
        return entry

    def entries(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)

    def verify(self) -> bool:
        return self._valid(self.entries())

    @classmethod
    def _valid(cls, entries):
        prev = _GENESIS
        for i, e in enumerate(entries, 1):
            if e['seq'] != i or e["prev"] != prev or e["hash"] != cls._digest(e):
                return False
            prev = e["hash"]
        return True
