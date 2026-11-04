import httpx
import pytest
import json

from app.exceptions import ProviderUnavailableError
from app.models.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_upstream_500_is_provider_unavailable_without_body_leak():
    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(base_url="http://fixture", transport=httpx.MockTransport(
        lambda req: httpx.Response(500, json={"error": "private upstream detail"})))
    try:
        with pytest.raises(ProviderUnavailableError) as error:
            await provider.generate({"prompt": "test"})
        assert error.value.status_code == 503
        assert "private" not in str(error.value)
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_generation_options_are_bounded_and_sent_inside_options():
    captured = []
    def respond(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"response": "{}", "eval_count": 2})
    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(base_url="http://fixture", transport=httpx.MockTransport(respond))
    try:
        await provider.generate({"prompt": "test", "max_tokens": 8, "temperature": 0.0})
        await provider.generate_structured({"prompt": "test", "max_tokens": 8})
        for payload in captured:
            assert payload["options"]["num_ctx"] == 4096
            assert payload["options"]["num_predict"] == 8
            assert "num_predict" not in payload
        assert captured[0]["options"]["temperature"] == 0.0
    finally:
        await provider.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["generate", "generate_structured"])
@pytest.mark.parametrize("body", [b"private upstream invalid JSON", b"[]", b"null"])
async def test_malformed_provider_response_is_unavailable_without_body_leak(method, body):
    provider = OllamaProvider()
    provider._client = httpx.AsyncClient(
        base_url="http://fixture",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=body)),
    )
    try:
        with pytest.raises(ProviderUnavailableError) as error:
            await getattr(provider, method)({"prompt": "test"})
        assert error.value.status_code == 503
        assert "private" not in str(error.value)
    finally:
        await provider.close()
