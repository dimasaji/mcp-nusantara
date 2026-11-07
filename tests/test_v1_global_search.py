"""Global search and selection through the V1 chat executor, with fixture inference."""
import pytest
from fastapi import HTTPException

from test_v1_service_dialogue import ask, setup


def test_search_result_number_selects_document_and_preserves_followup_scope():
    parts = setup()
    results = ask(parts, '/cari SOP data pribadi')
    assert '1. SOP Permohonan Data Pribadi' in results['response']
    assert '\n1.' in results['response']
    assert '\\n' not in results['response']
    selected = ask(parts, '1')
    assert 'Dokumen terpilih: SOP Permohonan Data Pribadi' in selected['response']
    context = parts[2]['gates'].memory.service_context('dialogue')
    assert context['document_id'] == 'service-private'
    assert 'search_results' not in context
    parts[4].answer = 'Menurut SOP: 3 Hari Kerja.'
    duration = ask(parts, 'Berapa lama?')
    assert '3 hari kerja' in duration['response'].lower()
    assert duration['evidence'][0]['document_id'] == 'service-private'


def test_search_deduplicates_documents_and_invalid_selection_retains_results():
    parts = setup()
    item = parts[2]['knowledge'].search_knowledge('fixture')[0]
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [item, item]
    result = ask(parts, '/cari SOP data pribadi')
    assert result['response'].count('SOP Permohonan Data Pribadi') == 1
    invalid = ask(parts, '2')
    assert 'Nomor hasil tidak tersedia' in invalid['response']
    assert 'Dokumen terpilih' in ask(parts, '1')['response']


def test_search_failure_does_not_claim_there_are_no_documents():
    parts = setup()
    def unavailable(*args, **kwargs):
        raise RuntimeError('fixture retrieval unavailable')
    parts[2]['knowledge'].search_knowledge = unavailable
    with pytest.raises(HTTPException) as error:
        ask(parts, '/cari SOP data pribadi')
    assert error.value.status_code == 503
    assert error.value.detail == 'RETRIEVAL_UNAVAILABLE'
    assert parts[4].calls == 0


def test_empty_search_clears_old_selection_results_without_calling_model():
    parts = setup()
    ask(parts, '/cari SOP data pribadi')
    result = ask(parts, '/cari SOP')
    assert result['response'] == 'Ketik /cari SOP diikuti nama atau topik layanan.'
    assert parts[2]['gates'].memory.service_context('dialogue') == {}
    assert parts[4].calls == 0


def test_search_in_explicit_document_scope_keeps_its_catalog_response():
    from test_golden_sop_chat import execute

    parts = setup()
    result = execute(parts, '/cari SOP data pribadi', document_ids=['service-private'])
    assert '1. SOP Permohonan Data Pribadi' in result['response']
    selected = execute(parts, '1', document_ids=['service-private'])
    assert 'Dokumen terpilih: SOP Permohonan Data Pribadi' in selected['response']


def test_selected_result_is_scoped_before_competing_documents_can_displace_it():
    parts = setup()
    selected = parts[2]['knowledge'].search_knowledge('fixture')[0]
    ask(parts, '/cari SOP data pribadi')
    ask(parts, '1')
    def search(query, top_k=None, filter=None):
        # Another approved service wins global top-k; selected-document search
        # still retrieves the requested source before candidate ranking.
        return [selected] if filter == {'document_ids': ['service-private']} else []
    parts[2]['knowledge'].search_knowledge = search
    parts[4].answer = 'Menurut SOP: 3 Hari Kerja.'
    duration = ask(parts, 'Berapa lama?')
    assert '3 hari kerja' in duration['response'].lower()
    assert duration['evidence'][0]['document_id'] == 'service-private'


def test_oversized_numeric_selection_is_invalid_and_preserves_results():
    parts = setup()
    ask(parts, '/cari SOP data pribadi')
    invalid = ask(parts, '9' * 5000)
    assert 'Nomor hasil tidak tersedia' in invalid['response']
    assert 'Dokumen terpilih' in ask(parts, '1')['response']
