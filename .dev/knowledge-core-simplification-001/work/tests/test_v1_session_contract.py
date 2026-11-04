"""Chat, history and citations share a session capability contract."""
import asyncio

import httpx
import pytest
from fastapi import FastAPI
from test_v1_sop_boundary import api as api


@pytest.mark.parametrize('session', ['web', 'other', 'web-' + 'a' * 36, '../web', ''])
def test_shared_or_malformed_session_is_denied_before_work(api, session):
    app = FastAPI()
    app.include_router(api.ns['router'])

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
            chat = await client.post('/v1/chat', json={'session_id': session, 'user_input': 'Halo'})
            history = await client.get('/v1/chat/history', headers={'X-Chat-Session': session})
            assert chat.status_code == 422
            assert history.status_code == 403
            assert api.calls['construct'] == api.calls['search'] == api.calls['model'] == 0
    asyncio.run(exercise())
