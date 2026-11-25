# KNOWLEDGE_INGESTION_TEST_REPORT

Status: `PARTIAL / BLOCKED`
Checked at: `2026-11-23T00:25:36Z`

## Lingkup

Tidak ada perubahan kode ingestion pada sesi remediation ini. Bukti yang dipakai adalah hasil verifikasi ECC/Post-ECC dan status runtime saat ini.

## Hasil

- `tests/test_knowledge_preparation.py` dan test preparation terkait: `15 passed, 1 skipped` pada `/data/tmp/opencode/fix_prep_final.txt`.
- `tests/test_document_answers.py`: PASS dalam targeted regression.
- `tests/test_chat_source_recovery.py`: `19 passed` setelah perbaikan grounding.
- `tests/test_sop_ingestion.py`: PASS dalam regression terkait.
- `tests/test_sop_source_pages.py::test_review_counts_original_pdf_pages_without_ocr_offsets`: FAIL karena `.dev/checkpoints/r2-20261007/health-gate/source-before/app/api/routes.py` tidak tersedia.
- `tests/test_web_evidence_pipeline.py`: 4 FAIL karena `data/knowledge/official_sources/ktp_el/manifest.json` tidak tersedia.

## Runtime evidence

- `/data/tmp/opencode/remediation_runtime_status.txt`: `knowledge_db=PRESENT`, `indobert_model_dir=MISSING`, `worker_scripts=MISSING`.
- `/data/tmp/opencode/remediation_sop_status.txt`: `knowledge_documents=0`, `piak03_knowledge_rows=0`, `piak03_pdf_in_repo=MISSING`.

## Kesimpulan

Jalur preparation dan jawaban berbasis fixture/knowledge synthetic terverifikasi. Ingestion PIAK-03 nyata, OCR/IndoBERT worker, dan artifacts historis tidak tersedia, sehingga STATUS tidak boleh dinaikkan menjadi PASS produksi.
