"""Metrik in-process (counter + latency). Mengisi /v2/metrics; V1 /metrics tetap."""
from __future__ import annotations

import threading
import time
from collections import defaultdict


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._lat: dict[str, list[float]] = defaultdict(list)
        self.started_at = time.time()

    def incr(self, name: str, n: int = 1) -> None:
        with self._lock:
            self._counters[name] += n

    def observe(self, name: str, ms: float) -> None:
        with self._lock:
            buf = self._lat[name]
            buf.append(ms)
            if len(buf) > 1000:
                del buf[: len(buf) - 1000]

    def snapshot(self) -> dict:
        with self._lock:
            lat = {}
            for k, v in self._lat.items():
                s = sorted(v)
                lat[k] = {"count": len(s), "p50_ms": round(s[len(s) // 2], 2),
                          "p95_ms": round(s[min(len(s) - 1, int(len(s) * 0.95))], 2)}
            return {"uptime_s": round(time.time() - self.started_at, 1),
                    "counters": dict(self._counters), "latency": lat}


metrics = Metrics()
