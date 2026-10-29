"""A timeout after model dispatch must never be advertised as retry-safe."""
import asyncio

import pytest
from fastapi import HTTPException
from test_v1_sop_boundary import SESSION, send
from test_v1_sop_boundary import api as api


def test_post_generation_timeout_is_unknown_and_cannot_start_a_new_retry(api):
    class Agent:
        def __init__(self, provider, **kwargs):
            provider.generation_started = True  # provider fixture; no network
        async def execute_v1(self, *args, **kwargs):
            raise HTTPException(504, 'stage timeout', headers={'X-Chat-Retry-Safe': 'pre-provider'})
    api.ns['HermesAgent'] = Agent
    with pytest.raises(HTTPException) as failure:
        send(api, request_id='a' * 32)
    assert (failure.value.headers or {}).get('X-Chat-Retry-Safe') != 'pre-provider'
    request = api.ns['ChatRequest'](session_id=SESSION, user_input='Halo', request_id='b'*32, retry_of='a'*32)
    with pytest.raises(HTTPException) as retry:
        asyncio.run(api.ns['chat'](request))
    assert retry.value.status_code == 409
    assert retry.value.detail == 'CHAT_RETRY_NOT_SAFE'
