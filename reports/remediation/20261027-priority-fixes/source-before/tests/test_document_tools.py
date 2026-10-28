import pytest

from app.knowledge.document_tools import DocumentTools, DocumentReadError
from test_sop_review import engine_at


def test_document_tools_access_version_and_unprocessed_are_distinct(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    run = engine.process_knowledge_source('sop.txt', b'Persyaratan layanan warga: surat permohonan kepada petugas.')
    from app.knowledge.sop_review import SOPReview
    detail = SOPReview(engine).detail(run['document_id'])
    tools = DocumentTools(engine, operator=True)
    found = tools.cari_dokumen('sop')
    assert found[0]['document_id'] == run['document_id']
    assert found[0]['processing_status'] == 'NOT_PROCESSED'
    with pytest.raises(DocumentReadError, match='DOCUMENT_ACCESS_DENIED'):
        DocumentTools(engine, operator=False).cari_dokumen('sop')
    with pytest.raises(DocumentReadError, match='DOCUMENT_NOT_FOUND'):
        tools.baca_dokumen('missing', detail['version_id'])
    with pytest.raises(DocumentReadError, match='DOCUMENT_VERSION_NOT_FOUND'):
        tools.baca_dokumen(run['document_id'], '0' * 64)
    with pytest.raises(DocumentReadError, match='DOCUMENT_NOT_PROCESSED'):
        tools.baca_dokumen(run['document_id'], detail['version_id'])


def test_conversion_cache_page_provenance_and_approval_are_independent(tmp_path, monkeypatch):
    import json
    import time
    from pathlib import Path
    from types import SimpleNamespace
    import pymupdf
    from app.knowledge.sop_review import SOPReview

    engine = engine_at(tmp_path / 'chat.db')
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((30, 50), 'SOP fixture pelayanan: persyaratan surat permohonan kepada petugas.')
    run = engine.process_knowledge_source('sop.pdf', pdf.tobytes())
    detail = SOPReview(engine).detail(run['document_id'])
    calls = []

    def worker(args, **kwargs):
        calls.append(args)
        Path(args[-1]).write_text(json.dumps({'status': 'COMPLETE', 'warnings': [], 'page_count': 1,
            'markdown': '|Berkas|Waktu|\n|Surat permohonan|3 hari|', 'docling_json': {'fixture': True},
            'blocks': [{'block_id': '#/tables/0', 'type': 'table', 'content': '|Berkas|Waktu|\n|Surat permohonan|3 hari|',
                        'page_numbers': [1], 'table_data': {'num_rows': 2, 'num_cols': 2}}]}), encoding='utf-8')
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr('app.knowledge.worker_process.run_worker', worker)
    tools = DocumentTools(engine, operator=True)
    tools.process(run['document_id'], detail['version_id'])
    deadline = time.monotonic() + 3
    while tools.status(run['document_id'])['status'] in {'QUEUED', 'PROCESSING'} and time.monotonic() < deadline:
        time.sleep(.01)
    result = tools.baca_halaman(run['document_id'], detail['version_id'], 1)
    assert result['blocks'][0]['table_data']['num_cols'] == 2
    assert result['blocks'][0]['page_numbers'] == [1]
    with pytest.raises(DocumentReadError, match='DOCUMENT_PAGE_INVALID'):
        tools.baca_halaman(run['document_id'], detail['version_id'], 0)
    tools.process(run['document_id'], detail['version_id'])
    tools.evidence(run['document_id'], detail['version_id'])
    assert len(calls) == 1
    assert SOPReview(engine).detail(run['document_id'])['content_ok'] is False

    # A failed reprocessing attempt retains the preceding completed payload,
    # but must expose the latest failure instead of serving it as fresh success.
    import subprocess
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('docling', 600)
    monkeypatch.setattr('app.knowledge.worker_process.run_worker', timeout)
    tools.process(run['document_id'], detail['version_id'], force=True)
    deadline = time.monotonic() + 3
    while tools.status(run['document_id'])['status'] in {'QUEUED', 'PROCESSING'} and time.monotonic() < deadline:
        time.sleep(.01)
    with pytest.raises(DocumentReadError, match='DOCUMENT_EXTRACTION_FAILED'):
        tools.baca_dokumen(run['document_id'], detail['version_id'])
    assert tools.inspect(run['document_id'], detail['version_id'])['status'] == 'FAILED'
    with engine._pipeline_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM document_extractions WHERE status='COMPLETE'").fetchone()[0] == 1
