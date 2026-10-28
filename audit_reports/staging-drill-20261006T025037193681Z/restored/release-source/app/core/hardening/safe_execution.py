"""safe_call: kegagalan satu komponen tidak menjatuhkan seluruh sistem."""
from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass
from typing import Any, Callable

from app.core.hardening.circuit_breaker import CircuitBreaker
from app.core.hardening.timeout import OperationTimeout, await_with_timeout, run_with_timeout


@dataclass
class SafeResult:
    ok: bool
    value: Any = None
    error: str | None = None
    error_type: str | None = None
    duration_ms: float = 0.0
    skipped_by_breaker: bool = False


def _fail(exc: BaseException, t0: float, **kw: Any) -> SafeResult:
    return SafeResult(False, None, str(exc)[:500], type(exc).__name__,
                      (time.perf_counter() - t0) * 1000, **kw)


def safe_call(fn: Callable[..., Any], *args: Any, timeout_s: float | None = None,
              breaker: CircuitBreaker | None = None, **kwargs: Any) -> SafeResult:
    """Panggil fungsi sync; tidak pernah melempar Exception (BaseException tetap lewat)."""
    t0 = time.perf_counter()
    if breaker and not breaker.allow():
        return SafeResult(False, None, f"circuit '{breaker.name}' terbuka", "CircuitOpen",
                          0.0, skipped_by_breaker=True)
    try:
        value = run_with_timeout(fn, timeout_s, *args, **kwargs) if timeout_s else fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - batas isolasi kegagalan disengaja
        if breaker:
            breaker.record_failure()
        return _fail(exc, t0)
    if breaker:
        breaker.record_success()
    return SafeResult(True, value, None, None, (time.perf_counter() - t0) * 1000)


async def safe_acall(fn: Callable[..., Any], *args: Any, timeout_s: float | None = None,
                     breaker: CircuitBreaker | None = None, **kwargs: Any) -> SafeResult:
    """Versi async; menerima fungsi sync maupun async."""
    t0 = time.perf_counter()
    if breaker and not breaker.allow():
        return SafeResult(False, None, f"circuit '{breaker.name}' terbuka", "CircuitOpen",
                          0.0, skipped_by_breaker=True)
    try:
        is_async_fn = (
            inspect.iscoroutinefunction(fn)
            or inspect.iscoroutinefunction(getattr(fn, "__call__", None))
        )

        if timeout_s is not None and not is_async_fn:
            async def _run_sync() -> Any:
                value = await asyncio.to_thread(fn, *args, **kwargs)
                if inspect.isawaitable(value):
                    return await value
                return value

            res = await await_with_timeout(_run_sync(), timeout_s)
        else:
            res = fn(*args, **kwargs)
            if inspect.isawaitable(res):
                res = await (
                    await_with_timeout(res, timeout_s)
                    if timeout_s is not None
                    else res
                )
    except OperationTimeout as exc:
        if breaker:
            breaker.record_failure()
        return _fail(exc, t0)
    except Exception as exc:  # noqa: BLE001
        if breaker:
            breaker.record_failure()
        return _fail(exc, t0)
    if breaker:
        breaker.record_success()
    return SafeResult(True, res, None, None, (time.perf_counter() - t0) * 1000)
