import asyncio
import time
from contextvars import ContextVar

import pytest

from app.core.hardening.circuit_breaker import CircuitBreaker
from app.core.hardening.safe_execution import safe_acall


def test_sync_timeout():
    def blocking():
        time.sleep(0.20)
        return "done"

    result = asyncio.run(safe_acall(blocking, timeout_s=0.05))

    assert result.ok is False
    assert result.error_type == "OperationTimeout"


def test_sync_timeout_does_not_block_event_loop():
    async def scenario():
        ticked = asyncio.Event()

        async def ticker():
            await asyncio.sleep(0.02)
            ticked.set()

        def blocking():
            time.sleep(0.20)

        task = asyncio.create_task(ticker())
        result = await safe_acall(blocking, timeout_s=0.05)

        await task
        return result, ticked.is_set()

    result, ticked = asyncio.run(scenario())

    assert result.ok is False
    assert result.error_type == "OperationTimeout"
    assert ticked is True


def test_contextvars_propagate_to_sync_thread():
    request_id = ContextVar("request_id", default="missing")
    request_id.set("REQ-P2-001")

    def read_context():
        return request_id.get()

    result = asyncio.run(safe_acall(read_context, timeout_s=1.0))

    assert result.ok is True
    assert result.value == "REQ-P2-001"


def test_sync_function_returning_awaitable():
    async def inner():
        await asyncio.sleep(0.01)
        return "awaited"

    def outer():
        return inner()

    result = asyncio.run(safe_acall(outer, timeout_s=0.20))

    assert result.ok is True
    assert result.value == "awaited"


def test_sync_function_returning_awaitable_respects_total_timeout():
    async def inner():
        await asyncio.sleep(0.20)
        return "late"

    def outer():
        return inner()

    result = asyncio.run(safe_acall(outer, timeout_s=0.05))

    assert result.ok is False
    assert result.error_type == "OperationTimeout"


def test_async_timeout():
    async def slow():
        await asyncio.sleep(0.20)
        return "done"

    result = asyncio.run(safe_acall(slow, timeout_s=0.05))

    assert result.ok is False
    assert result.error_type == "OperationTimeout"


def test_no_timeout_path():
    def sync_value():
        return "sync-ok"

    async def async_value():
        return "async-ok"

    sync_result = asyncio.run(safe_acall(sync_value))
    async_result = asyncio.run(safe_acall(async_value))

    assert sync_result.ok is True
    assert sync_result.value == "sync-ok"
    assert async_result.ok is True
    assert async_result.value == "async-ok"


def test_safe_exception_handling():
    def boom():
        raise ValueError("expected failure")

    result = asyncio.run(safe_acall(boom, timeout_s=1.0))

    assert result.ok is False
    assert result.error_type == "ValueError"
    assert "expected failure" in result.error


def test_circuit_breaker_regression():
    breaker = CircuitBreaker("phase2-test", failure_threshold=1)

    def boom():
        raise ValueError("boom")

    failed = asyncio.run(safe_acall(boom, timeout_s=1.0, breaker=breaker))
    skipped = asyncio.run(safe_acall(lambda: "should-not-run", timeout_s=1.0, breaker=breaker))

    assert failed.ok is False
    assert failed.error_type == "ValueError"
    assert breaker.state == "open"
    assert skipped.ok is False
    assert skipped.error_type == "CircuitOpen"
    assert skipped.skipped_by_breaker is True


def test_circuit_breaker_records_success():
    breaker = CircuitBreaker("phase2-success-test")

    result = asyncio.run(
        safe_acall(lambda: "success", timeout_s=1.0, breaker=breaker)
    )

    assert result.ok is True
    assert result.value == "success"
    assert breaker.state == "closed"
