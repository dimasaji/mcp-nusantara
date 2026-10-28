"""Audit trail append-only dengan hash chain (tamper-evident)."""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.observability.logging import redact

_GENESIS = "0" * 64


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
        with self._lock:
            prev = self._entries[-1]["hash"] if self._entries else _GENESIS
            entry = {"seq": len(self._entries) + 1, "ts": datetime.now(timezone.utc).isoformat(),
                     "event": event, "data": redact(fields), "prev": prev}
            entry["hash"] = self._digest(entry)
            self._entries.append(entry)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
            return entry

    def entries(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)

    def verify(self) -> bool:
        prev = _GENESIS
        for e in self.entries():
            if e["prev"] != prev or e["hash"] != self._digest(e):
                return False
            prev = e["hash"]
        return True
