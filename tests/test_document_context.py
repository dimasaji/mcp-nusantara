from app.knowledge.document_context import project_activity_blocks, select_blocks


def test_table_projection_keeps_actual_rows_and_header_labels():
    doc = {'blocks': [{'block_id': 'grid', 'type': 'table', 'content': 'Full table', 'page_numbers': [2]}],
           'activity_rows': [{'number': 1, 'activity': 'Menyerahkan Berkas X', 'kelengkapan': 'Berkas X',
                              'waktu': '', 'output': 'Berkas X', 'keterangan': '', 'block_id': 'grid'},
                             {'number': 2, 'activity': 'Memeriksa Berkas X', 'kelengkapan': 'Berkas X',
                              'waktu': '7 menit', 'output': 'Hasil pemeriksaan', 'keterangan': '', 'block_id': 'grid'}]}
    blocks = project_activity_blocks(doc, 'Bagaimana prosesnya?')
    assert 'Memeriksa Berkas X' in blocks[0]['content']
    assert blocks[0]['selected_columns'] == ['Uraian Kegiatan']
    assert blocks[0]['page_numbers'] == [2]
    requirements = project_activity_blocks(doc, 'Bawa apa saja?')
    assert requirements[0]['selected_rows'] == [1]
    assert 'Kelengkapan pemohon pada tahap pengajuan: Berkas X' in requirements[0]['content']


def test_budget_selection_discloses_omissions_without_cutting_a_table():
    blocks = [{'block_id': 'metadata', 'type': 'text', 'content': 'x' * 5000, 'page_numbers': [1]},
              {'block_id': 'table', 'type': 'table', 'content': '|Kelengkapan|\n|Berkas X|', 'page_numbers': [2]}]
    text, included, omitted = select_blocks(blocks, 'Apa persyaratannya?', 4096)
    assert [b['block_id'] for b in included] == ['table']
    assert omitted == ['metadata']
    assert '1 blok lain tidak dimuat' in text
    assert blocks[1]['content'] in text


def test_model_citations_must_belong_to_the_supplied_blocks_and_pages():
    from app.knowledge.document_citations import citations_supported
    blocks = [{'block_id': 'table-2', 'page_numbers': [2]}]
    assert citations_supported('Menurut halaman 2 [blok table-2].', blocks)
    assert not citations_supported('Menurut halaman 3.', blocks)
    assert not citations_supported('[blok table-9]', blocks)
    assert not citations_supported('Lihat halaman 2 dan 15.', blocks)
    assert not citations_supported('Lihat halaman 2-15.', blocks)
    assert not citations_supported('Lihat blok table-9.', blocks)
