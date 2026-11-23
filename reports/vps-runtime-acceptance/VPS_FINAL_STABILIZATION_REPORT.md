# VPS Final Stabilization Report

Tanggal: 2026-11-23
Executor: OpenCode VPS Instabox
Baseline: PR #16 — Final Consolidation

## Ringkasan Gate

| Gate | Verdict | Rujukan |
|---|---|---|
| Integrasi PR #16 | PASS (read-only) | `V1_INTEGRATION_ACCEPTANCE_REPORT.md` |
| Runtime VPS | BLOCKED / NO-GO | `VPS_RUNTIME_ACCEPTANCE_REPORT.md` |
| Regresi | PASS relatif baseline, residual terdokumentasi | `REGRESSION_ROOT_CAUSE_REPORT.md` |
| Knowledge SOP | BLOCKED | `KNOWLEDGE_SOP_READINESS_REPORT.md` |
| Merge otomatis | Tidak dilakukan | PR #16 masih open, `mergeable: clean` |
| Restart/deploy | Tidak dilakukan | Proses 8000/8100/5173/5200 tidak disentuh |
| Perubahan DB/data | Tidak dilakukan | DB hanya dibaca mode `ro` |

## Temuan Penentu

1. PR #16 bersih: base `b268da1e`, head audit `58f07307`, 13 commit, 178 file, 0 konflik, cakupan #14/#15 terpenuhi.
2. Backend aktif bukan PR #16:
   - port 8000 → build `5b3750b8` = commit `ddc54a2b`
   - port 8100 → build `d5bdf8fd` = commit `e9786bb8` / `87a58034` / `5ebe32b3`
   - keduanya meng-import `app/` legacy, bukan `backend/app/` kanonik.
3. Frontend aktif degraded: PID Vite 28365/347016 memiliki CWD `control-plane (deleted)` dan melayani 404 di port 5173/5200.
4. Regresi tidak memburuk: `89 failed / 1466 passed / 62 skipped / 49 errors`, identik dengan baseline PR #16; tidak ada defect baru yang terbukti.
5. SOP nyata tidak tersedia: 0 PDF, 0 dokumen, 0 chunk, model embedding tidak ada.

## Catatan deep-dive

- Baseline `b268da1e` di tree terpisah: `119 failed / 1434 passed / 62 skipped / 49 errors`; head PR #16: `89 failed / 1466 passed / 62 skipped / 49 errors`. 30 instance perbaikan, 0 ID regresi baru.
- Satu actual code defect terbukti tetapi **pre-existing**: `official_knowledge_ingestion.py:42` meng-import `app.knowledge.sqlite_backup` yang tidak ada di base maupun head. Tidak diperbaiki tanpa approval.
- Validator SOP tidak bisa dijalankan karena defect tersebut; PDF, manifest, `.venv-docling`, `nusantara-models/docling`, dan `production_knowledge.db` semuanya tidak ada. Satu file `.txt` sintetis tidak digunakan sebagai bukti.

## Keputusan

**FINAL STABILIZATION: NO-GO.**

Tidak boleh dinyatakan bahwa Nusantara V1 stabil di VPS pada commit PR #16. Yang sudah terbukti hanyalah integrasi Git dan regresi relatif baseline. Runtime yang diuji masih memakai kode legacy dan frontend sudah terdampak cleanup.

## Prasyarat untuk Approval Berikutnya

1. Approve merge PR #16, lalu checkout SHA yang sama di PC dan VPS.
2. Approve restart/rebind backend ke `backend/app` dengan commit PR #16 (mis. `PYTHONPATH=backend uvicorn app.main:app`) — proses lama tidak dihentikan tanpa izin.
3. Approve penyajian frontend dari `frontend/` kanonik ke port 5173/5200; jangan gunakan `control-plane/` yang sudah dihapus.
4. Sediakan PDF SOP asli, model embedding `indobenchmark/indobert-base-p1`, kredensial operator/admin, dan konfirmasi apakah data knowledge boleh diindeks ulang.

Laporan lama yang masih valid dan tidak diduplikasi di sini:
`reports/final-consolidation/VERIFICATION_SUMMARY.md`, `reports/vps-recovery/*.md`, `reports/stabilization/*.md`, dan `docs/reports/**`.
