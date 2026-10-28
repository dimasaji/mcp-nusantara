"""Cached sourced replies must retain current publication/version authority."""
import pytest
from fastapi import HTTPException

from app.knowledge.sop_review import SOPReview
from test_sop_review import engine_at
from test_review_publication_v1 import _approve_fixture, _convert
from test_v1_sop_boundary import api, send, SESSION
from test_selected_pdf_chat import approved_pdf


def test_unscoped_replay_cannot_release_a_revoked_source_answer(api, tmp_path):
    engine=engine_at(tmp_path/'source.db')
    identifier=engine.process_knowledge_source('SOP.txt',
        b'Persyaratan pelayanan adalah Surat Permohonan. Prosedur mengikuti SOP yang diperiksa.')['document_id']
    review=SOPReview(engine)
    detail=review.detail(identifier)
    _approve_fixture(review,detail)
    api.ns['_knowledge']=engine
    first=send(api,'Persyaratan',operator=True,request_id='d'*32)
    assert first['evidence'][0]['document_id']==identifier
    replay=send(api,'Persyaratan',operator=True,request_id='d'*32)
    assert replay==first
    assert api.calls['model']==1
    history=api.ns['chat_history'](SESSION,x_admin_token='operator-fixture')
    import json
    assert 'source_versions' not in json.dumps(history)
    review.decide(identifier,detail['version_id'],'problem','test-reviewer','Perlu pemeriksaan ulang')
    before=api.calls['model']
    with pytest.raises(HTTPException) as rejected:
        send(api,'Persyaratan',operator=True,request_id='d'*32)
    assert rejected.value.status_code==409
    assert api.calls['model']==before


def test_revocation_during_generation_prevents_release(api, tmp_path):
    engine=engine_at(tmp_path/'source.db')
    identifier=engine.process_knowledge_source('SOP.txt',
        b'Persyaratan pelayanan adalah Surat Permohonan. Prosedur mengikuti SOP yang diperiksa.')['document_id']
    review=SOPReview(engine)
    detail=review.detail(identifier)
    _approve_fixture(review,detail)
    api.ns['_knowledge']=engine
    original=api.ns['HermesAgent']
    class RevokingAgent(original):
        async def execute_v1(self,*args,**kwargs):
            core=await super().execute_v1(*args,**kwargs)
            review.decide(identifier,detail['version_id'],'problem','test-reviewer','Pemeriksaan ulang')
            return core
    api.ns['HermesAgent']=RevokingAgent
    with pytest.raises(HTTPException) as rejected:
        send(api,'Persyaratan',operator=True,request_id='f'*32,document_ids=[identifier])
    assert rejected.value.status_code==409
    assert api.calls['model']==1


def test_selected_replay_cannot_relabel_an_answer_after_reapproval(api, approved_pdf, monkeypatch):
    from app.knowledge.document_tools import DocumentTools, PARSER_VERSION
    engine,identifier=approved_pdf
    api.ns['_knowledge']=engine
    first=send(api,'Persyaratan',operator=True,request_id='e'*32,document_ids=[identifier])
    assert first['evidence'][0]['document_id']==identifier
    monkeypatch.setattr('app.knowledge.document_tools.PARSER_VERSION',PARSER_VERSION+'-new-provenance')
    review=SOPReview(engine)
    newer=_convert(DocumentTools(engine,operator=True),review,identifier,force=True)
    _approve_fixture(review,newer)
    before=api.calls['model']
    with pytest.raises(HTTPException) as rejected:
        send(api,'Persyaratan',operator=True,request_id='e'*32,document_ids=[identifier])
    assert rejected.value.status_code==409
    assert api.calls['model']==before
