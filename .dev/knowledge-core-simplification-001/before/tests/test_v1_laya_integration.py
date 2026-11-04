"""V1 regressions; real orchestrator/grounding, controlled external model boundary."""
import asyncio
import socket
from types import SimpleNamespace

import httpx

from app.core.nusantara_config import load_nusantara_config
from app.language.laya_intent import LayaIntentAdapter
from test_laya_intent import answer
from test_v1_service_dialogue import setup


def configured_parts(*, enabled, transport=None, base_url='http://127.0.0.1:18765'):
    parts = setup()
    config = load_nusantara_config(overrides={'laya_intent': {
        'enabled': enabled, 'base_url': base_url, 'timeout_s': .1}}).laya_intent
    adapter = LayaIntentAdapter(config, transport=transport)
    parts[1].language = SimpleNamespace(sop_intent_adapter=adapter, classify_sop_intent=adapter.classify)

    async def run_sync(fn, *args, timeout_s=30, **kwargs):
        return await asyncio.wait_for(asyncio.to_thread(fn, *args, **kwargs), timeout_s)
    parts[2]['run_sync'] = run_sync
    return parts, adapter


def ask(parts, text, session='laya-integration'):
    request = SimpleNamespace(user_input=text, session_id=session, model=None, stream=False)
    core = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    return parts[3](core.payload, intent_name=core.intent_name)


def comparable(public):
    return {key: value for key, value in public.items() if key not in {'timestamp', 'latency_ms'}}


def test_laya_hint_keeps_baseline_evidence_and_canonical_intent():
    calls = []
    def laya(request):
        calls.append(request)
        return httpx.Response(200, json=answer())
    off, disabled = configured_parts(enabled=False)
    on, enabled = configured_parts(enabled=True, transport=httpx.MockTransport(laya))
    queries = []
    baseline_search = on[2]['knowledge'].search_knowledge
    def search(query, **kwargs):
        queries.append(query)
        if len(queries) == 1:
            return baseline_search(query, **kwargs)
        # A confident intent must not elevate low-scoring or unrelated evidence.
        return [SimpleNamespace(document_id='irrelevant', title='Other service',
            chunk='Waktu penyelesaian 99 hari.', source='Other service', score=.1)]
    on[2]['knowledge'].search_knowledge = search
    try:
        original = ask(off, 'Berapa lama proses permohonan data pribadi?')
        enhanced = ask(on, 'Berapa lama proses permohonan data pribadi?')
        assert len(queries) == 2 and len(calls) == 1
        assert 'waktu penyelesaian' in queries[1]
        assert comparable(original) == comparable(enhanced)
        assert [item['document_id'] for item in enhanced['evidence']] == ['service-private']
        assert enhanced['grounding']['grounded']
    finally:
        disabled.close(); enabled.close()


def test_dead_laya_keeps_final_answer_and_followup_session_context():
    off, disabled = configured_parts(enabled=False)
    with socket.socket() as port:
        port.bind(('127.0.0.1', 0))
        dead, unavailable = configured_parts(enabled=True, base_url=f'http://127.0.0.1:{port.getsockname()[1]}')
        try:
            for text in ['Mau minta data pribadi, bawa apa?', 'Kalau prosesnya?', 'Berapa lama?', 'Bisa online?']:
                assert comparable(ask(off, text)) == comparable(ask(dead, text))
        finally:
            disabled.close(); unavailable.close()


def test_timeout_and_failed_extra_search_keep_original_final_answer():
    baseline, disabled = configured_parts(enabled=False)
    def timeout(request): raise httpx.ReadTimeout('fixture', request=request)
    slow, timed = configured_parts(enabled=True, transport=httpx.MockTransport(timeout))
    extra, accepted = configured_parts(enabled=True, transport=httpx.MockTransport(lambda request: httpx.Response(200, json=answer())))
    original_search = extra[2]['knowledge'].search_knowledge
    searches = []
    def search(query, **kwargs):
        searches.append(query)
        if len(searches) > 1: raise RuntimeError('fixture external store failure')
        return original_search(query, **kwargs)
    extra[2]['knowledge'].search_knowledge = search
    try:
        question = 'Berapa lama proses permohonan data pribadi?'
        expected = comparable(ask(baseline, question))
        assert comparable(ask(slow, question)) == expected
        assert comparable(ask(extra, question)) == expected
    finally:
        disabled.close(); timed.close(); accepted.close()
