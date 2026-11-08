"""HTTP progress contracts through real review/storage with fixture embeddings."""
from pathlib import Path

from test_knowledge_pipeline_api import AUTH, STATUS, upload
from test_sop_review import confirm_fixture_metadata

from app.api.knowledge_pipeline import get_knowledge_engine
from app.knowledge.document_tools import DocumentTools
from app.knowledge.sop_review import SOPReview

pytest_plugins = ('test_knowledge_pipeline_api',)


def test_all_documents_have_progress(client):
    ids = [upload(client, f'Persyaratan SOP {name}: Surat Permohonan kepada petugas.'.encode(), f'{name}.txt').json()['document_id']
           for name in ('CAPIL-01', 'DAFDUK-02')]
    assert client.get(STATUS).status_code == 403
    body = client.get(STATUS, headers=AUTH).json()
    docs = {doc['document_id']: doc for doc in body['documents']}
    for identifier in ids:
        assert docs[identifier]['review_status'] == 'Menunggu pemeriksaan isi'
        assert docs[identifier]['workflow']['state'] == 'REVIEW_REQUIRED'
        assert docs[identifier]['workflow']['stages']['cleaning'] == 'SUCCEEDED'
    assert body['sop_summary']['total'] == 2


def ready_document(client):
    run = upload(client, b'Persyaratan: Surat Permohonan. Prosedur: serahkan kepada petugas.', 'layanan.txt').json()
    owner = client.app.dependency_overrides[get_knowledge_engine]()
    review = SOPReview(owner)
    identifier = run['document_id']
    review.decide(identifier, review.detail(identifier)['version_id'], 'content_ok', 'fixture')
    confirm_fixture_metadata(review, review.detail(identifier))
    return review, identifier


def test_approval_and_revocation_are_current(client):
    review, identifier = ready_document(client)
    assert client.get(STATUS, headers=AUTH).json()['sop_summary']['counts']['APPROVAL_REQUIRED'] == 1
    review.decide(identifier, review.detail(identifier)['version_id'], 'approve', 'fixture')
    body = client.get(STATUS, headers=AUTH).json()
    assert body['sop_summary']['counts']['ACTIVE'] == 1
    assert body['documents'][0]['workflow']['next_action'] == 'chat'
    review.decide(identifier, review.detail(identifier)['version_id'], 'revoke', 'fixture', 'Periksa revisi')
    body = client.get(STATUS, headers=AUTH).json()
    assert body['sop_summary']['counts']['ACTIVE'] == 0
    assert body['sop_summary']['counts']['BLOCKED'] == 1
    assert body['documents'][0]['workflow']['next_action'] != 'chat'


def test_missing_source_blocks_only_that_document(client):
    runs = [upload(client, f'Persyaratan layanan {name}: Surat Permohonan kepada petugas.'.encode(), f'{name}.txt').json()
            for name in ('pertama', 'kedua')]
    Path(runs[0]['source_path']).unlink()
    body = client.get(STATUS, headers=AUTH).json()
    docs = {doc['document_id']: doc for doc in body['documents']}
    assert docs[runs[0]['document_id']]['workflow']['state'] == 'BLOCKED'
    assert docs[runs[1]['document_id']]['workflow']['state'] == 'REVIEW_REQUIRED'


def test_revocation_during_projection_cannot_remain_active(client, monkeypatch):
    review, identifier = ready_document(client)
    review.decide(identifier, review.detail(identifier)['version_id'], 'approve', 'fixture')
    original = DocumentTools.status
    revoked = False

    def interleaved(self, document_id, version=None):
        nonlocal revoked
        result = original(self, document_id, version)
        if document_id == identifier and not revoked:
            revoked = True
            review.decide(identifier, review.detail(identifier)['version_id'], 'revoke', 'fixture', 'Revisi berubah')
        return result

    monkeypatch.setattr(DocumentTools, 'status', interleaved)
    body = client.get(STATUS, headers=AUTH).json()
    assert body['documents'][0]['workflow']['state'] == 'BLOCKED'
    assert body['documents'][0]['workflow']['next_action'] != 'chat'


def test_failed_sources_count_latest_attempt_beyond_history_page(client):
    upload(client, b'x', 'gagal.txt')
    upload(client, b'x', 'gagal-lagi.txt')
    for _ in range(102):
        upload(client, b'Persyaratan: Surat Permohonan kepada petugas layanan warga.', 'layanan.txt')
    body = client.get(STATUS, headers=AUTH).json()
    assert len(body['runs']) == 100
    assert all(run['status'] != 'FAILED' for run in body['runs'])
    assert len(body['sop_summary']['failed_sources']) == 1
    assert body['sop_summary']['failed_sources'][0]['filename'] == 'gagal-lagi.txt'
    assert body['sop_summary']['total'] == 1


def test_unreadable_review_is_isolated_and_logs_no_source_text(client, monkeypatch, caplog):
    run = upload(client, b'Persyaratan layanan: Surat Permohonan kepada petugas warga.', 'layanan.txt').json()
    original = SOPReview.detail

    def broken(self, identifier, **kwargs):
        if identifier == run['document_id']:
            raise ValueError('PRIVATE_SOURCE_CONTENT')
        return original(self, identifier, **kwargs)

    monkeypatch.setattr(SOPReview, 'detail', broken)
    body = client.get(STATUS, headers=AUTH).json()
    assert body['sop_summary']['counts']['UNKNOWN'] == 1
    assert body['documents'][0]['workflow']['next_action'] != 'chat'
    assert 'ValueError' in caplog.text
    assert 'PRIVATE_SOURCE_CONTENT' not in caplog.text
