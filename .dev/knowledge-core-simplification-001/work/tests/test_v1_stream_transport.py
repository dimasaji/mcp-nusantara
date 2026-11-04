import asyncio
import json

import httpx
import pytest

from app.models.ollama import OllamaProvider
from app.models.streaming import stream_observer


@pytest.mark.asyncio
async def test_real_ollama_chunks_arrive_before_generation_finishes():
    release = asyncio.Event()
    observed = []

    class Body(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b'{"response":"awal ","done":false}\n'
            await release.wait()
            yield b'{"response":"akhir","done":false}\n'
            yield b'{"model":"gemma4:test","done":true,"eval_count":2,"eval_duration":1000000}\n'

    async def handle(request):
        payload = json.loads(request.content)
        assert payload['stream'] is True and payload['think'] is False
        return httpx.Response(200, stream=Body())

    async def observe(event):
        observed.append(event)
        if event['type'] == 'delta':
            release.set()

    provider = OllamaProvider(model='gemma4:test', http_client=httpx.AsyncClient(
        base_url='http://localhost', transport=httpx.MockTransport(handle)))
    token = stream_observer.set(observe)
    try:
        answer = await asyncio.wait_for(provider.generate({'prompt': 'test'}), 3)
        assert answer['content'] == 'awal akhir'
        assert [e['text'] for e in observed if e['type'] == 'delta'] == ['awal ', 'akhir']
        assert observed[-1]['type'] == 'timing'
        assert answer['execution_identity']['identity_status'] == 'RUNTIME_CONFIRMED'
    finally:
        stream_observer.reset(token)
        await provider.close()


@pytest.mark.asyncio
async def test_cancel_closes_provider_stream_without_another_request():
    started = asyncio.Event()
    closed = asyncio.Event()
    calls = []

    class Body(httpx.AsyncByteStream):
        async def __aiter__(self):
            started.set()
            await asyncio.Event().wait()
            yield b''

        async def aclose(self):
            closed.set()

    async def handle(request):
        calls.append(request)
        return httpx.Response(200, stream=Body())

    async def observe(event):
        pass

    provider = OllamaProvider(model='fixture', http_client=httpx.AsyncClient(
        base_url='http://localhost', transport=httpx.MockTransport(handle)))
    token = stream_observer.set(observe)
    try:
        task = asyncio.create_task(provider.generate({'prompt': 'test'}))
        await asyncio.wait_for(started.wait(), 3)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert closed.is_set() and len(calls) == 1
    finally:
        stream_observer.reset(token)
        await provider.close()
