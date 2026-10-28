"""Operator review through its persistent public interface; fixture inference only."""
import pytest

from app.knowledge.engine import KnowledgeEngine
from app.knowledge.rag import RAG
from app.knowledge.schemas import KnowledgeBaseConfig
from app.knowledge.store import SQLiteVectorStore
from app.knowledge.sop_review import SOPReview


def engine_at(path):
    return KnowledgeEngine(rag=RAG(config=KnowledgeBaseConfig(embedding_model='fixture', embedding_dimension=3),
        vector_store=SQLiteVectorStore(str(path)), embedding_func=lambda text: [1., 0., 0.]))


def test_approval_requires_content_and_every_required_trial_and_survives_restart(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan: Surat Permohonan. Prosedur: serahkan berkas. Waktu: 3 hari kerja.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])
    version = doc['version_id']
    with pytest.raises(ValueError):
        review.decide(doc['document_id'], version, 'approve', 'admin-token', '')
    review.decide(doc['document_id'], version, 'content_ok', 'admin-token', '')
    for case in doc['required_cases']:
        trial = review.record_trial(doc['document_id'], version, case, 'Pertanyaan', {'response': 'Jawaban fixture'}, 'admin-token')
        review.rate(doc['document_id'], version, trial['trial_id'], True, '', 'admin-token')
    approved = review.decide(doc['document_id'], version, 'approve', 'admin-token', '')
    assert approved['status'] == 'Aktif'
    assert SOPReview(engine_at(tmp_path / 'chat.db')).detail(doc['document_id'])['status'] == 'Aktif'
    assert review.decide(doc['document_id'], version, 'approve', 'admin-token', '')['approval'] == approved['approval']
    review.record_trial(doc['document_id'], version, 'requirements', 'Pertanyaan baru', {'response': 'Baru'}, 'admin-token')
    assert review.detail(doc['document_id'])['status'] != 'Aktif'
    failed = review.detail(doc['document_id'])['trials'][-1]
    problem = review.rate(doc['document_id'], version, failed['trial_id'], False, 'Jawaban belum tepat', 'admin-token')['problems'][0]
    replacement = review.record_trial(doc['document_id'], version, 'requirements', 'Pertanyaan koreksi', {'response': 'Koreksi'}, 'admin-token')
    review.rate(doc['document_id'], version, replacement['trial_id'], True, '', 'admin-token')
    result = review.decide(doc['document_id'], version, 'resolve', 'admin-token', 'Jawaban pengganti telah diperiksa', problem['event_id'])
    assert result['status'] == 'Siap disetujui'
    assert next(t for t in result['trials'] if t['trial_id'] == failed['trial_id'])['rating']['ok'] is False


def test_problem_requires_note_and_cannot_inherit_approval(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan layanan dalam SOP uji. Serahkan surat permohonan kepada petugas.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])
    with pytest.raises(ValueError):
        review.decide(doc['document_id'], doc['version_id'], 'problem', 'admin-token', '')
    result = review.decide(doc['document_id'], doc['version_id'], 'problem', 'admin-token', 'Ekstraksi keliru')
    assert result['status'] == 'Ada masalah'
    assert result['events'][-1]['note'] == 'Ekstraksi keliru'


def test_session_cannot_switch_document_or_version_and_changed_source_needs_review(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    first = engine.process_knowledge_source('first.txt', b'Persyaratan pertama surat permohonan untuk layanan warga dalam dokumen ini.')
    second = engine.process_knowledge_source('second.txt', b'Persyaratan kedua surat pengantar untuk layanan warga dalam dokumen ini.')
    review = SOPReview(engine)
    a, b = review.detail(first['document_id']), review.detail(second['document_id'])
    review.bind_session('session', a['document_id'], a['version_id'])
    with pytest.raises(ValueError):
        review.bind_session('session', b['document_id'], b['version_id'])
    review.decide(a['document_id'], a['version_id'], 'content_ok', 'admin-token')
    # Developer correction via the store's public document interface, not SQL.
    previous = engine.rag.get_document_info(a['document_id'])
    engine.rag._store.store_document_info(previous.model_copy(update={'title': 'Versi baru',
        'source': 'Persyaratan berubah menjadi surat lain. Prosedur baru perlu diperiksa oleh operator.'}))
    newer = review.detail(a['document_id'])
    assert newer['version_id'] != a['version_id']
    assert newer['content_ok'] is False
    assert newer['approval'] is None


def test_pilot_is_private_to_trial_before_first_human_decision(tmp_path):
    from app.security.v1_knowledge import V1KnowledgeBoundary
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan layanan: surat permohonan. Prosedur pelayanan tersedia pada SOP ini.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])
    review.bind_session('trial', doc['document_id'], doc['version_id'])
    assert review.is_pilot(doc['document_id'])
    normal = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[doc['document_id']])
    assert normal.search_knowledge('Persyaratan') == []
    assert V1KnowledgeBoundary(engine, operator=True, provider='ollama').search_knowledge('Persyaratan') == []
    trial = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[doc['document_id']], sop_version=doc['version_id'], review_trial=True)
    assert trial.search_knowledge('Persyaratan')[0].source == doc['text']


def test_content_check_event_persists_with_optional_trial_id_column(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan: surat permohonan. Prosedur: serahkan berkas.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])

    # Existing operator databases can have this nullable extension column.
    # Named-column insertion must remain compatible with that schema.
    with engine._pipeline_db() as conn:
        conn.execute('ALTER TABLE sop_review_events ADD COLUMN trial_id TEXT')

    saved = review.decide(doc['document_id'], doc['version_id'], 'content_ok', 'operator-fixture')
    refreshed = SOPReview(engine_at(tmp_path / 'chat.db')).detail(doc['document_id'])

    assert saved['content_ok'] is True
    assert refreshed['content_ok'] is True
    assert any(event['kind'] == 'content_ok' for event in refreshed['events'])
