"""V1 chat contract; provider fixture, never a live-model claim."""
import pytest
from test_ncp_v1_chat_contract import execute
from test_v1_langgraph import fixture


@pytest.mark.parametrize('question', ['Apa itu KTP-el?', 'KTp-Elektronik?', 'ktp-el', 'Secara umum, apa itu KTP-el?'])
def test_topic_definition_skips_retrieval_even_with_selected_document(question):
    parts = fixture(empty=False, answer='KTP-el adalah kartu identitas penduduk elektronik.')
    def unavailable(*args, **kwargs):
        raise RuntimeError('embedding unavailable')
    parts[2]['knowledge'].search_knowledge = unavailable
    result = execute(parts, question, document_ids=['selected-sop'])
    assert result['response'] == 'KTP-el adalah kartu identitas penduduk elektronik.'
    assert result['grounding']['reason'] == 'not_evaluated'
    assert result['evidence'] == []
    assert parts[4].calls == 1


def test_explicit_sop_request_cannot_be_answered_as_general_chat():
    parts = fixture(empty=True, answer='Jawaban umum yang tidak bersumber.')
    result = execute(parts, 'Menurut SOP yang saya unggah, kapan selesai?')
    assert result['grounding']['reason'] == 'no_evidence'
    assert result['response'] != 'Jawaban umum yang tidak bersumber.'


def test_retrieval_failure_is_distinct_from_empty_sources():
    from fastapi import HTTPException
    parts = fixture(empty=True)
    def unavailable(*args, **kwargs):
        raise RuntimeError('private embedding failure')
    parts[2]['knowledge'].search_knowledge = unavailable
    with pytest.raises(HTTPException) as failure:
        execute(parts, 'Menurut SOP ini, berapa biaya dalam euro?', document_ids=['selected-sop'])
    assert failure.value.status_code == 503
    assert failure.value.detail == 'RETRIEVAL_UNAVAILABLE'
    assert parts[4].calls == 0
