"""Timeout untuk fungsi sync dan coroutine."""
from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")


class OperationTimeout(TimeoutError):
    pass


def run_with_timeout(fn: Callable[..., T], timeout_s: float, *args: Any, **kwargs: Any) -> T:
    """Jalankan fungsi sync dengan batas waktu.

    CATATAN: thread Python tidak bisa dibunuh paksa. Pemanggil kembali tepat waktu,
    tetapi fungsi yang macet dapat terus berjalan di background. Untuk pekerjaan
    berisiko gunakan proses terpisah (lihat docs/v2/ROADMAP_STATUS.md).
    """
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(fn, *args, **kwargs)
    try:
        return fut.result(timeout=timeout_s)
    except concurrent.futures.TimeoutError as exc:
        raise OperationTimeout(f"melebihi {timeout_s}s") from exc
    finally:
        ex.shutdown(wait=False, cancel_futures=True)


async def await_with_timeout(aw: Awaitable[T], timeout_s: float) -> T:
    try:
        return await asyncio.wait_for(aw, timeout=timeout_s)
    except asyncio.TimeoutError as exc:
        raise OperationTimeout(f"melebihi {timeout_s}s") from exc
