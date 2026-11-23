"""Retry dengan exponential backoff (sleep bisa diinjeksi untuk tes)."""
from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")


def retry(fn: Callable[..., T], *args: Any, attempts: int = 3, base_delay: float = 0.2,
          max_delay: float = 5.0, retry_on: tuple[type[BaseException], ...] = (Exception,),
          sleep: Callable[[float], None] = time.sleep, **kwargs: Any) -> T:
    if attempts < 1:
        raise ValueError("attempts minimal 1")
    for i in range(attempts):
        try:
            return fn(*args, **kwargs)
        except retry_on:
            if i == attempts - 1:
                raise
            sleep(min(max_delay, base_delay * (2 ** i)))
    raise AssertionError("unreachable")


async def aretry(fn: Callable[..., Awaitable[T]], *args: Any, attempts: int = 3,
                 base_delay: float = 0.2, max_delay: float = 5.0,
                 retry_on: tuple[type[BaseException], ...] = (Exception,),
                 sleep: Callable[[float], Awaitable[None]] = asyncio.sleep, **kwargs: Any) -> T:
    if attempts < 1:
        raise ValueError("attempts minimal 1")
    for i in range(attempts):
        try:
            return await fn(*args, **kwargs)
        except asyncio.CancelledError:
            raise
        except retry_on:
            if i == attempts - 1:
                raise
            await sleep(min(max_delay, base_delay * (2 ** i)))
    raise AssertionError("unreachable")
