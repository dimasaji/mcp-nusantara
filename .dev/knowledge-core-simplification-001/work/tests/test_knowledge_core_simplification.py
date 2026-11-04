"""Contract behavior through the persistent review interface; isolated stores only."""
from test_sop_review import engine_at, confirm_fixture_metadata
from app.knowledge.sop_review import SOPReview


def test_one_explicit_approval_survives_new_unrated_trials(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Nama SOP: LAYANAN CONTOH\nPersyaratan: surat pengantar. Prosedur: serahkan berkas.')
    review = SOPReview(engine)
    detail = review.detail(run['document_id'])
    identifier, version = detail['document_id'], detail['version_id']
    review.decide(identifier, version, 'content_ok', 'fixture-operator')
    confirm_fixture_metadata(review, review.detail(identifier))
    approved = review.decide(identifier, version, 'approve', 'fixture-operator')
    assert approved['status'] == 'Aktif'
    review.record_trial(identifier, version, 'time_cost', 'Berapa biayanya?',
                        {'response': 'Tidak tersedia', 'evidence': []}, 'fixture-operator')
    refreshed = SOPReview(engine_at(tmp_path / 'chat.db')).detail(identifier)
    assert refreshed['status'] == 'Aktif'
    assert refreshed['approval']['event_id'] == approved['approval']['event_id']


def test_prepare_persists_detected_metadata_without_approving_or_inventing_absence(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Nama S.O.P LAYANAN CONTOH\nNomor SOP ABC-07\nInstansi: Dinas Contoh\nPersyaratan: Surat Pengantar.')
    review = SOPReview(engine)
    detail = review.detail(run['document_id'])
    prepared = review.prepare(detail['document_id'], detail['version_id'])
    assert prepared['official_metadata']['sop_number']['value'] == 'ABC-07'
    assert prepared['official_metadata']['effective_on']['status'] == 'unreadable'
    assert prepared['metadata_origin'] == 'system'
    assert prepared['metadata_confirmed'] is False
    assert prepared['approval'] is None
    assert prepared['operator_status'] == 'Siap disetujui'
    refreshed = SOPReview(engine_at(tmp_path / 'chat.db')).detail(detail['document_id'])
    assert refreshed['official_metadata'] == prepared['official_metadata']
    assert refreshed['system_summary']['material_binding'] == prepared['material_binding']
    again = review.prepare(detail['document_id'], detail['version_id'])
    assert len(again['events']) == len(prepared['events'])
    approved = review.decide(detail['document_id'], detail['version_id'], 'approve', 'fixture-operator')
    assert approved['status'] == 'Aktif'
    assert approved['metadata_confirmed'] is True


def test_preparation_is_authenticated_version_bound_and_reads_back_same_metadata(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.knowledge_pipeline import create_knowledge_pipeline_router, get_knowledge_engine
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'fixture-only')
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Nama SOP: LAYANAN CONTOH\nNomor SOP: TEST-09\nPersyaratan: surat pengantar.')
    async def run_sync(fn, *args, **kwargs): return fn(*args)
    app = FastAPI(); app.include_router(create_knowledge_pipeline_router(run_sync), prefix='/v1')
    app.dependency_overrides[get_knowledge_engine] = lambda: engine
    with TestClient(app) as client:
        url = '/v1/knowledge/pipeline/reviews/' + run['document_id']
        headers = {'X-Admin-Token': 'fixture-only'}
        version = client.get(url, headers=headers).json()['version_id']
        assert client.post(url + '/prepare', json={'version_id': version}).status_code == 403
        assert client.post(url + '/prepare', headers=headers, json={'version_id': '0' * 64}).status_code == 409
        prepared = client.post(url + '/prepare', headers=headers, json={'version_id': version})
        assert prepared.status_code == 200, prepared.text
        assert client.get(url, headers=headers).json()['official_metadata'] == prepared.json()['official_metadata']
        assert prepared.json()['approval'] is None
        decision = {'version_id': version, 'action': 'approve'}
        assert client.post(url + '/decision', headers=headers, json=decision).status_code == 422
        assert client.post(url + '/decision', headers=headers, json={**decision, 'material_binding': '0' * 64}).status_code == 409
        approved = client.post(url + '/decision', headers=headers, json={**decision, 'material_binding': prepared.json()['material_binding']})
        assert approved.status_code == 200, approved.text
        assert approved.json()['status'] == 'Aktif'


from test_v1_sop_boundary import api, SESSION


def test_chat_rejects_stale_approved_handoff_before_model(api, monkeypatch):
    import asyncio, pytest
    from fastapi import HTTPException
    monkeypatch.setattr(SOPReview, 'is_pilot', lambda *args: True)
    monkeypatch.setattr(SOPReview, 'detail', lambda *args: {'status': 'Aktif', 'version_id': 'b' * 64})
    request = api.ns['ChatRequest'](session_id=SESSION, user_input='Apa kelengkapannya?',
                document_ids=['internal-source'], document_version='a' * 64)
    with pytest.raises(HTTPException) as error:
        asyncio.run(api.ns['chat'](request, x_admin_token='operator-fixture'))
    assert error.value.status_code == 409
    assert error.value.detail == 'CHAT_SOURCE_VERSION_CHANGED'
    assert api.calls['model'] == 0


def test_optional_undetected_fields_need_no_operator_notes(tmp_path):
    from test_sop_metadata import metadata_payload
    engine = engine_at(tmp_path / 'chat.db')
    identifier = engine.process_knowledge_source('sop.txt', b'Nama SOP: LAYANAN CONTOH\nPersyaratan surat pengantar.')['document_id']
    review = SOPReview(engine); detail = review.detail(identifier)
    metadata = metadata_payload('LAYANAN CONTOH')
    metadata['unit'] = {'status':'unreadable','value':None,'note':''}
    saved = review.confirm_metadata(identifier, detail['version_id'], metadata, 'fixture-operator')
    assert saved['official_metadata']['unit']['note'] == ''


def test_new_metadata_snapshot_requires_fresh_explicit_approval(tmp_path):
    from test_sop_metadata import metadata_payload
    engine = engine_at(tmp_path / 'chat.db')
    identifier = engine.process_knowledge_source('sop.txt', b'Nama SOP: LAYANAN CONTOH\nPersyaratan surat pengantar.')['document_id']
    review = SOPReview(engine); detail = review.prepare(identifier, review.detail(identifier)['version_id'])
    approved = review.decide(identifier, detail['version_id'], 'approve', 'fixture-operator')
    changed = metadata_payload('LAYANAN YANG DIKOREKSI')
    saved = review.confirm_metadata(identifier, detail['version_id'], changed, 'fixture-operator',
                                    expected_event_id=approved['metadata_event_id'])
    assert saved['status'] != 'Aktif'
    assert saved['approval']['event_id'] == approved['approval']['event_id']
    prepared = review.prepare(identifier, detail['version_id'])
    assert prepared['status'] == 'Siap disetujui'
    assert prepared['approval']['event_id'] == approved['approval']['event_id']


def test_stale_metadata_display_cannot_authorize_a_new_snapshot(tmp_path, monkeypatch):
    from test_sop_metadata import metadata_payload
    import pytest
    engine = engine_at(tmp_path / 'chat.db')
    identifier = engine.process_knowledge_source('sop.txt', b'Nama SOP: LAYANAN CONTOH\nPersyaratan surat pengantar.')['document_id']
    review = SOPReview(engine); shown = review.prepare(identifier, review.detail(identifier)['version_id'])
    changed = review.confirm_metadata(identifier, shown['version_id'], metadata_payload('JUDUL DIKOREKSI'),
                                      'fixture-operator', expected_event_id=shown['metadata_event_id'])
    with pytest.raises(ValueError, match='Metadata berubah'):
        review.decide(identifier, shown['version_id'], 'approve', 'fixture-operator',
                      expected_material_binding=shown['material_binding'])
    assert review.detail(identifier)['approval'] is None
