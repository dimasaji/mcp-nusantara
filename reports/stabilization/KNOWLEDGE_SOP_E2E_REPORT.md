# Knowledge SOP E2E Report — Stabilization V1

- Tanggal verifikasi: 2026-11-23.
- Commit sumber terverifikasi: `4bdd387bd6b1101ca30a2fc047a93ffd0361efb8`.
- Status akhir: **BLOCKED** untuk E2E; **PASS** hanya untuk component test sintetis.

## Perintah yang dijalankan

- Pencarian PDF: `find /data/home/mcp-nusantara /data/workspace /data/home -iname '*.pdf'` (hasil kosong).
- Inspeksi fixture: `tests/fixtures/piak03-extracted.txt`, `docs/evidence/U02_U04_CHAT_VERIFICATION_20261026.md`.
- DB langsung: `sqlite3 data/knowledge/nusantara_knowledge.db "select count(*) from documents; select count(*) from chunks;"`.
- Endpoint: `curl http://127.0.0.1:8100/v1/knowledge/pipeline/status`, `curl http://127.0.0.1:8100/v1/runtime/readiness`.
- Component test: `.venv/bin/pytest -q tests/test_knowledge_pipeline.py::test_piak03_extracted_sop_is_only_a_generic_pipeline_fixture tests/test_sop_ingestion.py tests/test_golden_sop_chat.py`.
- Worker check: keberadaan `/data/home/mcp-nusantara/nusantara-models/.venv/bin/python` dan `/data/home/mcp-nusantara/nusantara-models/indobert_worker.py`.

## Hasil aktual

- Tidak ditemukan file `*.pdf` di tiga lokasi yang diperiksa.
- PDF asli PIAK-03 tidak tersedia; yang ada hanya turunan teks `tests/fixtures/piak03-extracted.txt` dan bukti historis `docs/evidence/U02_U04_CHAT_VERIFICATION_20261026.md`.
- Fixture `piak03-extracted.txt` secara eksplisit diperlakukan sebagai generic pipeline fixture, bukan bukti dokumen asli.
- Worker IndoBERT tidak tersedia di path yang diharapkan.
- DB: `documents=0`, `chunks=0`.
- Endpoint knowledge/status dan readiness: HTTP `403 {"detail":"admin token diperlukan"}`.
- Component test sintetis: `5 passed`, exit `0`.
- Tidak ada jawaban chat yang dapat dibuktikan berasal dari SOP PIAK-03 dengan sitasi halaman asli.

## Status bukti

- **PASS** — Pipeline komponen dapat diuji dengan fixture sintetis; rollback, idempotensi, dan golden chat dasar lolos.
- **BLOCKED** — E2E dengan PDF asli, ingestion nyata, jawaban berbasis SOP, dan sitasi halaman tidak dapat dijalankan.
- **BLOCKED** — Status/readiness endpoint tidak terverifikasi karena admin token tidak tersedia.

## Root cause

- Artefak sumber (PDF PIAK-03) tidak hadir di VPS.
- Worker embedding/IndoBERT tidak terpasang pada path yang diharapkan.
- Knowledge DB kosong, sehingga tidak ada chunk yang dapat di-retrieve.
- Endpoint administratif memerlukan token yang tidak diberikan dalam sesi ini.

## Corrective action

- Gunakan fixture sintetis hanya untuk component test dan nyatakan demikian.
- Jangan menghasilkan PDF tiruan untuk mensimulasikan PIAK-03.
- Jangan menulis jawaban atau sitasi ke laporan ini kecuali berasal dari dokumen asli yang tersedia.
- Simpan status `BLOCKED` sampai input nyata tersedia.

## Pekerjaan tersisa

- Sediakan PDF PIAK-03 asli dari pemilik dokumen, dengan kontrol akses dan bukan artefak publik.
- Sediakan admin token untuk endpoint pipeline/readiness.
- Pasang/verifikasi worker IndoBERT dan jalankan ulang ingestion pada DB bersih.
- Ulangi E2E dan rekam jawaban plus halaman sitasi sebelum status diubah menjadi PASS.

## Bukti

- `/data/tmp/opencode/ollama_knowledge_boundary.txt`
- `/data/tmp/opencode/stab_phase_d_component_tests.txt`
- `/data/tmp/opencode/stab_phase_b_database.txt`
