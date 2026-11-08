"""Public intake/extraction contracts with the real Haystack cleaner."""
import json
from pathlib import Path

from test_sop_review import engine_at


def test_upload_cleans_before_indexing_and_retains_original(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    original = 'Persyaratan:   Surat Permohonan.\n\n1.  Serahkan berkas.\n2.  Tunggu 3 hari kerja.'
    result = engine.process_knowledge_source('sop.txt', original.encode())
    assert result['status'] == 'READY', result
    doc = engine.rag.get_document_info(result['document_id'])
    assert doc.source == 'Persyaratan: Surat Permohonan.\n\n1. Serahkan berkas.\n2. Tunggu 3 hari kerja.'
    artifact = doc.metadata['text_cleaning']
    raw = json.loads((tmp_path / artifact['directory'] / artifact['raw_file']).read_text())
    cleaned = json.loads((tmp_path / artifact['directory'] / artifact['cleaned_file']).read_text())
    assert raw['text'] == original
    assert cleaned['text'] == doc.source
    assert raw['document_id'] == cleaned['document_id'] == result['document_id']
    assert engine.process_knowledge_source('sop.txt', original.encode())['status'] == 'DUPLICATE'


def test_docling_cleaning_reaches_review_without_changing_table_sources(tmp_path, monkeypatch):
    import time
    from types import SimpleNamespace

    from test_review_publication_v1 import _pdf

    from app.knowledge.document_tools import DocumentTools
    from app.knowledge.sop_review import SOPReview

    table = '|No.|Kegiatan|\n|---|---|\n|1|Periksa   Surat Permohonan|'
    payload = {'status': 'COMPLETE', 'warnings': [], 'page_count': 1,
        'markdown': 'Persyaratan:   Surat Permohonan.\n\n' + table,
        'full_document_text': 'Persyaratan:   Surat Permohonan.',
        'docling_json': {'fixture': True},
        'blocks': [
            {'block_id': 'text', 'type': 'text', 'content': 'Persyaratan:   Surat Permohonan.', 'page_numbers': [1]},
            {'block_id': 'table', 'type': 'table', 'content': table, 'page_numbers': [1],
             'table_data': {'num_rows': 2, 'num_cols': 2}}]}

    def worker(args, **kwargs):
        Path(args[-1]).write_text(json.dumps(payload), encoding='utf-8')
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr('app.knowledge.worker_process.run_worker', worker)
    monkeypatch.setattr('app.knowledge.document_tools.effective_config', lambda: {'fixture': True})
    engine = engine_at(tmp_path / 'chat.db')
    result = engine.intake_document('sop.pdf', _pdf())
    identifier = result['document_id']
    tools = DocumentTools(engine, operator=True)
    deadline = time.monotonic() + 10
    while tools.status(identifier)['status'] in {'QUEUED', 'PROCESSING'} and time.monotonic() < deadline:
        time.sleep(.01)
    assert tools.status(identifier)['status'] == 'COMPLETE', tools.status(identifier)
    detail = SOPReview(engine).detail(identifier)
    document = tools.baca_dokumen(identifier, detail['version_id'])
    assert document['blocks'][0]['content'] == 'Persyaratan: Surat Permohonan.'
    assert document['blocks'][1] == payload['blocks'][1]
    assert document['raw_extraction']['blocks'][0]['content'] == 'Persyaratan:   Surat Permohonan.'
    assert document['text_cleaning']['profile'].startswith('haystack-')
    assert document['docling_json'] == payload['docling_json']
    assert detail['approval'] is None
    reopened = DocumentTools(engine_at(tmp_path / 'chat.db'), operator=True)
    assert reopened.baca_dokumen(identifier, detail['version_id'])['raw_extraction'] == document['raw_extraction']


def test_cleaner_preserves_structure_and_is_idempotent():
    from app.knowledge.text_cleaning import clean_extraction, clean_text

    original = ('Judul   SOP\r\n\r\n  - Surat   Permohonan  \r\n'
        '|Berkas|Durasi|\r\n|Surat   asli|3 hari|\r\n'
        '```text\r\na   b\r\n```\r\n    teks   indentasi\r\n')
    expected = ('Judul SOP\r\n\r\n  - Surat Permohonan  \r\n'
        '|Berkas|Durasi|\r\n|Surat   asli|3 hari|\r\n'
        '```text\r\na   b\r\n```\r\n    teks   indentasi\r\n')
    assert clean_text(original) == expected
    payload = {'blocks': [{'type': 'text', 'content': original, 'page_numbers': [2]}],
               'markdown': original, 'activity_rows': [{'number': 1, 'activity': 'Periksa   surat'}]}
    cleaned = clean_extraction(payload)
    assert cleaned['raw_extraction']['blocks'][0]['content'] == original
    assert payload['blocks'][0]['content'] == original
    assert clean_extraction(cleaned) == cleaned
    assert clean_text('') == ''


def test_cleaned_pdf_offsets_follow_physical_pages(tmp_path):
    import pymupdf

    pdf = pymupdf.open()
    pdf.new_page().insert_text((30, 50), 'Halaman Pertama:   persyaratan surat permohonan untuk layanan warga.')
    pdf.new_page().insert_text((30, 50), 'Halaman Kedua:   durasi penyelesaian adalah 3 hari kerja.')
    engine = engine_at(tmp_path / 'chat.db')
    result = engine.process_knowledge_source('sop.pdf', pdf.tobytes())
    assert result['status'] == 'READY', result
    doc = engine.rag.get_document_info(result['document_id'])
    first, second = doc.metadata['source_pages']
    assert doc.source[first['start']:first['end']].startswith('Halaman Pertama: persyaratan')
    assert doc.source[second['start']:second['end']].startswith('Halaman Kedua: durasi')
    assert first['page'] == 1 and second['page'] == 2
    assert second['start'] == first['end'] + 1
    raw = json.loads((tmp_path / 'text-extractions' / doc.metadata['text_cleaning']['raw_file']).read_text())
    assert 'Pertama:   persyaratan' in raw['pages'][0]
    assert 'Kedua:   durasi' in raw['pages'][1]


def test_intake_disables_haystack_telemetry_before_import():
    import os
    import subprocess
    import sys

    script = ('from app.knowledge.text_cleaning import clean_text; '
              'clean_text("Surat   permohonan"); '
              'from haystack.telemetry import _telemetry; '
              'assert _telemetry.telemetry is None')
    subprocess.run([sys.executable, '-c', script],
        env={**os.environ, 'HAYSTACK_TELEMETRY_ENABLED': 'true'}, check=True,
        capture_output=True, timeout=30)


def test_cleaner_failure_is_visible_and_does_not_publish(tmp_path, monkeypatch):
    from haystack.components.preprocessors.document_cleaner import DocumentCleaner

    def unavailable(self, documents):
        raise RuntimeError('HAYSTACK_CLEANING_FAILED')

    monkeypatch.setattr(DocumentCleaner, 'run', unavailable)
    engine = engine_at(tmp_path / 'chat.db')
    result = engine.process_knowledge_source('sop.txt',
        b'Persyaratan:   Surat Permohonan kepada petugas layanan warga.')
    assert result['status'] == 'FAILED'
    assert 'HAYSTACK_CLEANING_FAILED' in result['reason']
    assert engine.rag.list_documents().total == 0
