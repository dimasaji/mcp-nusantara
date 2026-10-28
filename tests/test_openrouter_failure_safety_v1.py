import asyncio

import httpx
import pytest

from app.core.nusantara_config import load_nusantara_config
from app.models.cost_ledger import CostLedger
from app.models.openrouter import OpenRouterProvider


def test_timeout_preserves_reservation(tmp_path):
    config = load_nusantara_config(
        overrides={"llm": {"provider": "openrouter"}}
    )
    ledger = CostLedger(
        tmp_path / "cost.db",
        budget_usd="1.00",
        per_request_cap_usd="0.05",
    )

    def transport(request):
        raise httpx.ReadTimeout("simulated timeout")

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
            with pytest.raises(Exception):
                await provider.generate({"prompt": "test timeout"})

    asyncio.run(run())

    summary = ledger.summary()
    assert summary["reserved_usd"] == "0.01"
    assert summary["history"][0]["status"] == "unknown"


def test_missing_cost_preserves_reservation(tmp_path):
    config = load_nusantara_config(
        overrides={"llm": {"provider": "openrouter"}}
    )
    ledger = CostLedger(
        tmp_path / "cost.db",
        budget_usd="1.00",
        per_request_cap_usd="0.05",
    )

    def transport(request):
        return httpx.Response(
            200,
            json={
                "model": config.llm.model,
                "choices": [
                    {"message": {"content": "Jawaban mock"}}
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                },
            },
        )

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
            return await provider.generate({"prompt": "test missing cost"})

    result = asyncio.run(run())

    assert result["content"] == "Jawaban mock"
    assert ledger.summary()["history"][0]["status"] == "unknown"
