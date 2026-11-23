# Regression Remediation Report — Nusantara V1

Tanggal: 2026-11-23
Commit: `db32ee408e6972b8fc1a59b492cdeb57c46a90c6`
Baseline: `ec76a9ed01f160a28d1cbe34e263b3bbe9ccb075`
PR: `#17` — https://github.com/dimasaji/mcp-nusantara/pull/17
Scope: regresi yang diperkenalkan oleh perbaikan review gate pasca-merge.

## Ringkasan

| Item | Hasil |
|---|---|
| Regresi baru ditemukan | 1 |
| Regresi baru diperbaiki | 1 |
| Regresi baru tersisa | 0 |
| Failing/error ID vs baseline merge | 134 identik |
| ID fixed vs baseline merge | 1 |
| Full regression gate | **BLOCKED** oleh residual baseline |

## Gejala dan penyebab

Setelah commit `5e9a3e51`, `SOPReview.is_pilot` menganggap semua dokumen dengan `source_filename` atau `pipeline_status` sebagai dokumen yang wajib melalui review. Aturan ini benar untuk pipeline upload, tetapi juga mengenai dokumen yang masuk melalui endpoint admin `/v1/documents/ingest`.

Dampaknya: `tests/test_backend_runtime_fixture.py::test_backend_process_ingestion_retrieval_chat_and_history` gagal karena admin ingest menjadi tidak dapat di retrieval/grounded sampai review manual selesai.

## Perbaikan

| File | Perubahan |
|---|---|
| `backend/app/api/routes.py` | Admin ingest memaksa `ingest_channel='admin_api'` setelah menggabungkan metadata caller |
| `backend/app/knowledge/sop_review.py` | Pipeline review gate dilewati hanya jika `ingest_channel == 'admin_api'` |
| `tests/test_approval_boundary.py` | Test admin ingest exempt dari pipeline gate |
| `tests/test_audit_regressions.py` | Update assertion metadata admin ingest dan test anti-spoof caller metadata |

Keputusan desain: marker ditetapkan di route setelah `request.metadata` digabungkan, sehingga caller tidak dapat menimpa nilai `admin_api`. Pipeline upload tetap ter-gate karena tidak memiliki marker dan tetap memiliki `source_filename`/`pipeline_status`.

Validasi upper gate lain tetap berlaku: authority/status/title heuristics di `is_pilot` masih aktif untuk dokumen dengan indikasi SOP.

## Test hasil

### Reproduksi awal

`86 failed, 1478 passed, 62 skipped, 48 errors` pada `dfa1c8f0`.
Regresi baru: `FAILED tests/test_backend_runtime_fixture.py::test_backend_process_ingestion_retrieval_chat_and_history`.

### Setelah perbaikan

`85 failed, 1481 passed, 62 skipped, 1076 warnings, 48 errors in 23.23s` pada `db32ee40`.

| Perbandingan | ID baru | ID fixed |
|---|---:|---:|
| `ec76a9ed` → `db32ee40` | 0 | 1 |
| `dfa1c8f0` → `db32ee40` | 0 | 0 |
| Run kerja → run independen | 0 | 0 |

ID fixed: `FAILED tests/test_review_publication_v1.py::test_pending_candidates_cannot_displace_approved_knowledge_at_topk`.

Log:
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/verify-final/21-regression-full-final.log`
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/independent/80-full-regression.log`

## Targeted P0/P1

Hasil: `5 failed, 238 passed, 459 warnings in 8.76s`.

Failure residual:

1. `test_privileged_api_denies_before_access[False-None-/v2/dev-payload0]`
2. `test_privileged_api_denies_before_access[True-None-/v2/dev-payload0]`
3. `test_privileged_api_denies_before_access[True-invalid-/v2/dev-payload0]`
4. `test_authorized_developer_lists_workspace`
5. `test_synthetic_retriever_exposes_evidence_to_langchain` — PASS bila dijalankan dengan env-langchain

Log: `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/independent/81-targeted-p0p1.log`.

## Residual gate

134 failing/error ID tetap ada dan sudah ada pada baseline merge. Kategori dominan tetap: Windows-native actor/attestation, fixture arsip historis yang dihapus, optional dependency/LangChain, dan API expectation drift.

Perbaikan ini tidak menghapus, menonaktifkan, atau melemahkan test residual. Full regression tetap **BLOCKED** sampai owner PC menyediakan fixture/artifact dan menetapkan marker lintas-platform yang disetujui.

## Kesimpulan

Regresi admin ingest berhasil diremediasi dan tidak ada regresi baru. Status remediasi: **PASS**. Status full regression: **BLOCKED** oleh utang baseline yang sudah dikenal.
