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
