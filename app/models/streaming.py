"""Request-scoped observation of real provider chunks, shared by the V1 transport."""
from contextvars import ContextVar
from typing import Awaitable, Callable

stream_observer: ContextVar[Callable[[dict], Awaitable[None]] | None] = ContextVar('v1_stream_observer', default=None)
