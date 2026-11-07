from types import SimpleNamespace


def test_requirements_include_intake_checklist_without_internal_documents():
    from app.knowledge.document_answers import document_answer_facts

    rows = [
        {'number': 1, 'activity': 'Mengunggah berkas permohonan',
         'kelengkapan': 'Berkas persyaratan online', 'page': 2},
        {'number': 2, 'activity': 'Memeriksa kelengkapan berkas',
         'kelengkapan': '1. Surat A; 2. Surat B', 'page': 3},
        {'number': 3, 'activity': 'Mendisposisi permohonan',
         'kelengkapan': 'Lembar disposisi internal', 'page': 3}]
    item = SimpleNamespace(title='Layanan contoh', document_id='example', score=1.,
                           metadata={'sop_rows': rows})
    facts = document_answer_facts('Apa persyaratannya?', [item])
    assert facts is not None
    assert 'Surat A' in facts['fallback'] and 'Surat B' in facts['fallback']
    assert 'disposisi' not in facts['fallback'].casefold()
    assert facts['pages'] == [2, 3]
    first = document_answer_facts('Dokumen apa pada langkah pertama?', [item])
    assert first['fallback'] == 'Siapkan Berkas persyaratan online.'
    assert first['pages'] == [2]


def test_chat_keeps_later_intake_requirements_when_model_invents_documents():
    import asyncio

    from test_v1_langgraph import fixture

    from app.knowledge.pdf_sop import rows_text

    rows = [
        {'number': 1, 'activity': 'Mengunggah berkas permohonan',
         'kelengkapan': 'Berkas persyaratan online', 'page': 2},
        {'number': 2, 'activity': 'Memeriksa kelengkapan berkas',
         'kelengkapan': 'Surat A; Surat B', 'page': 3},
        {'number': 3, 'activity': 'Mendisposisi permohonan',
         'kelengkapan': 'Disposisi internal', 'page': 3}]
    text = rows_text(rows)
    item = SimpleNamespace(title='Layanan contoh', document_id='selected', score=1.,
        source=text, chunk=text, metadata={'sop_rows': rows, 'full_document_text': text,
        'citation_pages': [2, 3], 'docling_blocks': [
            {'block_id': 'grid', 'type': 'table', 'content': text, 'page_numbers': [2, 3]}]})
    parts = fixture(answer='Wajib membawa paspor dan membayar 500 rupiah.')
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [item]
    request = SimpleNamespace(user_input='Apa persyaratannya?', document_ids=['selected'],
                              sop_version='a'*64, session_id='same')
    core = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    answer = parts[3](core.payload, intent_name=core.intent_name)
    assert answer['grounding']['grounded'], answer
    assert 'Surat A' in answer['response'] and 'Surat B' in answer['response']
    assert 'paspor' not in answer['response'].casefold()
    assert 'disposisi' not in answer['response'].casefold()
    assert answer['evidence'][0]['pages'] == [2, 3]


def test_selected_sop_uses_verified_submission_cell_when_model_adds_requirements():
    import asyncio

    from test_v1_langgraph import fixture
    parts = fixture(answer='Wajib membawa KTP dan membayar 500 rupiah.')
    text = 'Kelengkapan: Surat Pengantar.'
    item = SimpleNamespace(title='Layanan contoh', document_id='selected', score=1., source=text,
        chunk=text, metadata={'sop_rows': [{'number': 1, 'activity': 'Menyampaikan Surat Pengantar',
            'kelengkapan': 'Surat Pengantar', 'waktu': '', 'output': 'Surat Pengantar', 'keterangan': '', 'page': 1}],
            'full_document_text': text, 'citation_pages': [1],
            'docling_blocks': [{'block_id': 'table-1', 'type': 'table', 'content': text, 'page_numbers': [1]}]})
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [item]
    request = SimpleNamespace(user_input='Apa persyaratannya?', document_ids=['selected'],
                              sop_version='a'*64, session_id='same')
    core = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    answer = parts[3](core.payload, intent_name=core.intent_name)
    assert answer['grounding']['grounded'], answer
    assert answer['response'] == 'Siapkan Surat Pengantar.'
    assert answer['evidence'][0]['document_id'] == 'selected'
    assert answer['evidence'][0]['pages'] == [1]


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
    assert 'biaya belum tercantum dalam sop ini' in public['response'].casefold()


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
