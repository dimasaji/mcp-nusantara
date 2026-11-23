# SOP_E2E_VERIFICATION_REPORT

Status: `BLOCKED`
Checked at: `2026-11-23T00:12:41Z`

## Evidence

Sumber: `/data/tmp/opencode/remediation_sop_status.txt`

- `piak03_pdf_in_repo=MISSING`
- `piak03_any_pdf=MISSING`
- `knowledge_documents=0`
- `piak03_knowledge_rows=0`

## Runtime

- Ollama tidak tersedia (`ollama_binary=UNAVAILABLE`, `ollama_api_http=000UNAVAILABLE`).
- IndoBERT worker dan model tidak tersedia.
- Tidak ada model atau PDF pribadi yang diunduh/dipindahkan ke repo.

## Pengujian yang tersedia

- Chat SOP diuji memakai fixture synthetic/offline.
- Golden PIAK-03 chat test lulus dengan `full_document_text` fixture.
- 12 failure kontak pada `tests/test_ncp_v1_chat_contract.py` sudah diperbaiki dengan menjaga source mentah tidak dianggap sebagai klaim terverifikasi.
- Ingestion nyata dan E2E PDF -> OCR -> retrieve -> model -> jawaban tidak dijalankan.

## Kesimpulan

Status SOP E2E nyata tetap `BLOCKED`. Laporan ini hanya menyatakan verifikasi fixture, bukan bukti operasional produksi.
