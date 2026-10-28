from test_selected_pdf_chat import table_pdf


def test_activity_grid_regions_use_physical_pdf_pages(tmp_path):
    from app.knowledge.docling_layout import activity_grid_regions
    source = tmp_path / 'table.pdf'
    source.write_bytes(table_pdf())
    regions = activity_grid_regions(source)
    assert set(regions) == {1, 2}  # Physical PDF page numbers, matching Docling Page.page_no.
    assert regions[1][0] == (20., 40., 1080., 160.)
    assert regions[2][0] == (20., 40., 1080., 220.)


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
    import pymupdf
    from app.knowledge.docling_layout import normalize_activity_grids
    from app.knowledge.document_answers import document_answer_facts
    from types import SimpleNamespace
    pdf = pymupdf.open(stream=table_pdf(), filetype='pdf')
    pdf[1].insert_text((20, 400), 'Tarif layanan Rp. 15000. WA: 08123456789.')
    source = tmp_path / 'footnotes.pdf'; pdf.save(source)
    result = normalize_activity_grids({'status': 'COMPLETE', 'warnings': [], 'blocks': [], 'docling_json': {}}, source)
    assert any('Tarif layanan' in b['content'] for b in result['blocks'])
    item = SimpleNamespace(title='Contoh', document_id='x', score=1., source=result['markdown'],
        metadata={'sop_rows': result['activity_rows'], 'full_document_text': result['full_document_text']})
    assert document_answer_facts('Berapa biayanya?', [item]) is None
    assert document_answer_facts('Nomor WhatsApp petugas?', [item]) is None
