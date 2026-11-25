# V1 Next Action Plan — Stabilization V1

- Tanggal: 2026-11-23.
- Commit sumber terverifikasi: `4bdd387bd6b1101ca30a2fc047a93ffd0361efb8`.
- Branch: `codex/vps-stabilization-20261123`.
- Verdict keseluruhan: **PARTIAL / BLOCKED**, bukan production-ready.

## Verdict A–F

- **A — Runtime environment: PASS.** Backend, frontend build, Ollama, Python import, dan pip check berhasil pada VPS Linux.
- **B — Structural mapping: PARTIAL.** Layout `backend/frontend/deploy/docker` tidak ada; struktur aktif dipetakan ke `app/` dan `control-plane/`.
- **C — Ollama runtime: PASS.** Ollama `0.40.17`, model `llama3.2:1b`, inferensi langsung dan lewat backend menghasilkan HTTP `200`.
- **D — Knowledge SOP E2E: BLOCKED.** PDF PIAK-03, worker, admin token, dan data DB tidak tersedia; hanya component test sintetis yang PASS.
- **E — Regression triage: PARTIAL.** Tidak ada regresi baru setelah perbaikan cost-ledger, tetapi suite tetap merah oleh 69 failure + 30 error baseline/environment/design.
- **F — Deliverables: PASS.** Bundle laporan di-commit sebagai `8c464050d82f901f0b4c5f04d89dc69b98b22d7c`, di-push, dan PR #15 dibuat tanpa merge ke PR #14: https://github.com/dimasaji/mcp-nusantara/pull/15.

## Root cause dan corrective action — ringkasan

- **Cost-ledger race:** `SELECT` then `INSERT` pada `cost_policy.singleton` menyebabkan `UNIQUE constraint failed` saat dua inisialisasi konkuren.
  - Corrective action: `INSERT OR IGNORE` diikuti `SELECT` dan `POLICY_MISMATCH` check; terverifikasi harness deterministik, targeted `7 passed`, dan full suite kembali ke baseline.
- **Knowledge E2E tidak dapat dijalankan:** PDF asli, worker, token, dan chunk DB tidak ada.
  - Corrective action: gunakan fixture sintetis untuk component test saja dan pertahankan status `BLOCKED`.
- **Attestation/authorization gagal:** VPS Linux tidak memenuhi `WINDOWS_REQUIRED`; checkpoint bukti tidak lengkap.
  - Corrective action: jalankan ulang di runner Windows dengan artefak lengkap; jangan soft-kan assertion.
- **Endpoint V1-only diuji sebagai V2:** metrics, memory, dan route komposisi V2 diharapkan oleh beberapa test lama.
  - Corrective action: keputusan cakupan resmi diperlukan; jangan tambahkan V2/V3 atau microservice dalam kontrak ini.
- **Struktur generik tidak cocok:** kontrak menyebut folder yang tidak ada.
  - Corrective action: dokumentasikan pemetaan struktur aktif; jangan bulk move folder.

## Prioritas tindakan berikutnya

1. **P0 — Sediakan input Knowledge nyata:** PDF PIAK-03 asli, admin token, worker IndoBERT, lalu ulang ingestion dan E2E dengan sitasi halaman.
2. **P0 — Jalankan attestation di lingkungan yang sesuai:** runner Windows dengan `PROFILE_BEFORE.json`, checkpoint `source-before`, dan manifest bukti lengkap.
3. **P1 — Putuskan cakupan test lama:** apakah endpoint V2/metrics/memory akan tetap out-of-scope untuk V1 atau perlu perubahan kontrak resmi.
4. **P1 — Pulihkan artefak baseline:** `.dev/checkpoints/...`, manifest web evidence, dan source before health-gate bila test baseline ingin dijalankan ulang.
5. **P2 — Perbaiki debt lint/mypy cost-ledger secara terpisah:** 3 ruff issue dan 9 mypy issue sudah ada sebelum perbaikan race dan tidak boleh mengaburkan review perbaikan ini.
6. **P2 — Pastikan PR stabilization ditinjau dan tidak di-merge otomatis ke PR #14.**

## Batasan yang harus dipertahankan

- Jangan klaim PASS untuk Knowledge SOP E2E tanpa PDF asli, ingestion nyata, jawaban SOP, dan sitasi.
- Jangan unggah PDF, DB, credential, kunci, atau data pribadi ke GitHub.
- Jangan force push, hard reset, merge, atau menghapus perubahan lokal pengguna.
- Jangan menurunkan threshold test, menghapus test, atau menambah fitur V2/V3/microservice.
- Jangan menyatakan production-ready sebelum E2E Knowledge dan regression environment selesai.

## Status akhir

- Perbaikan sumber dan laporan dikirim pada branch `codex/vps-stabilization-20261123`.
- PR #14 tetap OPEN dan tidak di-merge.
- Verifikasi selesai dengan status **PARTIAL / BLOCKED** sesuai bukti di atas.

## Bukti

- `reports/stabilization/VPS_RUNTIME_VERIFICATION.md`
- `reports/stabilization/GITHUB_SYNC_REPORT.md`
- `reports/stabilization/KNOWLEDGE_SOP_E2E_REPORT.md`
- `reports/stabilization/REGRESSION_TRIAGE_REPORT.md`
- `/data/tmp/opencode/stab_full_pytest_after_fix.txt`
