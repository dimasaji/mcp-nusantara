import os
from pathlib import Path

import pytest
from test_selected_pdf_chat import table_pdf


@pytest.mark.parametrize('number_header,quality_header', [
    ('No.', 'Kelengkapan'), ('Pelaksana', 'Kelengkapan'), ('No.', 'Mutu Baku'),
])
def test_scanned_activity_grid_uses_image_lines_and_ocr_headers(number_header, quality_header):
    """A raster PDF has no vector lines; OCR labels identify the procedure grid."""
    pytest.importorskip('docling_core')
    pytest.importorskip('cv2')
    pytest.importorskip('PIL')
    from types import SimpleNamespace

    import pymupdf
    from docling_core.types.doc import BoundingBox, CoordOrigin
    from PIL import Image

    from app.knowledge.docling_layout import scanned_activity_grid_regions

    pdf = pymupdf.open(stream=table_pdf(), filetype='pdf')
    pixmap = pdf[0].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
    image = Image.frombytes('RGB', [pixmap.width, pixmap.height], pixmap.samples)
    def cell(text, left, right):
        box = BoundingBox(l=left, t=50, r=right, b=70, coord_origin=CoordOrigin.TOPLEFT)
        return SimpleNamespace(text=text, rect=SimpleNamespace(to_bounding_box=lambda: box))
    page = SimpleNamespace(size=SimpleNamespace(width=1100, height=500),
        cells=[cell(number_header, 22, 55), cell('Kegiatan', 65, 200),
               cell(quality_header, 395, 530)], get_image=lambda scale: image)
    regions = scanned_activity_grid_regions(page)
    assert len(regions) == 1
    assert regions[0] == pytest.approx((20, 40, 1080, 160), abs=2)
    page.cells = [cell('Nama', 22, 55), cell('Alamat', 65, 200)]
    assert scanned_activity_grid_regions(page) == []


def test_activity_grid_regions_use_physical_pdf_pages(tmp_path):
    from app.knowledge.docling_layout import activity_grid_regions
    source = tmp_path / 'table.pdf'
    source.write_bytes(table_pdf())
    regions = activity_grid_regions(source)
    assert set(regions) == {1, 2}  # Physical PDF page numbers, matching Docling Page.page_no.
    assert regions[1][0] == (20., 40., 1080., 160.)
    assert regions[2][0] == (20., 40., 1080., 220.)


def test_unrelated_table_on_same_page_does_not_satisfy_activity_grid():
    from app.knowledge.docling_layout import missing_activity_grids

    detected = {2: [(20, 100, 800, 550)]}
    blocks = [{'type': 'table', 'page_numbers': [2], 'source_regions': [
        {'page': 2, 'bbox': [20, 10, 800, 90]}]}]
    assert missing_activity_grids(blocks, detected) == [2]
    blocks[0]['source_regions'][0]['bbox'] = [20, 100, 800, 550]
    assert missing_activity_grids(blocks, detected) == []


def test_ruled_normalization_preserves_cells_and_links_continuation_pages(tmp_path):
    from app.knowledge.docling_layout import normalize_activity_grids
    source = tmp_path / 'table.pdf'
    source.write_bytes(table_pdf())
    payload = {'status': 'COMPLETE', 'warnings': [], 'blocks': [], 'docling_json': {'original': True}}
    result = normalize_activity_grids(payload, source)
    assert result['docling_json'] == {'original': True}
    assert result['activity_rows'][0]['kelengkapan'] == 'Surat Pengantar'
    assert result['activity_rows'][2]['keterangan'] == '7 Hari Kerja'
    assert result['blocks'][0]['related_pages'] == [2]
    assert result['blocks'][1]['page_numbers'] == [2]


def test_footnotes_outside_grid_remain_available_for_absence_checks(tmp_path):
    from types import SimpleNamespace

    import pymupdf

    from app.knowledge.docling_layout import normalize_activity_grids
    from app.knowledge.document_answers import document_answer_facts
    pdf = pymupdf.open(stream=table_pdf(), filetype='pdf')
    pdf[1].insert_text((20, 400), 'Tarif layanan Rp. 15000. WA: 08123456789.')
    source = tmp_path / 'footnotes.pdf'
    pdf.save(source)
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [], 'docling_json': {}}, source)
    assert any('Tarif layanan' in b['content'] for b in result['blocks'])
    item = SimpleNamespace(title='Contoh', document_id='x', score=1., source=result['markdown'],
        metadata={'sop_rows': result['activity_rows'], 'full_document_text': result['full_document_text']})
    assert document_answer_facts('Berapa biayanya?', [item]) is None
    assert document_answer_facts('Nomor WhatsApp petugas?', [item]) is None


@pytest.mark.skipif(os.getenv('NUSANTARA_NATIVE_DOCLING_TEST') != '1',
                    reason='Explicit native Docling run with local models and ind+eng OCR only')
def test_native_scan_reconstructs_both_activity_pages(tmp_path):
    import json

    from app.knowledge.docling_worker import convert

    source = Path(__file__).parents[1] / (
        'reports/remediation/20261027-priority-fixes/database-before/0/source-documents/'
        'f9ad8a5dbdc7e16570122966ccad6dcfc3c36f447385789ae9b051a0838d7f1f.pdf')
    output = tmp_path / 'conversion.json'
    convert(source, output)
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['status'] == 'COMPLETE', payload['warnings']
    assert payload['effective_options']['activity_grid_pages'] == [2, 3]
    table_pages = {p for block in payload['blocks'] if block['type'] == 'table'
                   for p in block['page_numbers']}
    assert {2, 3}.issubset(table_pages)
    assert payload['page_count'] == 3
    assert payload['docling_json']['pages']
