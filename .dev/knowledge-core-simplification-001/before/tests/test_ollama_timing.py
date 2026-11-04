import httpx
import pytest

from app.models.ollama import OllamaProvider
from app.observability import metrics


@pytest.mark.asyncio
async def test_optional_metrics_failure_does_not_discard_model_answer(monkeypatch):
    def broken_metrics(*args, **kwargs):
        raise RuntimeError('metrics unavailable')

    monkeypatch.setattr(metrics, 'observe', broken_metrics)
    client = httpx.AsyncClient(base_url='http://fixture.invalid', transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={'response': 'Jawaban fixture',
            'done': True, 'model': 'fixture-local'})))
    provider = OllamaProvider(model='fixture-local', http_client=client)
    try:
        result = await provider.generate({'prompt': 'Fixture only'})
        assert result['content'] == 'Jawaban fixture'
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_nonstreaming_exposes_provider_durations_without_changing_answer():
    client = httpx.AsyncClient(base_url='http://fixture.invalid', transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={'response': 'Jawaban fixture', 'done': True,
            'model': 'fixture-local', 'total_duration': 9000000000, 'load_duration': 2000000000,
            'prompt_eval_duration': 3000000000, 'eval_duration': 4000000000,
            'prompt_eval_count': 10, 'eval_count': 5})))
    provider = OllamaProvider(model='fixture-local', http_client=client)
    try:
        result = await provider.generate({'prompt': 'Fixture only'})
        assert result['content'] == 'Jawaban fixture'
        assert result['timings'] == {'total_ms': 9000, 'load_ms': 2000, 'prompt_eval_ms': 3000,
            'eval_ms': 4000, 'prompt_eval_count': 10, 'eval_count': 5}
        assert provider.generation_started is True
    finally:
        await provider.close()
