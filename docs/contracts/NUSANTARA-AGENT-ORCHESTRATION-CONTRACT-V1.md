# NUSANTARA V1 — Agent Orchestration Boundary

Tanggal: 2026-10-06. Status: DOCUMENTED_IMPLEMENTATION_WITH_OPEN_GATES.

Scope: V1; subordinate pada Architecture Contract, Verification Work Contract dan GATES existing. Dokumen ini menutup kekurangan dokumen, bukan bukti acceptance runtime.

## Boundary dan lifecycle
Kontrak ini mendefinisikan boundary; tidak mengimplementasikan Agent/LangGraph/Graphify runtime. Hermes V1 tetap orchestration foundation. Lifecycle konseptual adalah request tervalidasi -> tahap engine existing -> evidence/trust/grounding -> respons atau kegagalan aman. Kehadiran modul tidak berarti seluruh kemampuan terhubung ke `/v1/chat`.

## Permission dan tool access
Model hanya mengusulkan tindakan; tool terdaftar harus melalui GovernedToolRegistry dengan permission, schema, policy dan approval. Tidak ada arbitrary shell default. Stdio MCP existing hanya expose dua tool baca. Integrasi tool otomatis ke chat V1 belum dibuktikan dan tidak diaktifkan oleh kontrak ini.

## Trust, policy, approval dan audit
Trust menilai dukungan evidence; confidence bukan fakta resmi atau izin eksekusi. Policy terpisah dari execution. Approval harus terikat payload, reviewer berbeda, expiry dan konsumsi sekali. Audit memakai komponen existing dan harus bisa diverifikasi. Production knowledge/source/policy/release tidak dapat berubah otomatis.

## Timeout dan budget
Gunakan batas tahap existing (route 30 detik, dua slot; tool timeout dari ToolSpec default 10 detik), serta batas provider/worker existing. Ini bukan jaminan penghentian side effect saat thread timeout. Settings memuat context tokens 4096 dan context window 10; belum ada bukti global agent budget/token/cost enforcement pada V1. Budget baru wajib proposal dan gate terpisah; tidak dibuat dalam closure.

## Rollback dan penerimaan
Perubahan orchestrator membutuhkan scope, backup, candidate terisolasi, evidence, approval sesuai risiko dan regression. Stop/restart/rollback produksi tetap OPEN sampai diuji pada target yang ditentukan. Keberadaan kontrak tidak memberi izin agent runtime atau menyatakan integrasi PASS.

## Evidence dan change control

Source yang disebut adalah implementation reference. Bukti historis: `reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md`; hasil closure: `reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md`. Kontrak baru tidak mengubah source, test, konfigurasi atau database. Risiko: interpretasi dokumen melebihi evidence; karena itu gaps tetap eksplisit. Rollback dokumen: hapus hanya file baru ini setelah review, pertahankan kontrak sebelumnya.
