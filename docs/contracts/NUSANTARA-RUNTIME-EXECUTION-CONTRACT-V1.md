# NUSANTARA V1 — Runtime Execution

Tanggal: 2026-10-06. Status: DOCUMENTED_IMPLEMENTATION_WITH_OPEN_GATES.

Scope: V1; subordinate pada Architecture Contract, Verification Work Contract dan GATES existing. Dokumen ini menutup kekurangan dokumen, bukan bukti acceptance runtime.

## Implementasi V1
`app/main.py` menjalankan FastAPI dan mempertahankan router `/v1`. `app/api/routes.py` menyusun tahap Language, Problem, Knowledge, reasoning/provider dan grounding menggunakan Hermes yang sudah ada. `/health` dan `/v1/health` memuat `BUILD_ID` dari `app/core/runtime_identity.py`, ditangkap saat import. Fingerprint meliputi source/assets app, pyproject dan worker; tidak mencakup environment, database, bobot model, atau dependency terpasang.

Konfigurasi umum berasal dari `app/core/config.py::settings`; komponen membaca override environment yang sudah ada. Tidak dibuat configuration truth kedua. `_run_sync_v1` membatasi dua pekerjaan sinkron dan timeout tahap default 30 detik: penuh menghasilkan 503, timeout 504. Timeout HTTP tidak menghentikan thread; slot tetap digunakan sampai pekerjaan selesai. Worker mempunyai batas waktu sendiri.

## Kriteria dan batas bukti
Health hanya membuktikan respons proses. Release harus mencocokkan identity proses dengan candidate dan memverifikasi model, knowledge, chat, workload, restart dan rollback pada target sebenarnya. Candidate lokal recovery lulus pemeriksaan endpoint; container/produksi belum terverifikasi. Perubahan metadata oracle mengubah fingerprint sehingga bukti proses recovery sebelumnya tidak membuktikan build terbaru.

## Rollback
Pulihkan hanya file yang diubah dari backup terikat perubahan; jangan reset working tree. Jalankan candidate terisolasi sebelum mengganti proses produksi. Tidak ada deployment/restart produksi dalam closure ini.

## Evidence dan change control

Source yang disebut adalah implementation reference. Bukti historis: `reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md`; hasil closure: `reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md`. Kontrak baru tidak mengubah source, test, konfigurasi atau database. Risiko: interpretasi dokumen melebihi evidence; karena itu gaps tetap eksplisit. Rollback dokumen: hapus hanya file baru ini setelah review, pertahankan kontrak sebelumnya.
