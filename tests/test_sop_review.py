"""Operator review through its persistent public interface; fixture inference only."""
import pytest

from app.knowledge.engine import KnowledgeEngine
from app.knowledge.rag import RAG
from app.knowledge.schemas import KnowledgeBaseConfig
from app.knowledge.sop_review import SOPReview
from app.knowledge.store import SQLiteVectorStore


def engine_at(path):
    return KnowledgeEngine(rag=RAG(config=KnowledgeBaseConfig(embedding_model='fixture', embedding_dimension=3),
        vector_store=SQLiteVectorStore(str(path)), embedding_func=lambda text: [1., 0., 0.]))


def confirm_fixture_metadata(review, detail):
    """Synthetic operator review for fixtures only; never used in runtime."""
    if detail.get('metadata_confirmed'):
        return detail
    absent = {'status': 'not_stated', 'note': 'Tidak tercantum pada sumber fixture.'}
    title = {'status': 'present', 'value': detail['title']}
    if detail['source_type'] == '.pdf':
        title['page_number'] = 1
    data = {'logical_sop_id': detail['document_id'], 'official_title': title,
            **{key: dict(absent) for key in ('institution', 'unit', 'sop_number', 'jurisdiction',
                'issued_on', 'effective_on', 'expires_on', 'revision')},
            'validity': 'not_confirmed', 'validity_note': 'Fixture; bukan konfirmasi hukum.'}
    return review.confirm_metadata(detail['document_id'], detail['version_id'], data, 'fixture-reviewer')


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
    confirm_fixture_metadata(review, review.detail(doc['document_id']))
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


@pytest.mark.parametrize('action,status', [('reject', 'Ditolak'), ('defer', 'Ditunda'), ('revoke', 'Dicabut')])
def test_publication_decision_blocks_retrieval_and_cached_answer_until_new_approval(tmp_path, action, status):
    from fastapi import HTTPException

    from app.security.v1_knowledge import V1KnowledgeBoundary

    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan: surat permohonan. Prosedur: serahkan berkas.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])
    identifier, version = doc['document_id'], doc['version_id']
    review.decide(identifier, version, 'content_ok', 'operator')
    for case in doc['required_cases']:
        trial = review.record_trial(identifier, version, case, 'Pertanyaan uji', {'response': 'Jawaban uji'}, 'operator')
        review.rate(identifier, version, trial['trial_id'], True, '', 'operator')
    confirm_fixture_metadata(review, review.detail(identifier))
    approved = review.decide(identifier, version, 'approve', 'operator')
    boundary = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[identifier])
    assert boundary.search_knowledge('Persyaratan')
    answer = {'evidence': [{'document_id': identifier}]}
    bindings = boundary.source_versions(answer)
    boundary.validate_response(answer, bindings)

    with pytest.raises(ValueError, match='Alasan'):
        review.decide(identifier, version, action, 'operator', '   ')
    result = review.decide(identifier, version, action, 'operator', 'Keputusan pemeriksaan uji')
    assert result['status'] == status
    reopened = SOPReview(engine_at(tmp_path / 'chat.db'))
    assert reopened.detail(identifier)['status'] == status
    assert reopened.detail(identifier)['publication_decision']['principal'] == 'operator'
    assert boundary.search_knowledge('Persyaratan') == []
    assert V1KnowledgeBoundary(engine, operator=True, provider='ollama').search_knowledge('Persyaratan') == []
    with pytest.raises(HTTPException) as error:
        boundary.validate_response(answer, bindings)
    assert error.value.status_code == 409
    with pytest.raises(ValueError, match='Versi berubah'):
        review.decide(identifier, '0' * 64, 'approve', 'operator')

    reapproved = reopened.decide(identifier, version, 'approve', 'operator', 'Diperiksa kembali')
    assert reapproved['status'] == 'Aktif'
    assert reapproved['approval']['event_id'] != approved['approval']['event_id']
    assert any(event['kind'] == action for event in reapproved['events'])
    assert boundary.search_knowledge('Persyaratan')


def test_unapproved_document_cannot_be_revoked(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan: surat permohonan. Prosedur: serahkan berkas.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])
    with pytest.raises(ValueError, match='aktif'):
        review.decide(doc['document_id'], doc['version_id'], 'revoke', 'operator', 'Cabut sumber')


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


def test_deferred_document_stays_blocked_after_reload_and_content_check(tmp_path):
    from app.security.v1_knowledge import V1KnowledgeBoundary

    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan: surat permohonan. Prosedur: serahkan berkas.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])
    result = review.decide(doc['document_id'], doc['version_id'], 'defer', 'operator', 'Periksa tabel biaya')
    assert result['status'] == 'Ditunda'
    reopened = SOPReview(engine_at(tmp_path / 'chat.db'))
    assert reopened.detail(doc['document_id'])['status'] == 'Ditunda'
    checked = reopened.decide(doc['document_id'], doc['version_id'], 'content_ok', 'operator')
    assert checked['status'] == 'Ditunda'
    assert checked['publication_decision']['note'] == 'Periksa tabel biaya'
    assert V1KnowledgeBoundary(engine, operator=True, provider='ollama').search_knowledge('Persyaratan') == []


def test_correction_retains_category_question_answer_revision_and_resolution(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan: surat permohonan. Prosedur: serahkan berkas.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])
    identifier, version = doc['document_id'], doc['version_id']
    trial = review.record_trial(identifier, version, 'requirements', 'Apa berkasnya?',
        {'response': 'Surat lain', 'evidence': [{'document_id': identifier, 'pages': [1]}]}, 'operator')
    result = review.rate(identifier, version, trial['trial_id'], False, 'Sumber salah dipilih', 'operator', category='retrieval')
    problem = result['problems'][0]
    assert problem['category'] == 'retrieval'
    reopened = SOPReview(engine_at(tmp_path / 'chat.db'))
    saved = reopened.detail(identifier)
    assert saved['trials'][0]['question'] == 'Apa berkasnya?'
    assert saved['trials'][0]['answer']['response'] == 'Surat lain'
    assert saved['trials'][0]['rating']['category'] == 'retrieval'
    fixed = reopened.decide(identifier, version, 'resolve', 'operator', 'Sumber telah diperbaiki', problem['event_id'])
    assert fixed['problems'] == []
    assert fixed['trials'][0]['rating']['ok'] is False
    assert fixed['trials'][0]['rating']['category'] == 'retrieval'

