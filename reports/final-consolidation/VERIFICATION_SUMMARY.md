# Verifikasi branch final konsolidasi

Branch: `codex/final-consolidation-20261123`
HEAD saat verifikasi: `8f51d50e` (setelah normalisasi manifest)
HEAD setelah cleanup: `d6fce599`
Python: `/data/workspace/nus-v1-integration-20261123/env/bin/python` (sama dengan bukti RC)

## Perintah dan hasil

| Pemeriksaan | Perintah | Hasil |
|---|---|---|
| Diff whitespace | `git diff --check HEAD~4..HEAD` | `DIFF_CHECK=OK` |
| Compile | `python -m compileall -q backend tests` | exit `0` |
| Targeted | `PYTHONPATH=backend python -m pytest -q <11 file targeted RC>` | `133 passed, 119 warnings` |
| Ruff scoped | `ruff check backend tests --output-format concise` | `2052 findings`; baseline `b268da1e` dengan biner sama `2098 findings` (46 lebih sedikit) |
| Regression penuh | `PYTHONPATH=backend python -m pytest -q --continue-on-collection-errors` | `89 failed, 1466 passed, 62 skipped, 49 errors` = 46 runtime errors + 3 collection errors |

## Perbandingan regresi

Bukti RC (`logs/regression-full-candidate-final.log`): `89 failed, 1466 passed, 62 skipped, 46 errors`.
Branch final menghasilkan angka sama setelah 3 error koleksi yang memang sudah dikenal
dikeluarkan dari perhitungan runtime:

- `tests/evaluation/test_live_harness.py` — kredensial operator tidak tersedia
- `tests/test_developer_control.py` — `developer.py` tidak ada
- `tests/test_v1_operational_data.py` — `app.knowledge.sqlite_backup` tidak ada

Perbandingan ID `FAILED`/`ERROR`: seluruh ID RC hadir di branch final; tidak ada ID kegagalan baru.
Tiga ID tambahan di branch final hanyalah error koleksi di atas.

## Status

Verifikasi **PASS** relatif terhadap baseline: 30 perbaikan dipertahankan, 0 regresi baru.
Cleanup sudah dijalankan dan ditandai `DELETED` di `FINAL_CONSOLIDATION_MANIFEST.csv`.
Push selesai dan PR final #16 sudah dibuat:
`https://github.com/dimasaji/mcp-nusantara/pull/16` (open, head `d882d1df`, base `codex/restructure-20261123`).
PC masih perlu checkout SHA yang sama setelah PR di-merge.
