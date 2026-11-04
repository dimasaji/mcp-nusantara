import asyncio

import httpx
import pytest

from app.core.nusantara_config import load_nusantara_config
from app.models.cost_ledger import CostLedger
from app.models.openrouter import OpenRouterProvider


def test_cancellation_preserves_reservation(tmp_path):
    config = load_nusantara_config(
        overrides={"llm": {"provider": "openrouter"}}
    )
    ledger = CostLedger(
        tmp_path / "cost.db",
        budget_usd="1.00",
        per_request_cap_usd="0.05",
    )

    entered_transport = asyncio.Event()

    async def transport(request):
        entered_transport.set()
        await asyncio.sleep(60)
        return httpx.Response(200, json={})

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(transport)
        ) as client:
            provider = OpenRouterProvider(
                nusantara_config=config,
                http_client=client,
                key_resolver=lambda: "synthetic-test-key",
                cost_ledger=ledger,
                cost_estimator=lambda payload: "0.01",
            )

            task = asyncio.create_task(
                provider.generate({"prompt": "uji cancellation"})
            )

            await asyncio.wait_for(entered_transport.wait(), timeout=3)
            task.cancel()

            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(run())

    summary = ledger.summary()
    assert summary["reserved_usd"] == "0.01"
    assert summary["history"][0]["status"] == "unknown"
