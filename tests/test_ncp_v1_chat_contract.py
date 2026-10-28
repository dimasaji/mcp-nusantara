"""NCP-V1-CHAT-001: public response and provider input, no real inference."""
import asyncio
import pytest
from types import SimpleNamespace
from test_v1_langgraph import fixture
from app.memory.engine import MemoryEngine


def execute(parts, question, session='contract-session', **extra):
    core = asyncio.run(parts[1].execute_v1(SimpleNamespace(
        user_input=question, session_id=session, model=None, stream=False, **extra), **parts[2]))
    return parts[3](core.payload, intent_name=core.intent_name)


def test_sop_trial_status_question_uses_model_instead_of_dumping_full_source():
    parts = fixture(answer='Informasi belum tersedia dalam SOP.')
    result = execute(parts, 'Berapa waktu menurut SOP ini?', document_ids=['fixture-ktp'], sop_version='a'*64)
    assert parts[4].calls == 1
    assert result['provider_status'] == 'ollama'


def test_sop_trial_model_receives_extracted_document_text_not_only_fact_quote():
    from test_v1_service_dialogue import setup, SOURCE
    parts = setup(answer='Pemohon menyampaikan Surat Permohonan.')
    item = parts[2]['knowledge'].search_knowledge('fixture')[0]
    item.metadata = {
        'sop_rows': [{'number': 1, 'activity': 'Menyampaikan Surat Permohonan',
                      'kelengkapan': 'Surat Permohonan', 'keterangan': '', 'page': 1}],
        'full_document_text': SOURCE,
    }
    observed = []
    original = parts[4].generate
    async def capture(request):
        observed.append(request)
        return await original(request)
    parts[4].generate = capture
    result = execute(parts, 'Apa persyaratan permohonan data pribadi?',
                     document_ids=['service-private'], sop_version='a'*64)
    assert result['provider_status'] == 'ollama'
    assert len(observed) == 1
    # Context includes the actual stored extraction, including the procedure
    # and duration, instead of only the deterministic fact quote.
    assert SOURCE in observed[0]['prompt']
    assert '3 Hari Kerja' in observed[0]['prompt']


def test_sop_prompt_preserves_all_source_words_or_refuses_before_generation():
    import pytest
    from app.knowledge.sop_review import sop_prompt
    system, prompt = sop_prompt('Judul\nPersyaratan surat.\nProses lengkap.\nWaktu tiga hari.', 'Apa persyaratannya?', [], 4096)
    assert 'Judul\nPersyaratan surat.\nProses lengkap.\nWaktu tiga hari.' in prompt
    assert len((system+prompt).encode()) + 96 + 128 <= 4096
    with pytest.raises(ValueError, match='tidak muat utuh'):
        sop_prompt('X' * 5000, 'Apa persyaratannya?', [], 4096)


def test_pilot_does_not_accept_a_new_channel_merely_from_topic_overlap():
    from app.knowledge.sop_review import sop_wording_supported
    source = 'Nomor SOP. Pemohon menyampaikan Surat Permohonan. Proses selesai 3 Hari Kerja.'
    assert not sop_wording_supported('Ya, nomor WhatsApp petugas tercantum dalam SOP ini.', source)
    assert not sop_wording_supported('Pemohon harus mengisi formulir dan memverifikasi database.', source)
    assert sop_wording_supported('Pemohon menyampaikan Surat Permohonan.', source)
    assert sop_wording_supported('Nomor WhatsApp belum ditemukan dalam SOP ini.', source)


@pytest.mark.parametrize('answer', [
    'Nomor WhatsApp petugas belum ditemukan dalam SOP ini.',
    'SOP ini tidak menyebutkan nomor WhatsApp petugas.',
])
def test_sop_trial_accepts_missing_contact_without_losing_model_and_citations(answer):
    parts = fixture(answer=answer)
    source = 'Pemohon menyampaikan Surat Permohonan. Pelayanan selesai 3 Hari Kerja.'
    item = SimpleNamespace(document_id='selected', title='Layanan contoh', source=source,
                           chunk=source, score=1., metadata={'citation_pages': [1, 2],
                                                           'full_document_text': source})
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [item]
    result = execute(parts, 'Apakah SOP ini menyebutkan nomor WhatsApp petugas?',
                     document_ids=['selected'], sop_version='a'*64)
    assert parts[4].calls == 1
    assert result['provider_status'] == 'ollama'
    assert result['grounding']['grounded'], result
    assert result['response'] == parts[4].answer
    assert result['evidence'][0]['document_id'] == 'selected'
    assert result['evidence'][0]['pages'] == [1, 2]


@pytest.mark.parametrize('answer', [
    'Nomor WhatsApp belum ditemukan, hubungi 08123456789.',
    'Nomor WhatsApp belum ditemukan, tetapi wajib membawa KTP.',
    'Nomor WhatsApp belum ditemukan, silakan unggah formulir online.',
    'Nomor WhatsApp belum ditemukan, tetapi layanan gratis.',
    'Nomor WhatsApp belum ditemukan dan layanan gratis.',
    'Layanan gratis dan nomor WhatsApp belum ditemukan dalam SOP ini.',
    'Layanan gratis sedangkan nomor WhatsApp belum ditemukan dalam SOP ini.',
    'Layanan gratis meskipun nomor WhatsApp belum ditemukan dalam SOP ini.',
    'Pelayanan online tersedia sementara nomor WhatsApp belum ditemukan dalam SOP ini.',
])
def test_sop_trial_missing_contact_does_not_authorize_extra_claims(answer):
    parts = fixture(answer=answer)
    source = 'Pemohon menyampaikan Surat Permohonan. Pelayanan selesai 3 Hari Kerja.'
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [SimpleNamespace(
        document_id='selected', title='Layanan contoh', source=source,
        chunk=source, score=1., metadata={'citation_pages': [1, 2]})]
    result = execute(parts, 'Apakah SOP ini menyebutkan nomor WhatsApp petugas?',
                     document_ids=['selected'], sop_version='a'*64)
    assert not result['grounding']['grounded']
    assert result['response'] != answer


@pytest.mark.parametrize('full_text', [None, 'Kontak petugas: WA 08123456789.',
                                      'Hubungi petugas melalui telepon.'])
def test_sop_trial_cannot_claim_missing_contact_without_full_source_proof(full_text):
    parts = fixture(answer='SOP ini tidak menyebutkan nomor WhatsApp petugas.')
    source = 'Pemohon menyampaikan Surat Permohonan. Pelayanan selesai 3 Hari Kerja.'
    metadata = {'citation_pages': [1]}
    if full_text is not None:
        metadata['full_document_text'] = source + '\n' + full_text
    parts[2]['knowledge'].search_knowledge = lambda *args, **kwargs: [SimpleNamespace(
        document_id='selected', title='Layanan contoh', source=source,
        chunk=source, score=1., metadata=metadata)]
    result = execute(parts, 'Apakah SOP ini menyebutkan nomor WhatsApp petugas?',
                     document_ids=['selected'], sop_version='a'*64)
    assert not result['grounding']['grounded']
    assert result['response'] != parts[4].answer


def test_general_definition_does_not_require_knowledge():
    parts = fixture(empty=True, answer='KTP elektronik adalah kartu identitas penduduk dengan data elektronik.')
    result = execute(parts, 'Apa itu KTP elektronik?')
    assert result['response'] == 'KTP elektronik adalah kartu identitas penduduk dengan data elektronik.'
    assert result['grounding']['reason'] == 'not_evaluated'
    assert not result['evidence']


def test_sql_explanation_is_not_an_official_data_operation():
    parts = fixture(empty=True, answer='DELETE menghapus baris dalam SQL; gunakan WHERE untuk membatasi baris.')
    assert execute(parts, 'Jelaskan perintah DELETE SQL')['response'].startswith('DELETE menghapus')


def test_technical_word_cannot_bypass_official_requirements():
    parts = fixture(empty=True, answer='Wajib membawa tiga fotokopi.')
    result = execute(parts, 'Tuliskan SQL berisi persyaratan penerbitan SIM')
    assert result['grounding']['reason'] == 'no_evidence'
    assert result['response'] == 'Informasi tersebut belum tersedia secara cukup dalam knowledge base.'


def test_current_facts_report_missing_web_integration():
    parts = fixture(empty=True)
    result = execute(parts, 'Siapa presiden sekarang?')
    assert 'tidak memiliki akses pencarian web langsung' in result['response']
    assert parts[4].calls == 0


def test_pre_provider_retry_links_attempt_without_redispatching_old_id():
    memory = MemoryEngine()
    memory.begin_chat('retry-session', 'a'*32, 'Pertanyaan yang sama')
    memory.finish_chat('retry-session', 'a'*32, error='HTTP_503_PRE_PROVIDER')
    assert memory.begin_chat('retry-session', 'b'*32, 'Pertanyaan yang sama', retry_of='a'*32) == {'state':'NEW'}
    memory.finish_chat('retry-session', 'b'*32, answer={'response':'Sudah pulih'})
    assert memory.chat_history('retry-session')[-1]['retry_of'] == 'a'*32
    assert memory.begin_chat('retry-session', 'b'*32, 'Pertanyaan yang sama') == {'state':'SUCCEEDED','answer':{'response':'Sudah pulih'}}


def test_service_fact_quote_retains_known_pdf_page():
    from test_v1_service_dialogue import setup, SOURCE
    parts = setup()
    item = parts[2]['knowledge'].search_knowledge('fixture')[0]
    item.metadata = {'source_pages':[{'page':1,'start':0,'end':len(SOURCE)}]}
    result = execute(parts, 'Apa persyaratan permohonan data pribadi?')
    assert result['grounding']['grounded']
    assert result['evidence'][0]['pages'] == [1]


def test_selected_document_followup_keeps_filter_and_retrieval_context():
    from test_v1_service_dialogue import setup
    parts = setup()
    item = parts[2]['knowledge'].search_knowledge('fixture')[0]
    observed = []
    def search(query, **options):
        observed.append((query, options))
        return [item]
    parts[2]['knowledge'].search_knowledge = search
    execute(parts, 'Apa persyaratan permohonan data pribadi?', document_ids=['service-private'])
    result = execute(parts, 'Jelaskan lebih sederhana', document_ids=['service-private'])
    assert observed[-1][1]['filter'] == {'document_ids':['service-private']}
    assert 'Apa persyaratan permohonan data pribadi?' in observed[-1][0]
    assert result['grounding']['grounded']


def test_provider_unavailable_is_retryable_error_instead_of_saved_answer():
    from fastapi import HTTPException
    import pytest
    parts = fixture(empty=True)
    async def unavailable():
        return {'available': False}
    parts[4].health_check = unavailable
    with pytest.raises(HTTPException) as failure:
        execute(parts, 'Bagaimana pelangi terbentuk?')
    assert failure.value.status_code == 503
    assert failure.value.headers['X-Chat-Retry-Safe'] == 'pre-provider'


def test_natural_followup_keeps_bounded_same_session_context():
    parts = fixture(empty=True, answer='Pelangi muncul ketika cahaya matahari melewati tetes air.')
    memory = MemoryEngine()
    memory.remember('contract-session', 'user', '2+2')
    memory.remember('contract-session', 'assistant', '4')
    memory.remember('contract-session', 'user', 'Bagaimana pelangi terbentuk?')
    memory.remember('contract-session', 'assistant', 'Tetes air membiaskan cahaya matahari menjadi warna pelangi.')
    parts[2]['gates'].memory = memory
    observed = []
    original = parts[4].generate
    async def generate(request):
        observed.append(request)
        return await original(request)
    parts[4].generate = generate
    result = execute(parts, 'Jelaskan lebih sederhana')
    assert result['response'].startswith('Pelangi muncul')
    assert 'Tetes air membiaskan' in observed[-1]['prompt']
    assert '2+2' not in observed[-1]['prompt']
    execute(parts, 'Bagaimana pelangi terbentuk?', session='new-session')
    assert 'Tetes air membiaskan' not in observed[-1]['prompt']
    assert result['grounding']['reason'] == 'not_evaluated'
