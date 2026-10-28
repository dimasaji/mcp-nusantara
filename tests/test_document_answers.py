from types import SimpleNamespace


def test_document_facts_use_submission_cell_and_never_invent_cost():
    from app.knowledge.document_answers import document_answer_facts
    item = SimpleNamespace(title='Layanan contoh', document_id='example', score=1., source='Tabel SOP',
        metadata={'sop_rows': [{'number': 1, 'activity': 'Menyampaikan Surat Pengantar',
            'kelengkapan': 'Surat Pengantar', 'waktu': '', 'output': 'Surat Pengantar', 'keterangan': '', 'page': 1},
            {'number': 2, 'activity': 'Pelayanan selesai', 'kelengkapan': '', 'waktu': '', 'output': '',
             'keterangan': '7 Hari Kerja', 'page': 2}], 'full_document_text': 'Persyaratan petugas: mengoperasikan komputer. Surat Pengantar. 7 Hari Kerja.'})
    facts = document_answer_facts('Bawa apa saja?', [item])
    assert facts['fallback'] == 'Siapkan Surat Pengantar.'
    cost = document_answer_facts('Berapa biayanya?', [item])
    assert cost['unknown'] is True
    assert 'gratis' not in cost['fallback'].lower()


def test_cost_absence_reaches_public_chat_without_an_intent_mapping_error():
    import asyncio
    from test_v1_langgraph import fixture
    parts = fixture(empty=False, answer='Biaya belum tercantum dalam SOP ini.')
    item = SimpleNamespace(title='Layanan contoh', document_id='selected', score=1., source='Surat Pengantar.',
        chunk='Surat Pengantar.', metadata={'sop_rows': [{'number': 1, 'activity': 'Menyampaikan Surat Pengantar',
            'kelengkapan': 'Surat Pengantar', 'waktu': '', 'output': 'Surat Pengantar', 'keterangan': '', 'page': 1}],
            'full_document_text': 'Surat Pengantar.'})
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [item]
    request = SimpleNamespace(user_input='Berapa biayanya?', document_ids=['selected'], sop_version='a'*64, session_id='same')
    result = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    public = parts[3](result.payload, intent_name=result.intent_name)
    assert public['grounding']['grounded']
    assert public['response'] == 'Biaya belum tercantum dalam SOP ini.'


def test_partial_extraction_error_is_preserved_instead_of_becoming_missing_information():
    import asyncio
    import pytest
    from fastapi import HTTPException
    from test_v1_langgraph import fixture
    parts = fixture(empty=False)
    def unreadable(*args, **kwargs):
        raise HTTPException(409, 'Masalah pembacaan SOP: DOCUMENT_EXTRACTION_PARTIAL')
    parts[2]['knowledge'].search_knowledge = unreadable
    request = SimpleNamespace(user_input='Apa persyaratannya?', document_ids=['selected'], sop_version='a'*64, session_id='same')
    with pytest.raises(HTTPException) as error:
        asyncio.run(parts[1].execute_v1(request, **parts[2]))
    assert error.value.status_code == 409
    assert 'DOCUMENT_EXTRACTION_PARTIAL' in error.value.detail
