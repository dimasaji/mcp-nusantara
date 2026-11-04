from test_selected_pdf_chat import table_pdf


def test_scanned_grid_is_detected_without_native_text(tmp_path):
    import pymupdf
    from app.knowledge.docling_layout import layout_grid_regions
    vector = pymupdf.open()
    page = vector.new_page(width=600, height=500)
    for x in range(30, 571, 60):
        page.draw_line((x, 50), (x, 450), color=(0, 0, 0), width=2)
    for y in range(50, 451, 50):
        page.draw_line((30, y), (570, y), color=(0, 0, 0), width=2)
    raster = pymupdf.open()
    scanned = raster.new_page(width=600, height=500)
    scanned.insert_image(scanned.rect, stream=page.get_pixmap().tobytes('png'))
    path = tmp_path / 'scan.pdf'
    raster.save(path)
    vector.close()
    raster.close()
    regions = layout_grid_regions(path)
    assert 1 in regions
    x0, y0, x1, y1 = regions[1][0]
    assert abs(x0 - 30) < 5 and abs(y0 - 50) < 5
    assert abs(x1 - 570) < 5 and abs(y1 - 450) < 5


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
