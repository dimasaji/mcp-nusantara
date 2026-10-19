import asyncio
from dataclasses import replace
from types import SimpleNamespace

from fastapi import HTTPException

from app.api import routes
from app.hermes.agent import HermesAgent
from app.memory.engine import MemoryEngine


SESSION = 'web-12345678-1234-1234-1234-123456789abc'
ANSWER = {
    'session_id': SESSION, 'response': 'Jawaban fixture.', 'model': 'fixture-local',
    'provider_status': 'local_rule', 'latency_ms': 0, 'timestamp': '2026-10-16T00:00:00Z',
    'trust': {'supports_claim': True, 'confidence': 1.0, 'risk_level': 'low',
              'requires_human': False, 'evidence_count': 0, 'evidence_available': False},
    'grounding': {'enabled': True, 'grounded': True, 'reason': 'fixture'},
    'understanding': {'intent': 'general'}, 'problem': {'goal': None}, 'evidence': [],
}


def _isolate_route(monkeypatch, tmp_path, execute):
    configuration, revision = routes.settings.configuration_snapshot()
    snapshot = configuration._snapshot.model_copy(update={
        'llm': configuration.llm.model_copy(update={'provider': 'ollama'})})
    configuration = replace(configuration, _snapshot=snapshot)
    monkeypatch.setattr(type(routes.settings), 'configuration_snapshot',
                        lambda _self: (configuration, revision))
    monkeypatch.setattr(type(routes.settings), 'record_v1_execution',
                        lambda _self, **_kwargs: None)
    monkeypatch.setattr(routes, '_gate_integration', SimpleNamespace(
        memory=MemoryEngine(storage_root=tmp_path)))
    monkeypatch.setattr(HermesAgent, 'execute_v1', execute)
    monkeypatch.setattr(routes, '_project_v1_chat_response', lambda *_args, **_kwargs: dict(ANSWER))


def test_repeated_chat_request_id_replays_answer_without_running_agent_twice(monkeypatch, tmp_path):
    calls = 0

    async def execute(self, *_args, **_kwargs):
        nonlocal calls
        calls += 1
        return SimpleNamespace(payload={}, intent_name='general')

    _isolate_route(monkeypatch, tmp_path, execute)
    request = routes.ChatRequest(session_id=SESSION, user_input='Halo', request_id='a' * 32)

    first = asyncio.run(routes.chat(request))
    repeated = asyncio.run(routes.chat(request))

    assert first == ANSWER
    assert repeated == ANSWER
    assert calls == 1
    history = routes._gate_integration.memory.chat_history(SESSION)
    assert len(history) == 1
    assert history[0]['status'] == 'SUCCEEDED'


def test_retry_uses_new_id_only_for_persisted_pre_provider_504(monkeypatch, tmp_path):
    calls = 0

    async def execute(self, *_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise HTTPException(504, 'batas waktu pemrosesan terlampaui')
        return SimpleNamespace(payload={}, intent_name='general')

    _isolate_route(monkeypatch, tmp_path, execute)
    first_request = routes.ChatRequest(session_id=SESSION, user_input='Halo', request_id='b' * 32)
    try:
        asyncio.run(routes.chat(first_request))
    except HTTPException as error:
        assert error.status_code == 504
        assert error.headers['X-Chat-Retry-Safe'] == 'pre-provider'
    else:
        raise AssertionError('first request should time out before provider dispatch')

    retry = routes.ChatRequest(session_id=SESSION, user_input='Halo',
                               request_id='c' * 32, retry_of='b' * 32)
    assert asyncio.run(routes.chat(retry)) == ANSWER
    assert calls == 2


def test_provider_unknown_failure_is_cached_and_cannot_be_retried_as_safe(monkeypatch, tmp_path):
    calls = 0

    async def execute(self, *_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise HTTPException(503, 'provider outcome unknown')

    _isolate_route(monkeypatch, tmp_path, execute)
    request = routes.ChatRequest(session_id=SESSION, user_input='Pertanyaan', request_id='d' * 32)
    for _ in range(2):
        try:
            asyncio.run(routes.chat(request))
        except HTTPException as error:
            assert error.status_code == 503
        else:
            raise AssertionError('provider failure must be returned')
    assert calls == 1

    unsafe_retry = routes.ChatRequest(session_id=SESSION, user_input='Pertanyaan',
                                      request_id='e' * 32, retry_of='d' * 32)
    try:
        asyncio.run(routes.chat(unsafe_retry))
    except HTTPException as error:
        assert error.status_code == 409
        assert error.detail == 'CHAT_RETRY_NOT_SAFE'
    else:
        raise AssertionError('uncertain provider failure must not be retried under a new request ID')
    assert calls == 1
