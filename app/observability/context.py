"""Correlation ID via contextvars: request_id, session_id, execution_id."""
from __future__ import annotations

import contextvars
import uuid
from contextlib import contextmanager
from collections.abc import Iterator

_request_id = contextvars.ContextVar("request_id", default="-")
_session_id = contextvars.ContextVar("session_id", default="-")
_execution_id = contextvars.ContextVar("execution_id", default="-")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def current_ids() -> dict[str, str]:
    return {"request_id": _request_id.get(), "session_id": _session_id.get(),
            "execution_id": _execution_id.get()}


@contextmanager
def request_context(request_id: str | None = None, session_id: str = "-") -> Iterator[dict[str, str]]:
    inherited = _request_id.get()
    toks = (
        _request_id.set(request_id or (inherited if inherited != "-" else new_id("req"))),
        _session_id.set(session_id),
        _execution_id.set(new_id("exe")),
    )
    try:
        yield current_ids()
    finally:
        _request_id.reset(toks[0])
        _session_id.reset(toks[1])
        _execution_id.reset(toks[2])
