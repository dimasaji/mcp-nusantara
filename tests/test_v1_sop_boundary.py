"""Exercise real V1 HTTP functions offline, without importing app.main/settings.

Only composition is replaced: real route/projection/history code is compiled
from the source AST, with an in-memory store and model/knowledge spies. No
credentials, production database, native worker or network are accessed.
"""
import ast
import asyncio
import json
import re
import socket
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Literal
from uuid import uuid4

import pytest
from fastapi import APIRouter, FastAPI, Header, HTTPException
import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.memory.engine import MemoryEngine
from app.models.streaming import stream_observer
from app.knowledge.schemas import capture_retrieval


SESSION = 'web-12345678-1234-1234-1234-123456789abc'
PRIVATE = 'SYNTHETIC_RESTRICTED_SOURCE_DO_NOT_PUBLISH'


def payload(session=SESSION, response='Jawaban telah diperiksa.'):
    return {
        'session_id': session, 'response': response, 'model': 'fixture-local',
        'provider_status': 'ollama', 'latency_ms': 0, 'timestamp': '2026-10-21T00:00:00Z',
        'trust': {'supports_claim': True, 'confidence': .9, 'risk_level': 'low',
                  'requires_human': False, 'evidence_count': 1, 'evidence_available': True},
        'grounding': {'enabled': True, 'grounded': True, 'reason': 'grounded'},
        'understanding': {'intent': 'general'}, 'problem': {'goal': None},
        'evidence': [{'document_id': 'internal-source', 'title': 'Fixture source',
                      'chunk': PRIVATE, 'score': .9}],
    }


@pytest.fixture
def api(monkeypatch):
    original_connect = socket.socket.connect
    original_socketpair = socket.socketpair
    def event_loop_socketpair(*args, **kwargs):
        # Windows builds asyncio's private wakeup pipe using a socketpair.
        # Permit only that synchronous stdlib construction, never HTTP I/O.
        with monkeypatch.context() as local:
            local.setattr(socket.socket, 'connect', original_connect)
            return original_socketpair(*args, **kwargs)
    def deny_network(*_args, **_kwargs):
        raise AssertionError('NETWORK_FORBIDDEN')
    monkeypatch.setattr(socket, 'socketpair', event_loop_socketpair)
    monkeypatch.setattr(socket.socket, 'connect', deny_network)
    tree = ast.parse(Path('app/api/routes.py').read_text(encoding='utf-8-sig'))
    names = {'ChatRequest', 'chat', 'chat_history', '_chat_completed',
             '_record_chat_result', '_project_v1_chat_response', 'KnowledgeSearchRequest',
             'search_knowledge', 'list_knowledge_documents'}
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
             and (n.name in names or n.name.startswith('_Public'))]
    # Include production boundary imports without executing runtime composition.
    imports = [n for n in tree.body if isinstance(n, ast.ImportFrom)
               and n.module == 'app.security.v1_knowledge']
    ns = dict(BaseModel=BaseModel, ConfigDict=ConfigDict, Field=Field, Any=Any,
              Dict=Dict, Literal=Literal, Header=Header, HTTPException=HTTPException,
              router=APIRouter(prefix='/v1'), asyncio=asyncio, re=re,
              capture_retrieval=capture_retrieval, uuid4=uuid4)
    exec(compile(ast.Module(body=imports + nodes, type_ignores=[]), 'offline-v1-route', 'exec'), ns)
    calls = {'search': 0, 'model': 0, 'construct': 0, 'auth': 0}
    configuration = SimpleNamespace(llm=SimpleNamespace(provider='ollama', model='fixture-local'))
    ns['settings'] = SimpleNamespace(configuration_snapshot=lambda: (configuration, 1),
                                     record_v1_execution=lambda **_: None)
    ns['_gate_integration'] = SimpleNamespace(memory=MemoryEngine())

    def authorize(token):
        calls['auth'] += 1
        if token != 'operator-fixture':
            raise HTTPException(403, 'DENIED')
    ns['require_admin'] = authorize

    def search(*_args, **_kwargs):
        calls['search'] += 1
        return [SimpleNamespace(document_id='internal-source', chunk=PRIVATE,
                                 title='Fixture', source=PRIVATE, score=.9, metadata={})]
    ns['_knowledge'] = SimpleNamespace(search_knowledge=search,
        rag=SimpleNamespace(get_document_info=lambda _: SimpleNamespace()))

    class Provider:
        def __init__(self, **_):
            calls['construct'] += 1
        async def close(self):
            pass
    ns['OllamaProvider'] = Provider
    ns['OpenRouterProvider'] = Provider
    ns['ProviderUnavailableError'] = type('ProviderUnavailableError', (Exception,), {})

    class Agent:
        def __init__(self, **_):
            pass
        async def execute_v1(self, request, *, knowledge, **_):
            evidence = knowledge.search_knowledge(request.user_input)
            calls['model'] += 1
            observer = stream_observer.get()
            if observer is not None:
                await observer({'type': 'delta', 'text': PRIVATE})
            result = payload(request.session_id, response=request.user_input)
            if not evidence:
                result['evidence'] = []
            return SimpleNamespace(payload=result, intent_name='general')
    ns['HermesAgent'] = Agent
    for name in ('_language', '_trust_engine', '_grounding_guard', '_developer_core',
                 '_policy_engine', '_handoff_engine', '_mcp_server', '_run_sync_v1',
                 '_extract_understanding_data', '_extract_intent', '_reconcile_problem_with_intent',
                 '_extract_entities', '_get_problem_value', '_build_evidence_text',
                 '_deterministic_response', '_arithmetic_response', '_build_system_prompt',
                 '_build_user_prompt', '_model_dump'):
        ns[name] = None
    async def run_sync(fn, *args, **kwargs):
        return fn(*args, **kwargs)
    ns['_run_sync_v1'] = run_sync
    return SimpleNamespace(ns=ns, calls=calls, configuration=configuration)


def send(api, text='Halo', *, operator=False, stream=False, request_id=None, document_ids=None):
    request = api.ns['ChatRequest'](session_id=SESSION, user_input=text, stream=stream,
                                  request_id=request_id, document_ids=document_ids or [])
    return asyncio.run(api.ns['chat'](request, x_admin_token='operator-fixture' if operator else None))


def test_projection_never_serializes_raw_source(api):
    answer = api.ns['_project_v1_chat_response'](payload(), intent_name='general')
    assert PRIVATE not in json.dumps(answer)
    assert answer['evidence'][0]['document_id'] == 'internal-source'


def test_public_unscoped_chat_never_enters_restricted_retrieval(api):
    result = send(api, 'Apa persyaratan layanan?')
    assert api.calls['search'] == 0
    assert result['evidence'] == []


def test_local_operator_can_retrieve_but_citations_contain_no_raw_chunk(api):
    result = send(api, operator=True, document_ids=['internal-source'])
    assert api.calls['search'] == 1
    assert PRIVATE not in json.dumps(result)


def test_stream_does_not_publish_tokens_before_final_projection(api):
    response = send(api, stream=True)
    async def collect():
        return [json.loads(part) async for part in response.body_iterator]
    events = asyncio.run(collect())
    assert PRIVATE not in json.dumps(events)
    assert [item['type'] for item in events] == ['status', 'final']


def test_invalid_operator_token_denied_before_any_work(api):
    request = api.ns['ChatRequest'](session_id=SESSION, user_input='Halo')
    with pytest.raises(HTTPException) as exc:
        asyncio.run(api.ns['chat'](request, x_admin_token='invalid-fixture'))
    assert exc.value.status_code == 403
    assert api.calls['construct'] == api.calls['search'] == api.calls['model'] == 0


def test_legacy_history_is_not_released_to_new_public_session(api):
    api.ns['_gate_integration'].memory.record_chat(SESSION, PRIVATE, answer=payload())
    result = api.ns['chat_history'](x_chat_session=SESSION)
    assert result['turns'] == []


def test_operator_and_public_history_have_separate_security_namespaces(api):
    send(api, 'Operator internal query', operator=True, request_id='a'*32)
    send(api, 'Public query', request_id='a'*32)
    public = api.ns['chat_history'](x_chat_session=SESSION)
    assert [item['question'] for item in public['turns']] == ['Public query']
    assert 'Operator internal query' not in json.dumps(public)
    operator = api.ns['chat_history'](x_chat_session=SESSION, x_admin_token='operator-fixture')
    assert [item['question'] for item in operator['turns']] == ['Operator internal query']


def test_operator_external_denied_before_cost_or_model_construction(api, monkeypatch):
    # Tripwire blocks production ledger creation even in the unfixed route.
    import sys
    def forbidden(*_args, **_kwargs):
        raise AssertionError('LEDGER_CONSTRUCTION_FORBIDDEN')
    monkeypatch.setitem(sys.modules, 'app.models.cost_ledger', SimpleNamespace(CostLedger=forbidden))
    monkeypatch.setitem(sys.modules, 'app.models.openrouter_cost_policy',
                        SimpleNamespace(estimate_openrouter_cost=forbidden))
    api.configuration.llm.provider = 'openrouter'
    with pytest.raises(HTTPException) as exc:
        send(api, operator=True)
    assert exc.value.status_code == 409
    assert api.calls['construct'] == api.calls['search'] == api.calls['model'] == 0


def test_actual_http_boundary_denies_public_document_scope_before_lookup(api):
    def forbidden_lookup(_):
        raise AssertionError('METADATA_READ_BEFORE_AUTH')
    api.ns['_knowledge'].rag.get_document_info = forbidden_lookup
    app = FastAPI()
    app.include_router(api.ns['router'])
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
            denied = await client.post('/v1/chat', json={
                'session_id': SESSION, 'user_input': 'Query', 'document_ids': ['internal-source']})
            assert denied.status_code == 403
            invalid = await client.post('/v1/chat', headers={'X-Admin-Token': 'invalid-fixture'},
                json={'session_id': SESSION, 'user_input': 'Query'})
            assert invalid.status_code == 403
            response = await client.post('/v1/chat', json={
                'session_id': SESSION, 'user_input': 'Query', 'stream': True, 'operator': True})
            assert response.status_code == 200
            assert PRIVATE not in response.text
            # An extra body field must not promote the request to operator.
            assert api.calls['search'] == 0
    asyncio.run(exercise())


def test_same_audience_replays_without_duplicate_model_call(api):
    first = send(api, 'Query', operator=True, request_id='c'*32)
    replay = send(api, 'Query', operator=True, request_id='c'*32)
    assert first == replay
    assert api.calls['search'] == api.calls['model'] == 1


def test_namespaced_history_survives_restart_without_public_operator_crossover(api, tmp_path):
    api.ns['_gate_integration'].memory = MemoryEngine(storage_root=tmp_path)
    send(api, 'Internal question', operator=True, request_id='d'*32)
    send(api, 'Public question', request_id='e'*32)
    api.ns['_gate_integration'].memory = MemoryEngine(storage_root=tmp_path)
    public = api.ns['chat_history'](x_chat_session=SESSION)
    private = api.ns['chat_history'](x_chat_session=SESSION, x_admin_token='operator-fixture')
    assert [item['question'] for item in public['turns']] == ['Public question']
    assert [item['question'] for item in private['turns']] == ['Internal question']
    assert PRIVATE not in json.dumps(public) + json.dumps(private)


def test_history_redacts_raw_chunks_even_if_a_stored_answer_contains_them(api):
    from app.security.v1_knowledge import v1_session_id
    api.ns['_gate_integration'].memory.record_chat(
        v1_session_id(SESSION, operator=False), 'Question', answer=payload())
    public = api.ns['chat_history'](x_chat_session=SESSION)
    assert PRIVATE not in json.dumps(public)
    assert public['turns'][0]['answer']['session_id'] == SESSION


def test_knowledge_denial_happens_before_real_embedding_and_sqlite_retrieval(api, tmp_path):
    from app.knowledge.engine import KnowledgeEngine
    from app.knowledge.rag import RAG
    from app.knowledge.schemas import KnowledgeBaseConfig, DocumentIngestRequest
    from app.knowledge.store import SQLiteVectorStore
    from app.security.v1_knowledge import V1KnowledgeBoundary

    store = SQLiteVectorStore(str(tmp_path/'fixture.db'))
    rag = RAG(config=KnowledgeBaseConfig(embedding_model='fixture', embedding_dimension=3),
              vector_store=store)
    rag.set_embedding_func(lambda _: [1., 0., 0.])
    assert rag.ingest_document(DocumentIngestRequest(document_id='internal-source',
        title='Synthetic source', source=PRIVATE)).success
    observed = []
    rag.set_embedding_func(lambda _: observed.append('embed') or [1., 0., 0.])
    owner = KnowledgeEngine(rag=rag)
    public = V1KnowledgeBoundary(owner, operator=False, provider='ollama')
    assert public.search_knowledge('Query') == []
    assert observed == []
    with pytest.raises(HTTPException):
        V1KnowledgeBoundary(owner, operator=True, provider='openrouter')
    assert observed == []
    operator = V1KnowledgeBoundary(owner, operator=True, provider='ollama')
    result = operator.search_knowledge(PRIVATE, filter={'document_ids': ['internal-source']})
    assert observed == ['embed']
    assert result and result[0].document_id == 'internal-source'


def test_stream_failure_does_not_reveal_internal_exception(api):
    async def failure(*_args, **_kwargs):
        raise RuntimeError(PRIVATE)
    api.ns['_chat_completed'] = failure
    response = send(api, stream=True)
    async def collect():
        return [json.loads(part) async for part in response.body_iterator]
    events = asyncio.run(collect())
    assert PRIVATE not in json.dumps(events)
    assert events[-1]['type'] == 'error' and events[-1]['status'] == 500


def test_direct_knowledge_http_endpoints_are_operator_only_before_store_access(api):
    def forbidden_list():
        raise AssertionError('DOCUMENT_LIST_READ_BEFORE_AUTH')
    api.ns['_knowledge'].list_documents = forbidden_list
    app = FastAPI()
    app.include_router(api.ns['router'])
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
            search = await client.post('/v1/knowledge/search', json={'query': 'Query'})
            assert search.status_code == 403
            listing = await client.get('/v1/knowledge/documents')
            assert listing.status_code == 403
            assert api.calls['search'] == 0
    asyncio.run(exercise())


def test_omitted_session_never_uses_a_shared_public_default(api):
    first = api.ns['ChatRequest'](user_input='Halo')
    second = api.ns['ChatRequest'](user_input='Halo')
    assert first.session_id != second.session_id
    assert re.fullmatch(r'web-[a-f0-9-]{36}', first.session_id)


def test_external_public_chat_never_retrieves_internal_evidence(api, monkeypatch):
    import sys
    # The adapter/ledger are fakes; no external transport or disk ledger exists.
    monkeypatch.setitem(sys.modules, 'app.models.cost_ledger',
                        SimpleNamespace(CostLedger=lambda *_args, **_kwargs: object()))
    monkeypatch.setitem(sys.modules, 'app.models.openrouter_cost_policy',
                        SimpleNamespace(estimate_openrouter_cost=lambda *_args, **_kwargs: None))
    api.configuration.llm.provider = 'openrouter'
    result = send(api, 'General conversation')
    assert result['evidence'] == []
    assert api.calls['search'] == 0


def test_operator_http_search_still_works_with_explicit_authorization(api):
    app = FastAPI()
    app.include_router(api.ns['router'])
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
            response = await client.post('/v1/knowledge/search', json={'query': 'Query'},
                                         headers={'X-Admin-Token': 'operator-fixture'})
            assert response.status_code == 200
            assert api.calls['search'] == 1
            assert response.json()['results'][0]['document_id'] == 'internal-source'
    asyncio.run(exercise())
