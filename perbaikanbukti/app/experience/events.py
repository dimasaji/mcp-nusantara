"""Phase 10 - telemetry event (skema berversi). Tidak pernah melempar exception ke core engine."""
from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.observability.context import current_ids, new_id
from app.observability.logging import redact

SCHEMA_VERSION = "1.0"
EVENT_TYPES = frozenset({
    "request_started", "request_completed", "model_called", "memory_read", "memory_written",
    "rag_retrieval", "tool_called", "tool_failed", "response_generated", "feedback_received",
    "stage_failed",
    "stage_completed",
})


@dataclass
class Event:
    event_id: str
    event_type: str
    timestamp: str
    session_id: str
    request_id: str
    component: str
    status: str
    latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION


def _trim(v: Any, n: int = 200) -> Any:
    if isinstance(v, str):
        return v[:n]
    if isinstance(v, dict):
        return {k: _trim(x, n) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_trim(x, n) for x in v[:20]]
    return v


class EventRecorder:
    def __init__(self, path: Path | None = None, max_memory: int = 5000,
                 max_file_bytes: int = 10_000_000, backup_count: int = 3):
        self.path = Path(path) if path else None
        self.max_memory = max_memory
        self.dropped = 0
        self._lock = threading.Lock()
        self._events: list[Event] = []
        if max_file_bytes < 1 or backup_count < 1:
            raise ValueError("invalid telemetry retention limits")
        self.max_file_bytes, self.backup_count = max_file_bytes, backup_count

    def _rotate(self, incoming_bytes: int) -> None:
        if not self.path.exists() or self.path.stat().st_size + incoming_bytes <= self.max_file_bytes:
            return
        oldest = self.path.with_name(self.path.name + f".{self.backup_count}")
        oldest.unlink(missing_ok=True)
        for index in range(self.backup_count - 1, 0, -1):
            source = self.path.with_name(self.path.name + f".{index}")
            if source.exists():
                source.replace(self.path.with_name(self.path.name + f".{index + 1}"))
        self.path.replace(self.path.with_name(self.path.name + ".1"))

    def emit(self, event_type: str, component: str, status: str = "ok", latency_ms: float = 0.0,
             metadata: dict[str, Any] | None = None) -> Event | None:
        try:
            if event_type not in EVENT_TYPES:
                raise ValueError("event_type tidak dikenal")
            ids = current_ids()
            ev = Event(new_id("evt"), event_type, datetime.now(timezone.utc).isoformat(),
                       ids["session_id"], ids["request_id"], component, status,
                       round(float(latency_ms), 2), _trim(redact(metadata or {})))
            with self._lock:
                self._events.append(ev)
                if len(self._events) > self.max_memory:
                    del self._events[: len(self._events) - self.max_memory]
                if self.path:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    line = json.dumps(asdict(ev), ensure_ascii=False, default=str) + "\n"
                    self._rotate(len(line.encode("utf-8")))
                    with self.path.open("a", encoding="utf-8") as f:
                        f.write(line)
            return ev
        except Exception:  # noqa: BLE001 - telemetry tidak boleh mengubah perilaku core
            self.dropped += 1
            return None

    def events(self) -> list[Event]:
        with self._lock:
            return list(self._events)

    @staticmethod
    def load(path: Path) -> list[dict[str, Any]]:
        p = Path(path)
        if not p.exists():
            return []
        out = []
        for line in p.read_text("utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out
