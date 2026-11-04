import asyncio
import threading

import pytest
from fastapi import HTTPException

from app.api import routes


@pytest.mark.asyncio
async def test_timed_out_work_keeps_capacity_and_recovers(monkeypatch):
    monkeypatch.setattr(routes, "_sync_slots", threading.BoundedSemaphore(1))
    release = threading.Event()
    entered = threading.Event()
    def stuck():
        entered.set()
        release.wait(2)
        return "done"
    try:
        with pytest.raises(HTTPException) as timed_out:
            await routes._run_sync_v1(stuck, timeout_s=.03)
        assert timed_out.value.status_code == 504
        assert entered.is_set()
        # The event loop remains available; no second stuck task gets queued.
        await asyncio.sleep(.01)
        with pytest.raises(HTTPException) as busy:
            await routes._run_sync_v1(lambda: "new")
        assert busy.value.status_code == 503
    finally:
        release.set()
        await asyncio.sleep(.05)
    assert await routes._run_sync_v1(lambda: "recovered") == "recovered"
