# Regression Root Cause Report

Tanggal: 2026-11-23
Baseline: PR #16 — Final Consolidation
Environment: `/data/workspace/nus-v1-integration-20261123/env/bin/python`, `PYTHONPATH=backend`

## Hasil Eksekusi

| Pemeriksaan | Perintah | Hasil |
|---|---|---|
| Targeted RC | `pytest -q -p no:cacheprovider <11 file>` | `133 passed, 119 warnings in 2.23s` |
| Penuh | `pytest -q -p no:cacheprovider --continue-on-collection-errors` | exit `1`; `89 failed, 1466 passed, 62 skipped, 49 errors` (46 runtime + 3 collection), 28.73s |

Log lengkap: `/tmp/vps-acceptance-full.log`.

## Perbandingan dengan Baseline PR #16

| Metrik | PR #16 / RC | Eksekusi ulang VPS | Delta |
|---|---:|---:|---:|
| Failed | 89 | 89 | 0 |
| Passed | 1466 | 1466 | 0 |
| Skipped | 62 | 62 | 0 |
| Runtime errors | 46 | 46 | 0 |
| Collection errors | 3 (tercatat) | 3 | 0 |
| Total errors | 49 | 49 | 0 |

Seluruh ID `FAILED` dan 46 ID runtime `ERROR` identik dengan baseline. Tiga error koleksi sudah tercatat di `reports/final-consolidation/VERIFICATION_SUMMARY.md` baris 24–26; ketiadaannya di log RC lama disebabkan perbedaan ketersediaan fixture workspace, bukan perubahan kode PR #16.

## Kelompok Penyebab

| Kategori | Temuan | Contoh |
|---|---|---|
| Pre-existing | 89 failures + 46 runtime errors sudah ada di baseline/RC | `test_control_plane_attestation_binding.py`, review execution API tests |
| Environment dependency | Kredensial dan guard lingkungan | `Configured operator credential unavailable`; `EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED ... reason=active_database_or_sidecar`; tidak ada `OPENROUTER_API_KEY` |
| Missing fixture | File historis/PC-owned atau hasil cleanup yang disetujui | `developer.py`, `app.knowledge.sqlite_backup`, `control-plane/evidence-requirements.json`, `reports/CONFIGURATION_BASELINE_20261006.json`, `.dev/checkpoints/r2-20261007/...`, `docs/reports/r2-.../...`, `data/knowledge/official_sources/ktp_el/manifest.json` |
| Actual code defect | Tidak terbukti pada cakupan PR #16 | Tidak ada perbaikan kode yang diajukan |
| New regression | Tidak ada regresi kode baru | 3 error koleksi adalah drift environment/fixture yang sudah terdokumentasi |

## Tindakan

- Tidak ada threshold yang diubah.
- Tidak ada test yang dinonaktifkan atau di-skip paksa.
- Tidak ada perbaikan kode yang diterapkan; perbaikan hanya boleh dilakukan jika defect terbukti dan disetujui.

## Deep-dive tambahan — baseline terpisah

Tree `b268da1e` di-archive ke `/tmp/nus-base-b268-audit` dan dijalankan dengan environment/perintah identik.

| Metrik | Base `b268da1e` | Head PR #16 `58f07307` | Delta |
|---|---:|---:|---:|
| Failed | 119 | 89 | -30 |
| Passed | 1434 | 1466 | +32 |
| Skipped | 62 | 62 | 0 |
| Errors | 49 | 49 | 0 |

Tidak ada ID kegagalan baru di head; 3 error koleksi muncul di kedua tree. Ini mengonfirmasi perbaikan PR #16 dan menyingkirkan regresi kode baru.

## Akar dominan dengan bukti log

| Pola | Bukti | Kategori |
|---|---|---|
| `WINDOWS_REQUIRED` (68 kemunculan) | `backend/app/security/local_operator.py:118`, lewat fixture `tests/test_runtime_authorization.py:60` | Environment dependency (fixture Windows di Linux) |
| `ISOLATED_CANDIDATE_TEST_FAILED` / `EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED` | guard `tests/run_evidence_tests_isolated.py:94` memblokir `_pytest/main.py` sebagai `active_database_or_sidecar` | Environment dependency (isolated runner terlalu agresif) |
| `Configured operator credential unavailable` | `scripts/run_eval.py:11` | Environment dependency |
| `FileNotFoundError` (20 kemunculan) | `developer.py`, `reports/CONFIGURATION_BASELINE_20261006.json`, `control-plane/evidence-*.json`, `.dev/checkpoints/...`, `docs/reports/...`, `data/knowledge/official_sources/ktp_el/manifest.json` | Missing fixture; semuanya juga absen di base `b268da1e` |
| `ModuleNotFoundError: app.knowledge.sqlite_backup` (4) | import di `backend/app/knowledge/official_knowledge_ingestion.py:42`; modul tidak ada di base maupun head | **Actual code defect, pre-existing** |
| `assert 404 == 403` / `404 == 200` (4) | endpoint `/v2/dev/*` sudah tidak ada | API surface drift, pre-existing |
| `assert 'NOT_VERIFIED' == 'CLOSED_PASS'` | bukti R2 tidak tersedia | Missing evidence |

Catatan penting: satu **actual code defect** memang terbukti (`sqlite_backup` import), tetapi sudah ada di `b268da1e` dan tidak diperkenalkan PR #16. Tidak ada perbaikan yang diterapkan tanpa approval.

## Final staging update — 2026-11-23

Fase ini menjalankan ulang regression dari RC immutable `6f037ab491d0ae2793db69d380b0d3e82ec88872` di worktree staging terpisah:

- Worktree: `/data/workspace/nus-v1-staging-6f037ab4/repo`
- Python: `/data/workspace/nus-v1-staging-6f037ab4/env/bin/python`
- Targeted log: `/data/workspace/nus-v1-staging-6f037ab4/runtime/regression-targeted.log`
- Full log: `/data/workspace/nus-v1-staging-6f037ab4/runtime/regression-full.log`

| Pemeriksaan | Hasil |
|---|---|
| Targeted 12 file | `138 passed, 119 warnings in 1.87s`, exit `0` |
| Full suite | `86 failed, 1478 passed, 62 skipped, 48 errors in 26.51s`, exit `1` |

Perbandingan ID kegagalan:

| Perbandingan | ID baru | ID fixed | Interpretasi |
|---|---:|---:|---|
| Base `b268da1e` → RC | 0 | 28 | Tidak ada regresi kode baru; perbaikan RC menurunkan jumlah kegagalan |
| RC sebelum fix sqlite → RC final | 2 | 3 | 3 error sqlite hilang; 2 error koleksi environment/fixture muncul |
| Setelah fix sqlite → RC final | 0 | 0 | Stabil untuk kode yang sama |

Dua ID baru terhadap RC sebelum fix bukan regresi kode:

- `tests/evaluation/test_live_harness.py` — `Configured operator credential unavailable`.
- `tests/test_developer_control.py` — `developer.py` tidak ada di worktree bersih.

Kelompok residual pada RC final:

| File | Jumlah ID | Kategori dominan |
|---|---:|---|
| `tests/test_runtime_authorization.py` | 38 | Windows-native actor proof (`WINDOWS_REQUIRED`) di Linux |
| `tests/test_control_plane_attestation_binding.py` | 31 | Windows/attestation guard dan fixture OS-specific |
| `tests/test_v1_review_execution_api.py` | 16 | evidence/runtime fixture tidak lengkap |
| `tests/test_audit_regressions.py` | 4 | V2/dev API surface expectations |
| `tests/test_evidence_finalization.py` | 4 | file evidence historis tidak ada |
| `tests/test_evidence_registry.py` | 4 | registry evidence tidak lengkap |
| `tests/test_provider_identity.py` | 4 | public route/identity expectations |
| `tests/test_web_evidence_pipeline.py` | 4 | official manifest tidak ada |
| `tests/test_langchain_e2e.py`, `hardening.py`, `adapter.py`, `langgraph_workflow.py` | 10 | optional LangChain/Indobert dependency tidak tersedia |
| `tests/test_phase3_metrics_integration.py` | 3 | metrics wiring expectation |
| `tests/test_runtime_verification.py` | 3 | protected historical source/checkpoint tidak ada |
| Lainnya | 8 | kredensial, `developer.py`, SOP source pages, synthetic RAG, session memory |

Tidak ada test yang di-skip paksa atau diubah untuk menurunkan angka kegagalan. Tidak ada perbaikan kode baru dalam fase staging ini. Defect `sqlite_backup` yang sebelumnya tercatat sebagai actual code defect sudah diperbaiki di `2278719c` dan terverifikasi oleh 5 test `tests/test_sqlite_backup_wal.py`.

## Verdict

**REGRESSION: PARTIAL.** Relatif terhadap baseline `b268da1e`, RC `6f037ab4` memperbaiki 28 ID dan tidak memperkenalkan ID kegagalan kode baru. Namun full suite masih menghasilkan 86 failures dan 48 errors, sehingga ini bukan PASS produksi. Residual terklasifikasi sebagai environment/fixture dan pre-existing; SOP real E2E tetap BLOCKED menurut `KNOWLEDGE_SOP_READINESS_REPORT.md`.
