"""Twenty V1 turns use a real temporary index/Hermes and fixture inference.

This tests orchestration, replay, restart and access; not live model quality.
"""
import asyncio

import pytest
from fastapi import HTTPException
from test_selected_pdf_chat import approved_pdf as approved_pdf
from test_v1_langgraph import fixture
from test_v1_sop_boundary import SESSION
from test_v1_sop_boundary import api as api

from app.knowledge.sop_review import SOPReview
from app.memory.engine import MemoryEngine


def test_twenty_document_turns_reopen_replay_isolate_and_revoke(api, approved_pdf, tmp_path):
    engine, identifier = approved_pdf
    parts = fixture(answer='Wajib membawa KTP dan membayar 500 rupiah.')
    memory_root = tmp_path / 'history'
    api.ns['_knowledge'] = engine
    api.ns['_gate_integration'].memory = MemoryEngine(storage_root=memory_root)
    gates = parts[2]['gates']
    def remember(session_id, response, service_context=None):
        api.ns['_gate_integration'].memory.remember(session_id, 'assistant', response,
            service_context=service_context or {})
    gates.remember_response = remember

    class Agent:
        def __init__(self, **kwargs):
            pass
        async def execute_v1(self, request, **services):
            gates.memory = api.ns['_gate_integration'].memory
            return await parts[1].execute_v1(request, **{**parts[2], 'knowledge': services['knowledge']})
    api.ns['HermesAgent'] = Agent

    scenarios = [('Apa persyaratan menurut SOP ini?', 'Surat Pengantar', 1),
                 ('Berapa lama waktu penyelesaiannya?', '7 Hari Kerja', 2)]
    last = None
    for index in range(20):
        if index == 10:
            api.ns['_gate_integration'].memory = MemoryEngine(storage_root=memory_root)
        question, expected, page = scenarios[index % len(scenarios)]
        request = api.ns['ChatRequest'](session_id=SESSION, user_input=question,
            document_ids=[identifier], request_id=f'{index+1:032x}')
        result = asyncio.run(api.ns['chat'](request, x_admin_token='operator-fixture'))
        assert expected in result['response']
        assert result['grounding']['grounded'] is True
        assert result['evidence'][0]['document_id'] == identifier
        assert page in result['evidence'][0]['pages']
        assert result['evidence'][0]['chunk'] == ''
        last = request

    history = api.ns['chat_history'](x_chat_session=SESSION, x_admin_token='operator-fixture')
    assert len(history['turns']) == 20
    assert all(turn['status'] == 'SUCCEEDED' for turn in history['turns'])
    assert api.ns['chat_history'](x_chat_session=SESSION)['turns'] == []
    before = parts[4].calls
    assert asyncio.run(api.ns['chat'](last, x_admin_token='operator-fixture')) == result
    assert parts[4].calls == before
    review = SOPReview(engine)
    detail = review.detail(identifier)
    review.decide(identifier, detail['version_id'], 'revoke', 'fixture-reviewer', 'Pengujian pencabutan')
    with pytest.raises(HTTPException) as failure:
        asyncio.run(api.ns['chat'](last, x_admin_token='operator-fixture'))
    assert failure.value.status_code == 409
    assert parts[4].calls == before
