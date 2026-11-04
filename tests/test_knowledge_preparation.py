"""Exercise preparation through the same ingestion and search interface as callers."""
from pathlib import Path

import pytest

from app.knowledge.engine import KnowledgeEngine
from app.knowledge.rag import RAG
from app.knowledge.schemas import KnowledgeBaseConfig
from app.knowledge.store import SQLiteVectorStore


def engine_at(tmp_path):
    return KnowledgeEngine(rag=RAG(
        config=KnowledgeBaseConfig(embedding_model='fixture', embedding_dimension=3),
        vector_store=SQLiteVectorStore(str(tmp_path / 'chat.db')),
        embedding_func=lambda text: [1.0, 0.0, 0.0],
    ))


def test_ingestion_cleans_controls_preserves_steps_and_is_searchable(tmp_path):
    engine = engine_at(tmp_path)
    raw = ('Nama SOP: PERMOHONAN DATA PRIBADI\n'
           '1. Surat\u00a0Permohonan\x00 diserahkan kepada petugas.\n'
           '2. Petugas memeriksa berkas.\nWaktu: 3 Hari Kerja.').encode()
    result = engine.process_knowledge_source('layanan.txt', raw)
    assert result['status'] == 'READY'
    info = engine.rag.get_document_info(result['document_id'])
    assert '1. Surat Permohonan  diserahkan kepada petugas.\n2.' in info.source
    assert info.metadata['knowledge_preparation']['status'] == 'VALID'
    assert info.metadata['source_authority'] == 'UNVERIFIED'
    assert Path(result['source_path']).read_bytes() == raw
    found = engine.search_knowledge('Surat Permohonan', filter={'document_ids': [result['document_id']]})
    assert found and found[0].document_id == result['document_id']
    assert '3 Hari Kerja' in found[0].source


@pytest.mark.parametrize('text', ['\ufffd' * 150, '\x00' * 150,
                                     'a' * 150, '!!! ??? ' * 40])
def test_unusable_text_is_retained_but_never_indexed(tmp_path, text):
    engine = engine_at(tmp_path)
    raw = text.encode()
    result = engine.process_knowledge_source('rusak.txt', raw)
    assert result['status'] == 'FAILED'
    assert engine.rag.list_documents().total == 0
    assert Path(result['source_path']).read_bytes() == raw


def test_long_document_is_not_rejected_for_having_a_small_alphabet(tmp_path):
    engine = engine_at(tmp_path)
    raw = ('Surat permohonan diserahkan ke petugas. Waktu layanan 3 Hari Kerja.\n' * 120).encode()
    result = engine.process_knowledge_source('panjang.txt', raw)
    assert result['status'] == 'READY'
    assert engine.rag.get_document_info(result['document_id']).source == raw.decode()


def test_two_pdf_pages_keep_physical_citations_after_sanitation(tmp_path):
    import io

    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    for text in [b'Persyaratan: Surat\xa0Permohonan diserahkan kepada petugas.',
                 b'Waktu layanan: 3 Hari Kerja. Petugas memeriksa berkas.']:
        page = writer.add_blank_page(width=600, height=800)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
            NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
            DictionaryObject({NameObject('/F1'): font})})
        stream = DecodedStreamObject()
        stream.set_data(b'BT /F1 12 Tf 50 750 Td (' + text + b') Tj ET')
        page[NameObject('/Contents')] = stream
    output = io.BytesIO()
    writer.write(output)
    engine = engine_at(tmp_path)
    result = engine.process_knowledge_source('dua-halaman.pdf', output.getvalue())
    assert result['status'] == 'READY'
    info = engine.rag.get_document_info(result['document_id'])
    pages = info.metadata['source_pages']
    assert info.metadata['knowledge_preparation']['changed_characters'] > 0
    assert [p['page'] for p in pages] == [1, 2]
    assert info.source[pages[1]['start']:pages[1]['end']].startswith('Waktu layanan: 3 Hari Kerja.')
    found = engine.search_knowledge('Waktu layanan', filter={'document_ids': [result['document_id']]})
    assert found and 2 in found[0].metadata['citation_pages']


def test_caller_cannot_supply_page_numbers_for_text_source(tmp_path):
    engine = engine_at(tmp_path)
    result = engine.process_knowledge_source('teks.txt',
        b'Persyaratan layanan: Surat Permohonan. Waktu layanan 3 Hari Kerja.',
        source_metadata={'source_pages': [{'page': 999, 'start': 0, 'end': 500}]})
    assert result['status'] == 'READY'
    info = engine.rag.get_document_info(result['document_id'])
    assert info.metadata.get('source_pages', []) == []


def test_windows_table_rows_do_not_gain_blank_lines(tmp_path):
    engine = engine_at(tmp_path)
    raw = b'| Langkah | Prosedur |\r\n| --- | --- |\r\n| 1 | Serahkan surat permohonan |\r\n| 2 | Periksa berkas |'
    result = engine.process_knowledge_source('tabel.md', raw)
    assert result['status'] == 'READY'
    info = engine.rag.get_document_info(result['document_id'])
    assert info.source.splitlines() == [
        '| Langkah | Prosedur | ', '| --- | --- | ',
        '| 1 | Serahkan surat permohonan | ', '| 2 | Periksa berkas |']
    assert len(info.source) == len(raw.decode())
