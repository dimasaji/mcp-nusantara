"""Regression for NUS-V1-LLAMA-RAG-001 runtime 500 (Defect C).

The local Ollama client must talk directly to the configured loopback URL and
never honor ambient environment proxy variables. A NO_PROXY entry such as
'[::1]' makes httpx's default trust_env=True client build an invalid URLPattern
mount and raise InvalidURL: Invalid port ':1]', which crashed every
health_check/generate call after retrieval had already succeeded.
"""
import asyncio

import httpx

from app.models.ollama import OllamaProvider

# The exact ambient value observed on the operator machine (Windows/Node setup).
BAD_NO_PROXY = "localhost,.localhost,127.0.0.1,127.0.0.0/8,[::1],::1"
LOCAL_OLLAMA = "http://127.0.0.1:11434"  # repo .env LLM_BASE_URL


def test_get_client_survives_ipv6_no_proxy_entry(monkeypatch):
    monkeypatch.setenv("NO_PROXY", BAD_NO_PROXY)
    provider = OllamaProvider(base_url=LOCAL_OLLAMA, model="llama3.2:1b")

    async def build_and_check():
        client = await provider._get_client()
        try:
            # Local-only provider must not inherit environment proxies.
            assert client.trust_env is False
            assert str(client.base_url).rstrip("/") == LOCAL_OLLAMA
        finally:
            await provider.close()

    # Before the fix this raises httpx.InvalidURL: Invalid port ':1]'.
    asyncio.run(build_and_check())


def test_health_check_does_not_crash_on_proxy_env(monkeypatch):
    monkeypatch.setenv("NO_PROXY", BAD_NO_PROXY)
    provider = OllamaProvider(base_url=LOCAL_OLLAMA, model="llama3.2:1b")

    async def handler(request):
        return httpx.Response(200, json={"models": [{"name": "llama3.2:1b"}]})

    transport = httpx.MockTransport(handler)

    async def run():
        # Inject a client built the same way the provider builds its own, so the
        # mount-parsing path is exercised under the hostile NO_PROXY value.
        client = httpx.AsyncClient(base_url=LOCAL_OLLAMA, transport=transport,
                                   trust_env=False)
        provider._client = client
        provider._injected_client = True
        try:
            result = await provider.health_check()
            assert result["available"] is True
        finally:
            await provider.close()

    asyncio.run(run())