"""Regression contract: OpenRouter must not dispatch without cost governance."""
import asyncio

import httpx
import pytest

from app.core.nusantara_config import load_nusantara_config
from app.models.openrouter import OpenRouterProvider


def test_openrouter_fails_closed_without_cost_governance():
    config = load_nusantara_config(
        overrides={"llm": {"provider": "openrouter"}}
    )
    calls = []

    def transport(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "model": config.llm.model,
                "choices": [{"message": {"content": "unexpected dispatch"}}],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                    "cost": 0.001,
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
            )
            try:
                with pytest.raises(Exception):
                    await provider.generate({"prompt": "offline test"})
            finally:
                await provider.close()

    asyncio.run(run())
    assert calls == [], "OpenRouter transport was called without a cost guard"
