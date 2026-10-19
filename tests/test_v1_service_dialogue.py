import asyncio
from types import SimpleNamespace
import pytest
from app.language.engine import LanguageEngine
from app.core.gate_integration import GateIntegration
from app.knowledge.grounding import EvidenceGroundingGuard, service_answer_facts
from test_v1_langgraph import fixture

SOURCE='''SOP Permohonan Data Pribadi (PIAK-03)
Persyaratan permohonan data pribadi: Surat Permohonan.
Prosedur: menyampaikan Surat Permohonan; mendisposisi izin dan proses; memverifikasi data dalam database; menyusun laporan hasil verifikasi dan jawaban; memverifikasi jawaban dan nota; menandatangani surat jawaban; menstempel dan mengagenda; menyerahkan dan mengarsipkan surat jawaban; pemohon menerima surat jawaban dan berkas data.
Pada akhir alur halaman 2 tercantum 3 Hari Kerja.
'''


@pytest.mark.parametrize('reference', ['BANTU-07', 'BANTU-99'])
def test_explicit_sop_reference_selects_only_matching_document(reference):
    turn = LanguageEngine.service_turn(f'Bagaimana prosedur pengajuan bantuan usaha menurut SOP {reference}?')
    source = 'Persyaratan bantuan usaha: Surat Usaha.\nProsedur: menyerahkan Surat Usaha; petugas memverifikasi data.'
    evidence = [SimpleNamespace(document_id=code, title=f'SOP Bantuan Usaha ({code})',
        source=source, score=.9) for code in ['BANTU-07', 'BANTU-08']]
    facts = service_answer_facts(turn, evidence)
    if reference == 'BANTU-07':
        assert facts is not None
        assert facts['document_id'] == reference
        assert facts['facet'] == 'procedure'
        assert 'memverifikasi data' in facts['quote']
    else:
        assert facts is None


@pytest.mark.parametrize('answer',[
    'Persyaratan layanan adalah Surat Permohonan yang harus disampaikan kepada petugas layanan. Waktu layanan adalah 3 hari kerja, yaitu hari Jumat, Sabtu, dan Minggu.',
    'Waktu layanan adalah 3 Hari Kerja, termasuk hari Minggu.',
    'Waktu layanan adalah 3 Hari Kerja. Sabtu.',
])
def test_real_model_cannot_add_delivery_steps_or_calendar_facts(answer):
    result=EvidenceGroundingGuard().validate(answer,[{'title':'fixture.pdf',
        'chunk':'Persyaratan layanan: Surat Permohonan. Waktu layanan adalah 3 Hari Kerja.'}],
        'ask_document_requirements')
    assert not result.grounded


def setup(answer='Silakan siapkan surat permohonan.'):
    parts=fixture(answer=answer)
    item=SimpleNamespace(document_id='service-private',title='SOP Permohonan Data Pribadi (PIAK-03)',source=SOURCE,chunk=SOURCE,score=.9)
    parts[2]['knowledge'].search_knowledge=lambda *args,**kwargs:[item]
    parts[2]['gates']=GateIntegration()
    return parts


def ask(parts,text,session='dialogue'):
    request=SimpleNamespace(user_input=text,session_id=session,model=None,stream=False)
    core=asyncio.run(parts[1].execute_v1(request,**parts[2]))
    return parts[3](core.payload,intent_name=core.intent_name)


@pytest.mark.parametrize('question',[
    'Mau minta data pribadi, bawa apa?',
    'Dokumen apa saja yang perlu saya siapkan untuk mengurus data pribadi?',
    'Aku ngurus data pribadi, syaratnya apa dong?',
])
def test_colloquial_service_requests_are_resolved_without_question_lookup(question):
    parts=setup()
    result=ask(parts,question)
    assert result['grounding']['grounded'] is True
    assert 'surat permohonan' in result['response'].lower()
    assert result['provider_status']=='ollama'
    assert len(result['evidence'])==1 and result['evidence'][0]['document_id']=='service-private'


def test_followups_retrieve_fresh_evidence_in_same_session_and_do_not_guess_online():
    parts=setup();ask(parts,'Mau minta data pribadi, bawa apa?')
    parts[4].answer='Silakan sampaikan Surat Permohonan. Petugas memverifikasi data dan menyiapkan jawaban.'
    process=ask(parts,'Kalau prosesnya?')
    assert process['grounding']['grounded'] and 'verifikasi' in process['response'].lower()
    parts[4].answer='SOP mencantumkan 3 Hari Kerja.'
    duration=ask(parts,'Berapa lama?')
    assert duration['grounding']['grounded'] and '3 Hari Kerja' in duration['response']
    calls=parts[4].calls
    online=ask(parts,'Bisa online?')
    assert online['grounding']['reason']=='grounded_abstention'
    assert parts[4].calls==calls
    assert 'belum tersedia' in online['response']
    assert not any(x in online['response'].lower() for x in ['bisa online','tidak bisa online','dapat online'])
    separate=ask(parts,'Berapa lama?',session='another-session')
    assert separate['response']=='Layanan apa yang Anda maksud?'
    assert not separate['evidence'] and not separate['grounding']['grounded']
    parts[2]['knowledge'].search_knowledge=lambda *args,**kwargs:[]
    missing=ask(parts,'Berapa lama?')
    assert not missing['grounding']['grounded'] and not missing['evidence']


def test_prosedurnya_retains_actual_service_context_and_citation():
    parts=setup()
    parts[4].name='openrouter'
    ask(parts,'Apa persyaratan permohonan data pribadi berdasarkan SOP PIAK-03?')
    turn=LanguageEngine.service_turn('Bagaimana prosedurnya?','permohonan data pribadi')
    assert turn['facet']=='procedure' and turn['uses_context']
    parts[4].answer='Petugas memverifikasi data dalam database.'
    result=ask(parts,'Bagaimana prosedurnya?')
    assert result['grounding']['grounded']
    assert 'verifikasi' in result['response'].lower()
    assert result['evidence'][0]['document_id']=='service-private'
    assert parts[4].calls==0
    parts[4].answer='SOP mencantumkan 3 Hari Kerja.'
    duration=ask(parts,'Berapa lama prosesnya?')
    assert duration['grounding']['grounded']
    assert '3 hari kerja' in duration['response'].lower()


@pytest.mark.parametrize('answer',[
    'Anda wajib membawa KTP dan Kartu Keluarga.',
    'Datang ke kantor dan bayar 50 ribu.',
    'Anda tidak perlu menyerahkan Surat Permohonan.',
    'Sumber: Surat Permohonan. Surat Permohonan Anda telah diserahkan kepada kami.',
    'Silakan siapkan Surat Permohonan yang sudah diterima petugas.',
])
def test_unsupported_model_rewrite_is_replaced_and_final_text_is_validated(answer):
    parts=setup(answer)
    result=ask(parts,'Mau minta data pribadi, bawa apa?')
    assert result['provider_status']=='evidence_fast_path'
    assert result['response']=='Silakan siapkan Surat Permohonan.'
    assert result['grounding']['grounded']
    assert parts[4].calls==1


def test_fact_selection_and_rewrite_are_not_specific_to_piak():
    turn=LanguageEngine.service_turn('Aku ngurus bantuan usaha, bawa apa?')
    source='Persyaratan bantuan usaha: Surat Usaha.\nProsedur: menyerahkan Surat Usaha; petugas memverifikasi data.\nWaktu penyelesaian 7 hari kerja.'
    evidence=[SimpleNamespace(document_id='other-service',title='Panduan Bantuan Usaha',source=source,score=.9)]
    facts=service_answer_facts(turn,evidence)
    assert facts['document_id']=='other-service'
    guard=EvidenceGroundingGuard()
    assert guard.validate_service_rewrite('Silakan siapkan Surat Usaha.',facts).grounded
    assert not guard.validate_service_rewrite('Bisa online tanpa Surat Usaha.',facts).grounded
    assert service_answer_facts({**turn,'topic_hint':'layanan berbeda'},evidence) is None
    context={'topic':'bantuan usaha','document_id':'other-service'}
    brief=service_answer_facts(LanguageEngine.service_turn('Kalau prosesnya?',context['topic']),evidence,context)
    detailed=service_answer_facts(LanguageEngine.service_turn('Jelaskan prosesnya lengkap',context['topic']),evidence,context)
    assert brief['rewrite_quote']=='menyerahkan Surat Usaha; petugas memverifikasi data.'
    assert detailed['rewrite_quote']==detailed['quote']


@pytest.mark.parametrize('answer',[
    'Layanan kami membutuhkan waktu 3 hari kerja.',
    'Menurut SOP, permohonan Anda pasti selesai dalam 3 hari kerja.',
    'Menurut SOP, waktunya 3 hari.',
])
def test_duration_rewrite_cannot_become_an_office_promise(answer):
    parts=setup();ask(parts,'Mau minta data pribadi, bawa apa?')
    parts[4].answer=answer
    result=ask(parts,'Berapa lama?')
    assert result['response']=='Menurut SOP, waktunya 3 hari kerja.'
    assert result['provider_status']=='evidence_fast_path'
    assert result['grounding']['grounded']


def test_provider_phrasing_failure_uses_validated_evidence_without_external_fallback():
    parts=setup();parts[4].failure='error'
    result=ask(parts,'Mau minta data pribadi, bawa apa?')
    assert result['response']=='Silakan siapkan Surat Permohonan.'
    assert result['provider_status']=='evidence_fast_path'
    assert result['grounding']['grounded']
    assert parts[4].calls==1


@pytest.mark.parametrize('question,facet',[
    ('Berapa lama prosesnya?','duration'),
    ('Bisa mengajukan lewat online?','channel'),
    ('Bagaimana cara mengajukan secara daring?','channel'),
])
def test_specific_followup_aspect_wins_over_generic_process_word(question,facet):
    turn=LanguageEngine.service_turn(question,'bantuan usaha')
    assert turn['facet']==facet
    assert turn['uses_context'] and turn['topic']=='bantuan usaha'
