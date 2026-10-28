"""Selected PDF scope must survive short follow-ups and expose real page citations."""
import asyncio
from types import SimpleNamespace
import pytest

from test_v1_langgraph import fixture
from test_sop_review import engine_at


def table_pdf():
    import pymupdf
    pdf = pymupdf.open()
    rows = [
        [['No.', 'Uraian Kegiatan', 'Kelengkapan', 'Waktu', 'Output', 'Keterangan'],
         ['1', 'Menyampaikan Surat Pengantar', 'Surat Pengantar', '', 'Surat Pengantar', '']],
        [['No.', 'Uraian Kegiatan', 'Kelengkapan', 'Waktu', 'Output', 'Keterangan'],
         ['2', 'Memeriksa permohonan', 'Surat Pengantar', '5 menit', 'Hasil pemeriksaan', ''],
         ['3', 'Pelayanan selesai', '', '', '', '7 Hari Kerja']]]
    for page_rows in rows:
        page = pdf.new_page(width=1100, height=500)
        xs = [20, 60, 390, 580, 710, 900, 1080]
        for y in range(40, 41 + 60 * len(page_rows), 60):
            page.draw_line((20, y), (1080, y))
        for x in xs:
            page.draw_line((x, 40), (x, 40 + 60 * len(page_rows)))
        for r, row in enumerate(page_rows):
            for c, value in enumerate(row):
                page.insert_text((xs[c] + 4, 65 + r * 60), value, fontsize=10)
    return pdf.tobytes()


@pytest.fixture
def approved_pdf(tmp_path, monkeypatch):
    """Exercise the existing review lifecycle before ordinary document Chat."""
    import json
    from pathlib import Path
    from app.knowledge.document_tools import DocumentTools
    from app.knowledge.sop_review import SOPReview
    from test_review_publication_v1 import _approve_fixture, _convert
    engine = engine_at(tmp_path/'chat.db')
    identifier = engine.process_knowledge_source('table.pdf',table_pdf())['document_id']
    def worker(args, **kwargs):
        Path(args[-1]).write_text(json.dumps({'status':'COMPLETE','warnings':[],
            'page_count':2,'markdown':'','blocks':[],'docling_json':{'fixture':True}}),encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('app.knowledge.worker_process.run_worker',worker)
    review = SOPReview(engine)
    detail = _convert(DocumentTools(engine,operator=True),review,identifier)
    assert _approve_fixture(review,detail)['status']=='Aktif'
    return engine,identifier


def test_selected_pdf_uses_verified_table_cells_and_recovers_pages_without_reindex(approved_pdf):
    from app.security.v1_knowledge import V1KnowledgeBoundary
    engine,identifier = approved_pdf
    before = engine.rag.get_document_info(identifier).model_dump()
    boundary = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[identifier])
    evidence = boundary.search_knowledge('Apa persyaratannya?', filter={'document_ids': [identifier]})
    assert len(evidence) == 1
    assert evidence[0].metadata['sop_rows'][0]['kelengkapan'] == 'Surat Pengantar'
    assert {r['page'] for r in evidence[0].metadata['sop_rows']} == {1, 2}
    assert engine.rag.get_document_info(identifier).model_dump() == before


def test_selected_pdf_followup_cannot_escape_to_conversation_or_clarification():
    parts = fixture(empty=False, answer='Menurut SOP, waktunya 7 hari kerja.')
    evidence = SimpleNamespace(document_id='selected-pdf', title='Layanan contoh',
        source='Waktu penyelesaian: 7 hari kerja.', chunk='Waktu penyelesaian: 7 hari kerja.',
        score=1., metadata={'citation_pages': [2]})
    parts[2]['knowledge'].search_knowledge = lambda *args, **kw: [evidence]
    parts[2]['gates'].memory = SimpleNamespace(service_context=lambda _: {},
        context=lambda *args, **kw: [
            {'role': 'user', 'content': 'Apa persyaratan menurut SOP Layanan contoh?'},
            {'role': 'assistant', 'content': 'Informasi belum ditemukan.'}])
    request = SimpleNamespace(user_input='Berapa lama waktu penyelesaiannya?',
        document_ids=['selected-pdf'], session_id='same-session')
    core = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    answer = parts[3](core.payload, intent_name=core.intent_name)
    assert answer['grounding']['grounded'], answer
    assert answer['evidence'][0]['document_id'] == 'selected-pdf'
    assert answer['evidence'][0]['pages'] == [2]
    assert '7 hari kerja' in answer['response']


@pytest.mark.parametrize('question,expected,pages', [
    ('Apa persyaratan menurut SOP layanan contoh?', 'Surat Pengantar', [1]),
    ('Berapa lama waktu penyelesaiannya?', '7 Hari Kerja', [2]),
    ('Bagaimana prosedurnya?', 'Memeriksa permohonan', [1, 2]),
])
def test_selected_pdf_answers_from_cells_when_model_invents_requirements(approved_pdf, question, expected, pages):
    from app.security.v1_knowledge import V1KnowledgeBoundary
    engine,identifier = approved_pdf
    parts = fixture(answer='Wajib membawa KTP dan membayar 500 rupiah.')
    parts[2]['knowledge'] = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[identifier])
    req = SimpleNamespace(user_input=question, document_ids=[identifier], session_id='same-session')
    core = asyncio.run(parts[1].execute_v1(req, **parts[2]))
    answer = parts[3](core.payload, intent_name=core.intent_name)
    assert answer['grounding']['grounded'], answer
    assert expected.casefold() in answer['response'].casefold()
    assert 'KTP' not in answer['response'] and '500' not in answer['response']
    assert answer['evidence'][0]['pages'] == pages


def test_pdf_procedure_rejects_invented_destination_and_truncated_steps(approved_pdf):
    from app.security.v1_knowledge import V1KnowledgeBoundary
    engine,identifier = approved_pdf
    parts = fixture(answer='Menyampaikan Surat Pengantar ke departemen yang berwenang. Memeriksa permohonan.')
    parts[2]['knowledge'] = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[identifier])
    req = SimpleNamespace(user_input='Bagaimana prosedurnya?', document_ids=[identifier], session_id='same-session')
    core = asyncio.run(parts[1].execute_v1(req, **parts[2]))
    answer = parts[3](core.payload, intent_name=core.intent_name)
    assert answer['grounding']['grounded']
    assert 'departemen' not in answer['response']
    assert 'Pelayanan selesai' in answer['response']


def test_pdf_procedure_preserves_source_row_order(approved_pdf):
    from app.security.v1_knowledge import V1KnowledgeBoundary
    engine,identifier = approved_pdf
    parts = fixture(answer='Prosedur:\n3. Pelayanan selesai.\n2. Memeriksa permohonan.\n1. Menyampaikan Surat Pengantar.')
    parts[2]['knowledge'] = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[identifier])
    req = SimpleNamespace(user_input='Bagaimana prosedurnya?', document_ids=[identifier], session_id='same-session')
    core = asyncio.run(parts[1].execute_v1(req, **parts[2]))
    answer = parts[3](core.payload, intent_name=core.intent_name)
    assert answer['grounding']['grounded']
    assert answer['response'].index('Menyampaikan') < answer['response'].index('Memeriksa') < answer['response'].index('Pelayanan selesai')
