# SOP Knowledge Test Report

Tanggal observasi: 2026-11-22  
Repository: `/data/home/mcp-nusantara`  
Branch: `codex/fullroot-control-20261007`

## Status singkat

`SOP/RAG END-TO-END: BLOCKED / NOT VERIFIED`  
`API BOUNDARY CONTRACTS (OFFLINE): sebagian PASS`

Semua uji memakai data sintetis. Tidak ada data kependudukan, DB nyata, token produksi, atau kunci API yang dipakai/diunggah.

## Probe runtime dengan data sintetis

| Endpoint | Hasil | Bukti |
| --- | --- | --- |
| `POST /v1/documents/ingest` | `400` | `[Errno 2] No such file or directory: '/data/home/mcp-nusantara/nusantara-models/.venv/bin/python'` |
| `POST /v1/knowledge/search` | `500` | `Terjadi kesalahan internal layanan. Coba lagi atau hubungi operator.`; traceback `app/knowledge/indobert_embedding.py:42` → `app/language/semantic/indobert_client.py:107 encode` → `start()` baris `59` |
| `POST /v1/chat` tanpa Ollama | `503` | `PROVIDER_UNAVAILABLE` |

## Akar blocker

- `nusantara-models/` tidak ada di checkout.
- `git ls-files nusantara-models` menghasilkan output kosong.
- `Dockerfile:18` menulis `COPY nusantara-models/indobert_worker.py ./nusantara-models/indobert_worker.py`.
- Runtime mengharapkan python worker di `nusantara-models/.venv/bin/python` dan worker di `NUSANTARA_INDOBERT_WORKER`.
- Tidak ada file `.db` di checkout, termasuk `data/knowledge/nusantara_knowledge.db`.
- Ollama tidak berjalan, sehingga generasi LLM nyata tidak dapat diverifikasi.

Worker tidak dibuat-buat dan fallback tidak ditambahkan tanpa persetujuan, karena itu akan mengubah kontrak runtime/model.

## Bukti pengujian offline

| Gate | Sebelum | Sesudah perbaikan test harness |
| --- | --- | --- |
| `tests/test_v1_sop_boundary.py` | `11 failed, 8 passed` | `19 passed` |
| Subset V1 yang memakai fixture together | — | `34 passed, 3 failed`; 3 failure = session-id drift P2-3 (`web`, `other`, `web-aaaa...`) |
| `tests/test_openrouter_provider.py` | `2 failed` karena `CHAT_SESSION_PATTERN` tidak ada di namespace AST | `37 passed` |
| `tests/test_langchain_adapter.py` + `tests/test_langgraph_workflow.py` | adapter `None` / `AttributeError` | `7 passed, 1 failed`; failure tersisa `assert 0 >= 1` karena knowledge store kosong |
| `tests/test_langchain_adapter.py` + `tests/test_synthetic_rag_fixture.py` | data-dependent retrieval gagal dengan store kosong | `7 passed`; fixture sintetis mengisi store dengan dokumen uji `synthetic-sop-1` |

Perbaikan yang dilakukan bersifat test harness, bukan produksi:
- `_check_rate_limit` stub disuntik di namespace AST `tests/test_v1_sop_boundary.py`.
- `CHAT_SESSION_PATTERN` disuntik di namespace AST `tests/test_openrouter_provider.py`.
- Optional extras `.[workflow,langchain]` dipasang di `.venv`.

Ini membuktikan kontrak batas (auth, session, replay, provider selection, workflow wiring) dapat diuji secara offline, **bukan** membuktikan embedder/pdf worker/DB/RAG nyata bekerja.

## Yang boleh dan tidak boleh diklaim

Boleh diklaim PASS:

- Boot endpoint publik dan health check.
- Kontrak boundary V1 offline untuk 19 test di `test_v1_sop_boundary.py`.
- Provider selection OpenRouter pada 37 test AST.
- Routing/workflow language saat optional extras terpasang, kecuali satu test data-dependent.

Tidak boleh diklaim PASS:

- Ingest dokumen SOP sintetis.
- Pencarian pengetahuan dengan embedding IndoBERT.
- Chat grounded dengan sumber SOP dan LLM nyata.
- Kesiapan data produksi atau privasi.

## Syarat untuk melanjutkan

1. Sediakan artifact `nusantara-models/` yang sesuai (worker + python environment) melalui checkout/persetujuan eksplisit; jangan disintesiskan sebagai pengganti model asli.
2. Nyalakan Ollama/local model atau konfigurasikan provider yang disetujui untuk uji chat nyata.
3. Ulangi synthetic ingest → synthetic search → synthetic chat dengan sumber dokumen uji, lalu catat status, latency, dan kutipan sumber.
4. Putuskan secara eksplisit apakah session-id drift P2-3 diperbaiki atau diterima sebagai kontrak saat ini.

## Sprint 1 synthetic RAG fixture (belum di-commit saat verifikasi)

`tests/test_synthetic_rag_fixture.py` sekarang menyediakan `build_synthetic_engine(tmp_path)`, dipakai bersama oleh fixture pytest dan `tests/test_langchain_adapter.py`. Engine memakai `SQLiteVectorStore(tmp_path/'fixture.db')`, embedding deterministik `[1.0, 0.0, 0.0]`, serta dokumen `synthetic-sop-1`. Ini menghilangkan kegagalan `assert 0 >= 1` akibat store kosong tanpa memakai data PC.

Bukti yang dijalankan:

- `.venv/bin/python -m pytest tests/test_langchain_adapter.py tests/test_synthetic_rag_fixture.py -q` → `7 passed`.
- `.venv/bin/python -m pytest tests/test_synthetic_rag_fixture.py tests/test_knowledge_pipeline_api.py -q -k "synthetic or metadata_http or pdf_approval"` → PASS; 5 test.
- Broad targeted regression 68 item → `tests/test_knowledge_pipeline_api.py ............`; satu failure historis R2 di luar knowledge pipeline.

Flake `409 {"detail":"DOCUMENT_VERSION_NOT_FOUND"}` terjadi karena upload PDF memicu `prepare_uploaded_source` → `documents.prepare` → `DocumentTools.process` secara async; test lama langsung GET/POST dengan `source_version` sebelum extraction selesai. Perbaikan test menunggu `prepared['extraction_status'] in {'COMPLETE', 'PARTIAL', 'FAILED'}` sebelum GET/POST.

Ini membuktikan retrieval/evidence/answer-context dengan data buatan, **bukan** membuktikan IndoBERT worker, OCR/Docling, LLM/Ollama, atau PDF SOP nyata. Status `SOP/RAG END-TO-END: BLOCKED / NOT VERIFIED` tetap berlaku.

## Sprint 2 runtime portability (belum di-commit saat verifikasi)

Resolusi OCR kini portabel: `docling_config.tesseract_command()` memakai `NUSANTARA_TESSERACT_CMD`, lalu `shutil.which('tesseract')`, lalu path legacy Windows hanya jika benar-benar ada. Jika tidak ada Tesseract, `effective_config()` mengembalikan `tesseract_cmd=''`, `tesseract_sha256=None`, dan `language_sha256={}` alih-alih melempar `FileNotFoundError`. `KnowledgeEngine` memakai helper yang sama.

Bukti: `tests/test_runtime_portability.py` `6 passed`; `tests/test_runtime_portability.py tests/test_capil01_knowledge.py` `12 passed, 1 skipped`. Ini hanya membuktikan resolusi path dan OCR fixture, bukan OCR native nyata.

Tidak ada perbaikan untuk worker IndoBERT, model cache, atau Ollama. Status `SOP/RAG END-TO-END: BLOCKED / NOT VERIFIED` tetap berlaku.

## Kesimpulan

`SOP_KNOWLEDGE_TEST_REPORT` menyatakan alur SOP/RAG penuh **BLOCKED**. Bukti yang ada cukup untuk menyebut batas kegagalan, bukan untuk menyatakan fitur berfungsi.
