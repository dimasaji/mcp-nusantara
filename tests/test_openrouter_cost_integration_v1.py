import asyncio
from pathlib import Path
import json

import httpx
import pytest

from app.core.nusantara_config import load_nusantara_config
from app.models.cost_ledger import CostLedger
from app.models.openrouter import OpenRouterProvider
from app.models.openrouter_cost_policy import CostEstimateUnavailable, estimate_openrouter_cost


@pytest.mark.parametrize('stream', [False, True, 'false', 0])
def test_actual_payload_uses_real_estimator_before_dispatch(tmp_path, stream):
    """Exercise the adapter/estimator seam that a constant cost stub misses."""
    config = load_nusantara_config(overrides={'llm': {'provider': 'openrouter'}})
    pricing = tmp_path / 'pricing.json'
    pricing.write_text(json.dumps({'models': {config.llm.model: {
        'verified': True, 'input_usd_per_token': '0.00000015',
        'output_usd_per_token': '0.0000006', 'max_input_tokens': 4096,
        'max_output_tokens': 220,
    }}}), encoding='utf-8')
    ledger = CostLedger(tmp_path / 'cost.db', budget_usd='1.00', per_request_cap_usd='0.05')
    calls = []

    def transport(request):
        assert ledger.summary()['reserved_usd'] != '0.00'
        calls.append(request)
        return httpx.Response(200, json={'model': config.llm.model,
            'choices': [{'message': {'content': 'Fixture answer'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15, 'cost': 0.001}})

    def estimate(payload):
        assert payload['stream'] is False
        if stream is not False:
            payload = {**payload, 'stream': stream}
        return estimate_openrouter_cost(payload, pricing_file=pricing)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            provider = OpenRouterProvider(nusantara_config=config, http_client=client,
                key_resolver=lambda: 'synthetic-test-key', cost_ledger=ledger, cost_estimator=estimate)
            return await provider.generate({'prompt': 'Fixture question', 'max_tokens': 20})

    if stream is False:
        assert asyncio.run(run())['content'] == 'Fixture answer'
        assert len(calls) == 1
        assert ledger.summary()['actual_usd'] == '0.01'
    else:
        with pytest.raises(CostEstimateUnavailable):
            asyncio.run(run())
        assert calls == []
        assert ledger.summary()['reserved_usd'] == '0.00'


def test_openrouter_reserves_before_dispatch(tmp_path):
    config = load_nusantara_config(
        overrides={"llm": {"provider": "openrouter"}}
    )

    ledger = CostLedger(
        tmp_path / "cost.db",
        budget_usd="1.00",
        per_request_cap_usd="0.05",
    )

    calls = []

    def transport(request):
        # HTTP tidak boleh berjalan tanpa reservasi sebelumnya.
        assert ledger.summary()["reserved_usd"] != "0.00"
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "model": config.llm.model,
                "choices": [
                    {"message": {"content": "Jawaban pengujian"}}
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
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
                cost_ledger=ledger,
                cost_estimator=lambda payload: "0.01",
            )
            return await provider.generate({
                "prompt": "Uji reservasi biaya",
                "max_tokens": 20,
            })

    result = asyncio.run(run())

    assert result["content"] == "Jawaban pengujian"
    assert len(calls) == 1
    assert ledger.summary()["actual_usd"] == "0.01"
