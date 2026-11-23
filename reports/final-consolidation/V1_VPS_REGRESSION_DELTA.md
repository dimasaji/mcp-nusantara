# V1 VPS Regression Delta

Tanggal: 2026-11-23
Head PR #16: `2278719c30d16dffb767826aa6f3a765d7fda60d`
Baseline: `b268da1e0911e43ad9e7ea5b166ba473d81f072e`
Environment: `/data/workspace/nus-v1-integration-20261123/env/bin/python`
Invocation: `PYTHONPATH=backend python -m pytest -q -p no:cacheprovider --continue-on-collection-errors`

## Ringkasan angka

| Run | Failed | Passed | Skipped | Errors | Warnings | Log |
|---|---:|---:|---:|---:|---:|---|
| Baseline `b268da1e` | 119 | 1434 | 62 | 49 | 1053 | `/tmp/nus-base-b268-full.log` |
| RC candidate final | 89 | 1466 | 62 | 46 | 1076 | `/data/workspace/nus-v1-integration-20261123/logs/regression-full-candidate-final.log` |
| PR #16 HEAD | 86 | 1478 | 62 | 48 | 1076 | `/tmp/vps-fix-full-final.log` |

Delta HEAD vs baseline: `-33 failed`, `+44 passed`, `0 skipped`, `-1 error`.
Delta HEAD vs RC: `-3 failed`, `+12 passed`, `0 skipped`, `+2 error`.

## Analisis ID

Perbandingan memakai pasangan `(status, test id)` dari baris `FAILED`/`ERROR`.

| Perbandingan | ID baru | ID hilang | Catatan |
|---|---:|---:|---|
| HEAD vs baseline `b268da1e` | 0 | 28 | Tidak ada regresi baru terhadap baseline restrukturisasi |
| HEAD vs RC candidate | 2 | 3 | 2 error koleksi known-environment; 3 perbaikan dari `sqlite_backup` |

Dua ID yang muncul terhadap RC tetapi bukan terhadap baseline:

- `ERROR tests/evaluation/test_live_harness.py` — `Configured operator credential unavailable`.
- `ERROR tests/test_developer_control.py` — file `developer.py` tidak ada.

Keduanya sudah tercatat sebagai keterbatasan environment VPS, bukan perubahan kode PR #16. Error koleksi `tests/test_v1_operational_data.py` akibat `app.knowledge.sqlite_backup` hilang sudah hilang setelah perbaikan di HEAD.

## Targeted suite

Command:

```sh
PYTHONPATH=backend /data/workspace/nus-v1-integration-20261123/env/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_cost_ledger_v1.py \
  tests/test_openrouter_cost_policy_v1.py \
  tests/test_cost_ledger_initialization_race.py \
  tests/test_knowledge_preparation.py \
  tests/test_knowledge_cleaning.py \
  tests/test_effective_rag_profile.py \
  tests/test_hermes_v1_contextual_followup.py \
  tests/test_v1_knowledge_reuse_rebind.py \
  tests/test_runtime_portability.py \
  tests/test_v1_chat_rag_regression.py \
  tests/test_ncp_v1_chat_contract.py
```

Hasil: `133 passed, 119 warnings in 1.77s`, exit `0`.
Log: `/tmp/v1-pr16-targeted-final.log`.

## Domain defect yang diperbaiki

- Sebelum perbaikan: `backend/app/knowledge/official_knowledge_ingestion.py:42` meng-import `app.knowledge.sqlite_backup.backup_sqlite_database`, tetapi modul tidak ada.
- RED final: 5 test gagal dengan `ModuleNotFoundError` saat modul dihapus di tree sementara.
- GREEN: modul dipulihkan dari `3a361c03:app/knowledge/sqlite_backup.py`; 12 test sqlite targeted lulus.
- Quality gates: `ruff check` lulus, `ruff format --check` modul baru lulus, `mypy` modul baru lulus.
- `graphify update .` tidak dapat dijalankan karena `graphify: command not found`; dicatat sebagai keterbatasan tool.

## Kesimpulan delta

Tidak ada regresi baru terhadap baseline. Perbaikan `sqlite_backup` menambah 12 test lulus dan menghilangkan error koleksi terkait. Residual failure/error bukan bagian dari perubahan PR #16 dan tetap harus dijadikan catatan operasional, bukan klaim PASS produksi.
