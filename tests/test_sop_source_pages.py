"""Physical pages remain navigable when OCR has no source-text offsets."""
import io

from pypdf import PdfWriter
from test_sop_review import engine_at

from app.knowledge.sop_review import SOPReview


def test_review_counts_original_pdf_pages_without_ocr_offsets(tmp_path, monkeypatch):
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=600, height=800)
    output = io.BytesIO()
    writer.write(output)
    engine = engine_at(tmp_path / 'chat.db')
    # Simulate the OCR adapter returning text with unknown physical offsets.
    monkeypatch.setattr(engine, '_extract_pipeline_text',
                        lambda name, raw: 'Persyaratan surat permohonan. Petugas memeriksa kelengkapan berkas.')
    run = engine.process_knowledge_source('scan.pdf', output.getvalue())
    assert run['status'] == 'READY'
    detail = SOPReview(engine).detail(run['document_id'])
    assert detail['pages'] == []
    assert detail['source_page_count'] == 3
    assert detail['can_approve'] is False
