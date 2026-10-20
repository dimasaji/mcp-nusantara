# NUSANTARA V1 — Intelligence Model

Tanggal: 2026-10-06. Status: DOCUMENTED_IMPLEMENTATION_WITH_OPEN_GATES.

Scope: V1; subordinate pada Architecture Contract, Verification Work Contract dan GATES existing. Dokumen ini menutup kekurangan dokumen, bukan bukti acceptance runtime.

## Implementasi V1
`app/language/engine.py` memakai semantic intent engine dan IndoBERT client yang sudah tersedia. RAG menggunakan `app/knowledge/indobert_embedding.py`; worker `nusantara-models/indobert_worker.py` memuat `indobenchmark/indobert-base-p1`, embedding 768 dimensi. Route berbagi client semantic intent dengan embedding adapter jika semantic engine tersedia; request pipe client diserialisasi. Ini tidak mengubah bobot atau model.

`app/hermes/agent.py` mempertahankan LanguageEngine, ProblemEngine dan ReasoningEngine. Route membuat `OllamaProvider` dari settings/model request. Provider default mandiri Hermes adalah MockProvider; keberhasilan mock/unit test tidak membuktikan model produksi. Tidak mengganti Hermes/model router atau membuat orchestrator kedua.

## Kriteria dan batas bukti
Error provider/model harus dilaporkan dengan aman, tanpa fallback fakta yang diklaim benar. Verifikasi memerlukan model tersedia, output finite, dimensi sesuai, timeout dan kegagalan provider; kualitas jawaban memerlukan oracle approved. Hasil recovery targeted berhasil setelah worker dibagi; hal ini bukan bukti akurasi resmi atau kapasitas produksi. Tidak mengubah konfigurasi atau memasang dependency pada closure.

## Rollback
Perubahan client recovery mempunyai backup `reports/v1-recovery-backup-20261006/app/api/routes.py`; rollback selektif memerlukan pemeriksaan perubahan pengguna dan regression, bukan penggantian otomatis seluruh file.

## Evidence dan change control

Source yang disebut adalah implementation reference. Bukti historis: `reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md`; hasil closure: `reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md`. Kontrak baru tidak mengubah source, test, konfigurasi atau database. Risiko: interpretasi dokumen melebihi evidence; karena itu gaps tetap eksplisit. Rollback dokumen: hapus hanya file baru ini setelah review, pertahankan kontrak sebelumnya.
