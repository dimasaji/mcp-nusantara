"""Synthetic ingestion regressions and opt-in real CAPIL-01 OCR verification."""
import os
from pathlib import Path

import pytest
from test_sop_review import engine_at


def test_long_sop_is_indexed_without_rejecting_document_length(tmp_path):
    # Synthetic service text, not a published transcription of a real SOP.
    text = 'Kolom contoh NAMA SOP ; LAYANAN CONTOH\n' + '\n'.join(
        f'Bagian {index}: Pemohon menyerahkan Surat Contoh kepada petugas. '
        'Petugas memeriksa berkas dan mencatat hasil pemeriksaan.' for index in range(100))
    raw = text.encode()
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('layanan_contoh.txt', raw)
    assert run['status'] == 'READY', run.get('reason')
    assert engine.rag.get_document_info(run['document_id']).title == 'LAYANAN CONTOH'
    evidence = engine.search_knowledge('Surat Contoh')
    assert evidence and evidence[0].document_id == run['document_id']
    assert 'Surat Contoh' in evidence[0].source
    duplicate = engine.process_knowledge_source('layanan_contoh.txt', raw)
    assert duplicate['status'] == 'DUPLICATE'
    assert duplicate['document_id'] == run['document_id']


def test_pdf_mixed_native_and_scanned_pages_keep_searchable_page_provenance(tmp_path, monkeypatch):
    import subprocess

    import pymupdf

    scan = pymupdf.open()
    page = scan.new_page()
    page.insert_text((40, 80), 'Persyaratan kelahiran: Surat Keterangan Kelahiran.')
    image = page.get_pixmap().tobytes('png')
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), 'Nama SOP: Pelayanan Akta Kelahiran. Dokumen contoh halaman pertama.')
    page = document.new_page()
    page.insert_image(page.rect, stream=image)
    monkeypatch.setenv('NUSANTARA_TESSERACT_CMD', 'fixture-tesseract')
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs:
        subprocess.CompletedProcess(args[0], 0, b'Persyaratan kelahiran: Surat Keterangan Kelahiran.\n', b''))
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('mixed.pdf', document.tobytes())
    assert run['status'] == 'READY', run.get('reason')
    stored = engine.rag.get_document_info(run['document_id'])
    assert 'Surat Keterangan Kelahiran' in stored.source
    assert [p['page'] for p in stored.metadata['source_pages']] == [1, 2]
    for page in stored.metadata['source_pages']:
        assert stored.source[page['start']:page['end']].strip()
    assert 'Surat Keterangan Kelahiran' in stored.source[
        stored.metadata['source_pages'][1]['start']:stored.metadata['source_pages'][1]['end']]


def test_low_alphabet_garbage_still_fails_quality_screen(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    result = engine.process_knowledge_source('broken.txt', b'abcde ' * 1500)
    assert result['status'] == 'FAILED'
    assert result['reason'] == 'EXTRACTED_TEXT_QUALITY_CHECK_FAILED'
    assert engine.list_documents().documents == []


def test_standalone_multiline_sop_title_still_works(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('scan.txt',
        b'Nama S.O.P\nLAYANAN KELAHIRAN\nPersyaratan layanan tersedia dalam sumber dokumen.')
    assert run['status'] == 'READY'
    assert engine.rag.get_document_info(run['document_id']).title == 'LAYANAN KELAHIRAN'


@pytest.mark.parametrize('short_text', ['', 'Lampiran'])
def test_native_pdf_with_blank_or_short_native_page_does_not_require_ocr(tmp_path, monkeypatch, short_text):
    import shutil

    import pymupdf

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((40, 80), 'Nama SOP: Pelayanan Kelahiran. Informasi persyaratan layanan warga.')
    page = document.new_page()
    if short_text:
        page.insert_text((40, 80), short_text)
    monkeypatch.delenv('NUSANTARA_TESSERACT_CMD', raising=False)
    monkeypatch.setattr(shutil, 'which', lambda name: None)
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('native.pdf', document.tobytes())
    assert run['status'] == 'READY', run.get('reason')
    stored = engine.rag.get_document_info(run['document_id'])
    pages = stored.metadata['source_pages']
    assert [p['page'] for p in pages] == [1, 2]
    assert stored.source[pages[1]['start']:pages[1]['end']].strip() == short_text


@pytest.mark.skipif(os.getenv('NUSANTARA_NATIVE_OCR_TEST') != '1',
                    reason='Explicit native Tesseract ind+eng run only')
def test_native_capil01_pdf_upload_ocr_index_and_pages(tmp_path):
    from app.knowledge.sop_review import SOPReview
    from app.security.v1_knowledge import V1KnowledgeBoundary

    source = Path(__file__).parents[1] / (
        'reports/remediation/20261027-priority-fixes/database-before/0/source-documents/'
        'f9ad8a5dbdc7e16570122966ccad6dcfc3c36f447385789ae9b051a0838d7f1f.pdf')
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('CAPIL_01.pdf', source.read_bytes())
    assert run['status'] == 'READY', run.get('reason')
    doc = engine.rag.get_document_info(run['document_id'])
    assert 'Akta Kelahiran' in doc.title
    assert [p['page'] for p in doc.metadata['source_pages']] == [1, 2, 3]
    assert all(doc.source[p['start']:p['end']].strip() for p in doc.metadata['source_pages'])
    assert engine.search_knowledge('Akta Kelahiran')[0].document_id == run['document_id']
    assert engine.process_knowledge_source('CAPIL_01.pdf', source.read_bytes())['status'] == 'DUPLICATE'
    detail = SOPReview(engine).detail(run['document_id'])
    assert detail['status'] == 'Menunggu ekstraksi'
    assert detail['can_approve'] is False
    assert detail['metadata_confirmed'] is False
    assert V1KnowledgeBoundary(engine, operator=True, provider='ollama').search_knowledge('Akta Kelahiran') == []
