"""Official metadata is a human, source/version-bound review, not model output."""
import pytest
from test_selected_pdf_chat import approved_pdf as approved_pdf
from test_sop_review import engine_at

from app.knowledge.sop_review import SOPReview


def metadata_payload(title='PERMOHONAN DATA PRIBADI'):
    absent = {'status': 'not_stated', 'value': None, 'note': 'Tidak tercantum pada sumber uji.'}
    return {'schema_version': 1, 'logical_sop_id': 'LAYANAN-DATA-PRIBADI',
            'official_title': {'status': 'present', 'value': title},
            **{key: dict(absent) for key in ('institution', 'unit', 'sop_number', 'jurisdiction',
                'issued_on', 'effective_on', 'expires_on', 'revision')},
            'validity': 'not_confirmed', 'validity_note': 'Keberlakuan belum dikonfirmasi.'}


def ready_review(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('scan.txt', b'Nama SOP: PERMOHONAN DATA PRIBADI\nPersyaratan surat permohonan.')
    review = SOPReview(engine)
    doc = review.detail(run['document_id'])
    identifier, version = doc['document_id'], doc['version_id']
    review.decide(identifier, version, 'content_ok', 'operator')
    for case in doc['required_cases']:
        trial = review.record_trial(identifier, version, case, 'Pertanyaan', {'response': 'Fixture'}, 'operator')
        review.rate(identifier, version, trial['trial_id'], True, '', 'operator')
    return review, identifier, version


def test_metadata_required_and_revision_bound_without_rewriting_source(tmp_path):
    review, identifier, version = ready_review(tmp_path)
    before = review.engine.rag.get_document_info(identifier)
    assert review.detail(identifier)['can_approve'] is False
    with pytest.raises(ValueError):
        review.decide(identifier, version, 'approve', 'operator')
    detail = review.confirm_metadata(identifier, version, metadata_payload(), 'shared-admin-token')
    assert detail['official_metadata']['official_title']['value'] == 'PERMOHONAN DATA PRIBADI'
    assert detail['metadata_confirmed'] is True
    approved = review.decide(identifier, version, 'approve', 'operator')
    assert approved['status'] == 'Aktif'
    reopened = SOPReview(engine_at(tmp_path / 'chat.db'))
    assert reopened.detail(identifier)['metadata_confirmed'] is True
    assert reopened.detail(identifier)['status'] == 'Aktif'
    assert reopened.engine.rag.get_document_info(identifier).source == before.source
    # Editing metadata preserves prior decisions but invalidates their binding.
    changed = metadata_payload()
    changed['unit'] = {'status': 'present', 'value': 'Unit pelayanan'}
    updated = reopened.confirm_metadata(identifier, version, changed, 'operator',
        expected_event_id=reopened.detail(identifier)['metadata_event_id'])
    assert updated['approval']['event_id'] == approved['approval']['event_id']
    assert updated['status'] != 'Aktif'
    with pytest.raises(ValueError, match='Versi berubah'):
        reopened.confirm_metadata(identifier, '0' * 64, changed, 'operator')


def test_missing_metadata_is_explicit_and_title_cannot_be_filename_fallback(tmp_path):
    review, identifier, version = ready_review(tmp_path)
    data = metadata_payload()
    data['official_title'] = {'status': 'not_stated', 'note': 'Tidak terbaca'}
    with pytest.raises(ValueError):
        review.confirm_metadata(identifier, version, data, 'operator')


@pytest.mark.parametrize('field,change', [
    ('institution', {'status': 'not_stated', 'value': 'Nama rekaan', 'note': 'Tidak ada'}),
    ('unit', {'status': 'unreadable', 'note': '   '}),
    ('effective_on', {'status': 'present', 'value': '2026-02-30'}),
    ('official_title', {'status': 'present', 'value': '   '}),
])
def test_invalid_official_fields_cannot_be_saved(tmp_path, field, change):
    review, identifier, version = ready_review(tmp_path)
    data = metadata_payload()
    data[field] = change
    with pytest.raises(ValueError):
        review.confirm_metadata(identifier, version, data, 'operator')
    assert review.detail(identifier)['official_metadata'] is None


@pytest.mark.parametrize('field,value', [('effective_on', '2099-01-01'), ('expires_on', '2000-01-01')])
def test_source_dates_block_publication_without_discarding_review(tmp_path, field, value):
    review, identifier, version = ready_review(tmp_path)
    data = metadata_payload()
    data[field] = {'status': 'present', 'value': value}
    detail = review.confirm_metadata(identifier, version, data, 'operator')
    assert detail['metadata_confirmed'] is True
    assert detail['can_approve'] is False
    with pytest.raises(ValueError):
        review.decide(identifier, version, 'approve', 'operator')


def test_metadata_edit_requires_current_lease_and_keeps_audit(tmp_path):
    review, identifier, version = ready_review(tmp_path)
    first = review.confirm_metadata(identifier, version, metadata_payload(), 'operator')
    with pytest.raises(ValueError, match='Metadata berubah'):
        review.confirm_metadata(identifier, version, metadata_payload(), 'operator')
    assert review.detail(identifier)['metadata_event_id'] == first['metadata_event_id']


def test_same_service_cannot_publish_two_active_revisions_or_create_a_cycle(tmp_path):
    review, first_id, first_version = ready_review(tmp_path)
    first = review.confirm_metadata(first_id, first_version, metadata_payload(), 'operator')
    review.decide(first_id, first_version, 'approve', 'operator')
    run = review.engine.process_knowledge_source('revision.txt', b'Persyaratan surat baru. Prosedur pelayanan versi revisi.')
    second_id = run['document_id']
    second = review.detail(second_id)
    second_version = second['version_id']
    data = metadata_payload()
    data['replaces_document_id'] = first_id
    review.confirm_metadata(second_id, second_version, data, 'operator')
    review.decide(second_id, second_version, 'content_ok', 'operator')
    for case in second['required_cases']:
        trial = review.record_trial(second_id, second_version, case, 'Pertanyaan', {'response': 'Fixture'}, 'operator')
        review.rate(second_id, second_version, trial['trial_id'], True, '', 'operator')
    with pytest.raises(ValueError, match='masih aktif'):
        review.decide(second_id, second_version, 'approve', 'operator')
    cyclic = metadata_payload()
    cyclic['replaces_document_id'] = second_id
    with pytest.raises(ValueError, match='melingkar'):
        review.confirm_metadata(first_id, first_version, cyclic, 'operator', expected_event_id=first['metadata_event_id'])
    review.decide(first_id, first_version, 'revoke', 'operator', 'Digantikan revisi terbaru')
    assert review.decide(second_id, second_version, 'approve', 'operator')['status'] == 'Aktif'
    changed_identity = metadata_payload()
    changed_identity['logical_sop_id'] = 'OTHER-SERVICE'
    with pytest.raises(ValueError, match='sudah dirujuk'):
        review.confirm_metadata(first_id, first_version, changed_identity, 'operator',
            expected_event_id=first['metadata_event_id'])
    assert review.detail(second_id)['status'] == 'Aktif'
    # A predecessor source change cannot leave the revision relationship green
    # until its new metadata has been checked again.
    previous = review.engine.rag.get_document_info(first_id)
    review.engine.rag._store.store_document_info(previous.model_copy(update={'title': 'Sumber berubah'}))
    assert review.detail(second_id)['status'] == 'Hubungan revisi perlu diperiksa'
    with pytest.raises(ValueError):
        review.decide(second_id, second_version, 'approve', 'operator')


@pytest.mark.parametrize('page', [None, 999])
def test_pdf_metadata_requires_an_existing_physical_page(approved_pdf, page):
    engine, identifier = approved_pdf
    review = SOPReview(engine)
    detail = review.detail(identifier)
    data = metadata_payload()
    data['official_title']['page_number'] = page
    with pytest.raises(ValueError, match=r'[Hh]alaman'):
        review.confirm_metadata(identifier, detail['version_id'], data, 'operator',
            expected_event_id=detail['metadata_event_id'])
    assert review.detail(identifier)['status'] == 'Aktif'
