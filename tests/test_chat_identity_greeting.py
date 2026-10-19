"""Identity conversation may have a greeting, without bypassing evidence domains."""
import asyncio
from types import SimpleNamespace
import pytest
from app.hermes.agent import _conversation_request
from test_v1_langgraph import fixture


@pytest.mark.parametrize('question',['Halo, siapa kamu?','Hallo! Siapa Anda?','Hai, siapa kamu?'])
def test_identity_with_greeting_reaches_model_conversation(question):
    assert _conversation_request(question)
    parts=fixture(answer='Saya asisten AI Nusantara. Ada yang dapat saya bantu?')
    core=asyncio.run(parts[1].execute_v1(SimpleNamespace(user_input=question,session_id='identity-fixture',model=None,stream=False),**parts[2]))
    public=parts[3](core.payload,intent_name=core.intent_name)
    assert parts[4].calls==1
    assert public['response']=='Saya asisten AI Nusantara. Ada yang dapat saya bantu?'
    assert public['grounding']['reason']=='not_evaluated'
    assert not public['evidence']


@pytest.mark.parametrize('question',['Halo, apa syarat membuat KTP?','Halo, siapa kamu? Berapa biaya paspor?',
 'Halo, apa fungsi Nusantara?','Halo, siapa kamu? Permohonan saya sudah disetujui?'])
def test_greeting_cannot_bypass_evidence_required_requests(question):
    assert not _conversation_request(question)
