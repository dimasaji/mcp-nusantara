# NUSANTARA V1 — Knowledge RAG

Tanggal: 2026-10-06. Status: DOCUMENTED_IMPLEMENTATION_WITH_OPEN_GATES.

Scope: V1; subordinate pada Architecture Contract, Verification Work Contract dan GATES existing. Dokumen ini menutup kekurangan dokumen, bukan bukti acceptance runtime.

## Implementasi V1
`app/knowledge/engine.py` adalah facade ke `app/knowledge/rag.py` dan SQLiteVectorStore. Default V1 memakai `data/knowledge/nusantara_knowledge.db`, terpisah dari production KB. Parameter `filter` facade saat ini reserved/diabaikan; tidak dijadikan batas authorization. Route menyaring canonical Evidence.score >= 0.50 lalu mengadaptasikannya ke Trust.relevance tanpa memutasi evidence asli. Relevansi bukan authority sumber.

EvidenceGroundingGuard, intent-aware checks dan abstention tetap digunakan. Evidence kosong/tidak mendukung harus menahan klaim; persyaratan, biaya, waktu, prosedur dan alamat tidak boleh diciptakan. Kemampuan guard tidak dianggap sempurna dari fixture tests. Provenance, authority, wilayah, versi, tanggal berlaku, conflict dan approval harus ditinjau sebelum jawaban layanan resmi diterima.

## Oracle dan gate terbuka
`app/evaluation/datasets/v1_recovery_oracle.json` berisi 3 PROJECT_FIXTURE, 1 NEGATIVE_CASE, 2 REVIEW_REQUIRED dan 1 MISSING. Hash snapshot dipisahkan dari hash sumber yang dideklarasikan. Tanggal publikasi/revisi tidak diperlakukan sebagai tanggal berlaku. Dua snapshot Tangerang tidak tersedia di default V1 DB. Syarat paspor/wilayah resmi belum tersedia. Fixture PASS tidak menjadi production correctness.

## Perubahan dan rollback
Tidak ingest/promote production tanpa governance approval. Verifikasi retrieval memakai snapshot DB terisolasi. Closure menambahkan metadata oracle saja, tanpa mengubah pertanyaan/jawaban/evidence; backup berada di `reports/v1-closure-backup-20261006/app/evaluation/datasets/v1_recovery_oracle.json`.

## Evidence dan change control

Source yang disebut adalah implementation reference. Bukti historis: `reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md`; hasil closure: `reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md`. Kontrak baru tidak mengubah source, test, konfigurasi atau database. Risiko: interpretasi dokumen melebihi evidence; karena itu gaps tetap eksplisit. Rollback dokumen: hapus hanya file baru ini setelah review, pertahankan kontrak sebelumnya.
