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

## Verdict

**REGRESSION: PASS relatif terhadap baseline, dengan residual yang sudah dikenal.** Ini bukan PASS produksi; lihat `VPS_RUNTIME_ACCEPTANCE_REPORT.md` untuk blocker runtime.
