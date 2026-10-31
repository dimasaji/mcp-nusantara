"""Chat regressions with real retrieval/grounding and an offline provider."""
import asyncio
from types import SimpleNamespace

import pytest
from test_effective_rag_profile import FakeStore, make_rag
from test_v1_langgraph import fixture

from app.knowledge.engine import KnowledgeEngine


def run_document_chat(question, answer, *, pilot=False, source=None, metadata=None):
    parts = fixture(answer=answer)
    source = source or 'Persyaratan: Pemohon menyerahkan Surat Permohonan kepada petugas.'
    evidence = SimpleNamespace(document_id='selected', title='SOP contoh', source=source,
        chunk=source, score=1., metadata={'citation_pages': [1], **(metadata or {})})
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [evidence]
    request = SimpleNamespace(user_input=question, session_id='fixture-session',
        document_ids=['selected'], sop_version='a' * 64 if pilot else None)
    core = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    return parts[3](core.payload, intent_name=core.intent_name)


def test_supported_sop_paraphrase_reaches_chat_without_replacing_the_answer():
    answer = 'Persyaratan: Pemohon menyampaikan Surat Permohonan kepada petugas.'
    public = run_document_chat('Apa persyaratan SOP ini?', answer, pilot=True)
    assert public['response'] == answer
    assert public['grounding']['grounded']
    assert public['evidence'][0]['pages'] == [1]


def test_supported_procedure_action_paraphrase_reaches_chat():
    answer = 'Prosedur: mengecek data.'
    public = run_document_chat('Bagaimana prosedur SOP ini?', answer, pilot=True,
        source='Prosedur: memeriksa data.')
    assert public['response'] == answer
    assert public['grounding']['grounded']


def test_chat_keeps_source_accepted_by_canonical_retrieval(tmp_path):
    source = 'KTP-el adalah identitas penduduk.'
    store = FakeStore(semantic=(.5, .2), lexical=(0., 0.))
    store.chunks[0].content = source
    store.get_document_info = lambda _: SimpleNamespace(title='KTP-el', source=source, metadata={})
    engine = KnowledgeEngine(rag=make_rag(tmp_path, store=store))
    parts = fixture(answer=source)
    parts[2]['knowledge'] = engine
    request = SimpleNamespace(user_input='Apa itu KTP-el?', session_id='fixture-session')
    core = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    public = parts[3](core.payload, intent_name=core.intent_name)
    assert public['response'] == source
    assert public['grounding']['grounded']
    assert len(public['evidence']) == 1
    assert public['evidence'][0]['score'] < .5


def test_failed_answer_validation_does_not_claim_the_document_lacks_information():
    public = run_document_chat('Apa persyaratan dokumen ini?',
        'Persyaratan: Wajib membawa KTP dan membayar 500 rupiah.')
    assert not public['grounding']['grounded']
    assert 'belum dapat dipastikan' in public['response']
    assert 'tidak ditemukan' not in public['response']
    assert public['evidence'][0]['document_id'] == 'selected'


def test_selected_sop_recovers_explicit_source_when_model_invents_a_requirement():
    public = run_document_chat('Apa persyaratan SOP ini?',
        'Persyaratan: Wajib membawa KTP dan membayar 500 rupiah.', pilot=True)
    assert public['response'] == 'Persyaratan: Pemohon menyerahkan Surat Permohonan kepada petugas.'
    assert public['grounding']['grounded']
    assert public['trust']['supports_claim']
    assert public['provider_status'] == 'evidence_fast_path'
    assert public['evidence'][0]['pages'] == [1]


@pytest.mark.parametrize('answer', [
    'Persyaratan: Pemohon menyerahkan Surat Permohonan dan KTP kepada petugas.',
    'Persyaratan: Pemohon menyerahkan Surat Permohonan dengan biaya 500 rupiah.',
    'Persyaratan: Pemohon mengunggah Surat Permohonan melalui aplikasi.',
    'Persyaratan: Pemohon menyerahkan Surat Permohonan kepada kepolisian.',
    'Persyaratan: Pemohon tidak perlu menyerahkan Surat Permohonan kepada petugas.',
    'Persyaratan: Pemohon menyerahkan Surat Permohonan dalam 3 hari kerja.',
])
def test_recovery_never_delivers_invented_documents_channels_places_negations_or_numbers(answer):
    public = run_document_chat('Apa persyaratan SOP ini?', answer, pilot=True)
    assert public['response'] == 'Persyaratan: Pemohon menyerahkan Surat Permohonan kepada petugas.'
    assert public['grounding']['grounded']
    assert public['provider_status'] == 'evidence_fast_path'


def test_recovery_does_not_return_only_the_first_item_of_a_multiline_requirement_list():
    public = run_document_chat('Apa persyaratan SOP ini?', 'Wajib membawa paspor.', pilot=True,
        source='Persyaratan: Surat Permohonan\n- Surat Pengantar')
    assert not public['grounding']['grounded']
    assert 'belum dapat dipastikan' in public['response']
    assert public['provider_status'] != 'evidence_fast_path'


def test_recovery_does_not_omit_requirement_items_split_into_separate_blocks():
    public = run_document_chat('Apa persyaratan SOP ini?', 'Wajib membawa paspor.', pilot=True,
        source='Persyaratan: Surat Permohonan\nSurat Pengantar', metadata={'docling_blocks': [
            {'block_id': 'first', 'content': 'Persyaratan: Surat Permohonan', 'page_numbers': [1]},
            {'block_id': 'second', 'content': 'Surat Pengantar', 'page_numbers': [1]}]})
    assert not public['grounding']['grounded']
    assert public['provider_status'] != 'evidence_fast_path'


@pytest.mark.parametrize('score', [float('nan'), float('inf'), -.1, 1.1, .49])
def test_adapter_without_canonical_retrieval_cannot_bypass_score_checks(score):
    parts = fixture(answer='KTP-el adalah identitas penduduk.')
    item = SimpleNamespace(document_id='unverified', title='KTP-el',
        source='KTP-el adalah identitas penduduk.', chunk='KTP-el adalah identitas penduduk.', score=score)
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [item]
    request = SimpleNamespace(user_input='Apa itu KTP-el?', session_id='fixture-session')
    core = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    public = parts[3](core.payload, intent_name=core.intent_name)
    assert not public['grounding']['grounded']
    assert public['evidence'] == []


def test_backend_loads_the_existing_chat_route():
    from fastapi.testclient import TestClient

    from app.main import app

    assert TestClient(app).post('/v1/chat', json={}).status_code == 422
