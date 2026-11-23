"""Circuit breaker thread-safe: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
from __future__ import annotations

import threading
import time
from collections.abc import Callable


class CircuitOpen(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout_s: float = 30.0,
                 clock: Callable[[], float] = time.monotonic):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout_s = reset_timeout_s
        self._clock = clock
        self._lock = threading.Lock()
        self._failures = 0
        self._opened_at: float | None = None
        self._probe_in_flight = False

    @property
    def state(self) -> str:
        with self._lock:
            return self._state_locked()

    def _state_locked(self) -> str:
        if self._opened_at is None:
            return "closed"
        if self._clock() - self._opened_at >= self.reset_timeout_s:
            return "half_open"
        return "open"

    def allow(self) -> bool:
        with self._lock:
            s = self._state_locked()
            if s == "closed":
                return True
            if s == "half_open" and not self._probe_in_flight:
                self._probe_in_flight = True  # hanya satu probe
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None
            self._probe_in_flight = False

    def record_failure(self) -> None:
        with self._lock:
            self._probe_in_flight = False
            self._failures += 1
            if self._failures >= self.failure_threshold or self._opened_at is not None:
                self._opened_at = self._clock()
