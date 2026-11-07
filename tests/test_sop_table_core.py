"""Document-table contract shared by digital and scanned SOP extraction."""
from copy import deepcopy

import pymupdf
import pytest

from app.knowledge.docling_layout import normalize_activity_grids


def scan_source(tmp_path, pages=1):
    """Image-only source; structured content is supplied by the OCR adapter."""
    pdf = pymupdf.open()
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 10, 10), False)
    image.clear_with(255)
    for _ in range(pages):
        page = pdf.new_page()
        page.insert_image(page.rect, stream=image.tobytes('png'))
    source = tmp_path / 'scanned.pdf'
    pdf.save(source)
    return source


def table_block(page, values):
    headers = ['No.', 'Kegiatan', 'Kelengkapan', 'Waktu', 'Output', 'Keterangan']
    matrix = [headers, *values]
    cells = [{'start_row_offset_idx': r, 'end_row_offset_idx': r + 1,
              'start_col_offset_idx': c, 'end_col_offset_idx': c + 1,
              'row_span': 1, 'col_span': 1, 'text': text, 'column_header': r == 0,
              'bbox': {'l': c*50, 't': r*20, 'r': (c+1)*50, 'b': (r+1)*20,
                       'coord_origin': 'TOPLEFT'}}
             for r, row in enumerate(matrix) for c, text in enumerate(row)]
    return {'block_id': f'#/tables/{page}', 'type': 'table', 'page_numbers': [page],
            'content': 'Original table markdown',
            'table_data': {'num_rows': len(matrix), 'num_cols': 6, 'table_cells': cells}}


def test_scan_tables_normalize_across_pages_without_losing_original_cells(tmp_path):
    source = scan_source(tmp_path, pages=2)
    payload = {'status': 'COMPLETE', 'warnings': [], 'page_count': 2,
               'docling_json': {'original': True}, 'blocks': [
        table_block(1, [['1', 'Mengunggah berkas permohonan', 'Berkas persyaratan', '', '', '']]),
        table_block(2, [['2', 'Memeriksa kelengkapan berkas', 'Surat A; Surat B', '5 menit', '', ''],
                        ['3', 'Proses pelayanan selesai', '', '', '', '4 Hari Kerja']])]}
    original = deepcopy(payload)
    result = normalize_activity_grids(payload, source)
    assert [r['number'] for r in result['activity_rows']] == [1, 2, 3]
    assert [r['page'] for r in result['activity_rows']] == [1, 2, 2]
    assert result['activity_rows'][1]['kelengkapan'] == 'Surat A; Surat B'
    assert result['activity_rows'][2]['keterangan'] == '4 Hari Kerja'
    assert result['blocks'][0]['table_data'] == original['blocks'][0]['table_data']
    assert result['docling_json'] == original['docling_json']
    assert result['activity_rows'][1]['source_cells']['kelengkapan']['text'] == 'Surat A; Surat B'
    assert payload == original
    assert normalize_activity_grids(result, source) == result


def test_targeted_number_ocr_can_supply_unreadable_source_cell(tmp_path):
    source = scan_source(tmp_path)
    block = table_block(1, [['1', 'Menyerahkan Surat A', 'Surat A', '', '', '']])
    number = next(c for c in block['table_data']['table_cells']
                  if c['start_row_offset_idx'] == 1 and c['start_col_offset_idx'] == 0)
    recovered = {**number, 'text': '1', 'method': 'tesseract-number-cell', 'confidence': 96}
    number['text'] = '?'
    block['number_cells'] = [recovered]
    payload = {'status': 'COMPLETE', 'warnings': [], 'blocks': [block]}
    result = normalize_activity_grids(payload, source)
    assert result['status'] == 'COMPLETE'
    assert result['activity_rows'][0]['number'] == 1
    assert result['activity_rows'][0]['source_cells']['number']['method'] == 'tesseract-number-cell'
    assert number['text'] == '?'


@pytest.mark.parametrize('number', ['?', '2'])
def test_missing_or_discontinuous_numbers_remain_partial(tmp_path, number):
    source = scan_source(tmp_path)
    block = table_block(1, [[number, 'Menyerahkan Surat A', 'Surat A', '', '', '']])
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [block]}, source)
    assert result['status'] == 'PARTIAL'
    assert result['activity_rows'] == []
    assert result['warnings']
    assert result['blocks'][0]['table_data'] == block['table_data']


def test_source_order_is_not_repaired_by_sorting_step_numbers(tmp_path):
    source = scan_source(tmp_path)
    block = table_block(1, [['2', 'Kegiatan kedua', 'Surat B', '', '', ''],
                            ['1', 'Kegiatan pertama', 'Surat A', '', '', '']])
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [block]}, source)
    assert result['status'] == 'PARTIAL'
    assert result['activity_rows'] == []


def test_conflicting_number_evidence_is_not_silently_overridden(tmp_path):
    source = scan_source(tmp_path)
    block = table_block(1, [['1', 'Menyerahkan Surat A', 'Surat A', '', '', '']])
    number = next(c for c in block['table_data']['table_cells']
                  if c['start_row_offset_idx'] == 1 and c['start_col_offset_idx'] == 0)
    block['number_cells'] = [{**number, 'text': '2', 'confidence': 96}]
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [block]}, source)
    assert result['status'] == 'PARTIAL'
    assert 'ACTIVITY_TABLE_NUMBER_CONFLICT' in result['warnings'][0]


def test_source_header_reconnects_duration_cell_without_changing_table(tmp_path):
    from types import SimpleNamespace

    from app.knowledge.document_answers import document_answer_facts

    block = table_block(1, [['1', 'Proses pelayanan selesai', '', '', '', '4 Hari Kerja']])
    header = next(c for c in block['table_data']['table_cells']
                  if c['start_row_offset_idx'] == 0 and c['start_col_offset_idx'] == 5)
    header['text'] = ''
    block['source_regions'] = [{'page': 1, 'bbox': [0, 0, 300, 40]}]
    block['header_cells'] = [{'text': 'Keterangan', 'bbox': dict(header['bbox']), 'page_number': 1}]
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [block]}, scan_source(tmp_path))
    assert result['activity_rows'][0]['keterangan'] == '4 Hari Kerja'
    item = SimpleNamespace(title='Contoh', document_id='example', score=1., metadata={'sop_rows': result['activity_rows']})
    assert document_answer_facts('Berapa lama?', [item])['fallback'] == 'Menurut SOP: 4 Hari Kerja.'
    assert header['text'] == ''


def test_header_from_another_grid_cannot_label_a_missing_column(tmp_path):
    block = table_block(1, [['1', 'Proses pelayanan selesai', '', '', '', '4 Hari Kerja']])
    for cell in block['table_data']['table_cells']:
        cell['bbox']['t'] += 100
        cell['bbox']['b'] += 100
    header = next(c for c in block['table_data']['table_cells']
                  if c['start_row_offset_idx'] == 0 and c['start_col_offset_idx'] == 5)
    header['text'] = ''
    block['source_regions'] = [{'page': 1, 'bbox': [0, 100, 300, 140]}]
    block['header_cells'] = [{'text': 'Keterangan', 'page_number': 1,
                            'bbox': {'l': 250, 't': 0, 'r': 300, 'b': 20, 'coord_origin': 'TOPLEFT'}}]
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [block]}, scan_source(tmp_path))
    assert result['activity_rows'][0]['keterangan'] == ''


def test_detected_activity_grid_with_unreadable_headers_is_partial(tmp_path):
    block = table_block(1, [['1', 'Menyerahkan Surat A', 'Surat A', '', '', '']])
    block['activity_grid'] = True
    next(c for c in block['table_data']['table_cells']
         if c['start_row_offset_idx'] == 0 and c['start_col_offset_idx'] == 2)['text'] = '?'
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [block]}, scan_source(tmp_path))
    assert result['status'] == 'PARTIAL'
    assert result['activity_rows'] == []


def test_mixed_native_and_scan_pages_share_one_continuous_procedure(tmp_path):
    from test_selected_pdf_chat import table_pdf

    original = pymupdf.open(stream=table_pdf(), filetype='pdf')
    image = original[1].get_pixmap()
    mixed = pymupdf.open()
    mixed.insert_pdf(original, from_page=0, to_page=0)
    page = mixed.new_page(width=original[1].rect.width, height=original[1].rect.height)
    page.insert_image(page.rect, stream=image.tobytes('png'))
    source = tmp_path / 'mixed.pdf'
    mixed.save(source)
    block = table_block(2, [['2', 'Memeriksa berkas', 'Surat A; Surat B', '', '', ''],
                            ['3', 'Proses pelayanan selesai', '', '', '', '4 Hari Kerja']])
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [block],
                                     'docling_json': {'original': True}}, source)
    assert result['status'] == 'COMPLETE', result['warnings']
    assert [r['number'] for r in result['activity_rows']] == [1, 2, 3]
    assert [r['page'] for r in result['activity_rows']] == [1, 2, 2]
    assert result['activity_rows'][0]['source_cells']['kelengkapan']['text'] == 'Surat Pengantar'
    assert result['activity_rows'][1]['source_cells']['kelengkapan']['text'] == 'Surat A; Surat B'


def test_disagreeing_high_confidence_ocr_does_not_supply_a_number(tmp_path, monkeypatch):
    import subprocess

    from app.knowledge.sop_table_ocr import recover_number_cells

    block = table_block(1, [['?', 'Menyerahkan Surat A', 'Surat A', '', '', '']])
    block['source_regions'] = [{'page': 1, 'bbox': [0, 0, 300, 40]}]
    def ocr(command, **kwargs):
        value = '4' if command[command.index('--psm') + 1] == '6' else '1'
        tsv = f'text\tconf\tleft\ttop\twidth\theight\n{value}\t96\t10\t30\t10\t10\n'
        return subprocess.CompletedProcess(command, 0, tsv.encode(), b'')
    monkeypatch.setattr(subprocess, 'run', ocr)
    assert recover_number_cells(block, scan_source(tmp_path),
        {'tesseract_cmd': 'fixture-tesseract', 'tessdata_path': '/fixture'}) == []


def test_normalized_tables_reach_approved_chat_and_survive_restart(tmp_path, monkeypatch):
    import asyncio
    import json
    from pathlib import Path
    from types import SimpleNamespace

    from test_review_publication_v1 import _approve_fixture, _convert
    from test_sop_review import engine_at
    from test_v1_langgraph import fixture

    from app.knowledge.document_tools import DocumentTools
    from app.knowledge.sop_review import SOPReview
    from app.security.v1_knowledge import V1KnowledgeBoundary

    pdf = pymupdf.open()
    for _ in range(2):
        page = pdf.new_page()
        page.insert_text((40, 80), 'Dokumen contoh layanan warga dengan persyaratan pada tabel sumber.')
    raw = pdf.tobytes()
    payload = {'status': 'COMPLETE', 'warnings': [], 'page_count': 2,
        'markdown': 'Tabel sumber', 'docling_json': {'fixture': True}, 'blocks': [
        table_block(1, [['1', 'Mengunggah berkas permohonan', 'Berkas online', '', '', '']]),
        table_block(2, [['2', 'Memeriksa kelengkapan berkas', 'Surat A; Surat B', '', '', ''],
                        ['3', 'Proses pelayanan selesai', '', '', '', '4 Hari Kerja']])]}
    def worker(args, **kwargs):
        Path(args[-1]).write_text(json.dumps(payload), encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('app.knowledge.worker_process.run_worker', worker)
    monkeypatch.setattr('app.knowledge.document_tools.effective_config', lambda: {'fixture': True})
    db = tmp_path / 'chat.db'
    engine = engine_at(db)
    identifier = engine.process_knowledge_source('Layanan.pdf', raw)['document_id']
    review = SOPReview(engine)
    detail = _convert(DocumentTools(engine, operator=True), review, identifier)
    assert _approve_fixture(review, detail)['status'] == 'Aktif'
    restarted = engine_at(db)
    boundary = V1KnowledgeBoundary(restarted, operator=True, provider='ollama', document_ids=[identifier])
    parts = fixture(answer='Wajib membawa paspor dan membayar 500 rupiah.')
    parts[2]['knowledge'] = boundary
    request = SimpleNamespace(user_input='Apa persyaratannya?', document_ids=[identifier], session_id='same')
    core = asyncio.run(parts[1].execute_v1(request, **parts[2]))
    answer = parts[3](core.payload, intent_name=core.intent_name)
    assert answer['grounding']['grounded'], answer
    assert 'Surat A' in answer['response'] and 'Surat B' in answer['response']
    assert 'paspor' not in answer['response'].casefold()
    assert answer['evidence'][0]['pages'] == [1, 2]
    assert engine.process_knowledge_source('Nama lain.pdf', raw)['status'] == 'DUPLICATE'
    assert V1KnowledgeBoundary(restarted, operator=False, provider='ollama').search_knowledge('Persyaratan') == []


def test_invalid_activity_structure_cannot_be_approved_or_read_by_chat(tmp_path, monkeypatch):
    import json
    import time
    from pathlib import Path
    from types import SimpleNamespace

    from test_review_publication_v1 import _pdf
    from test_sop_review import engine_at

    from app.knowledge.document_tools import DocumentReadError, DocumentTools
    from app.knowledge.sop_review import SOPReview
    from app.security.v1_knowledge import V1KnowledgeBoundary

    payload = {'status': 'COMPLETE', 'warnings': [], 'page_count': 1,
        'markdown': 'Tabel sumber', 'docling_json': {'fixture': True}, 'blocks': [
        table_block(1, [['2', 'Menyerahkan Surat A', 'Surat A', '', '', '']])]}
    def worker(args, **kwargs):
        Path(args[-1]).write_text(json.dumps(payload), encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('app.knowledge.worker_process.run_worker', worker)
    monkeypatch.setattr('app.knowledge.document_tools.effective_config', lambda: {'fixture': True})
    engine = engine_at(tmp_path / 'chat.db')
    identifier = engine.process_knowledge_source('Layanan.pdf', _pdf())['document_id']
    review = SOPReview(engine)
    tools = DocumentTools(engine, operator=True)
    tools.process(identifier, review.detail(identifier)['version_id'])
    deadline = time.monotonic() + 5
    while tools.status(identifier)['status'] in {'QUEUED', 'PROCESSING'} and time.monotonic() < deadline:
        time.sleep(.01)
    assert tools.status(identifier)['status'] == 'PARTIAL'
    detail = review.detail(identifier)
    assert detail['can_approve'] is False
    with pytest.raises(DocumentReadError, match='PARTIAL'):
        tools.baca_dokumen(identifier, detail['version_id'])
    with pytest.raises(ValueError):
        review.decide(identifier, detail['version_id'], 'approve', 'fixture-reviewer')
    assert V1KnowledgeBoundary(engine, operator=True, provider='ollama').search_knowledge('Surat A') == []
