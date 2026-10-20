# NUSANTARA V1 — Trust Policy Approval

Tanggal: 2026-10-06. Status: DOCUMENTED_IMPLEMENTATION_WITH_OPEN_GATES.

Scope: V1; subordinate pada Architecture Contract, Verification Work Contract dan GATES existing. Dokumen ini menutup kekurangan dokumen, bukan bukti acceptance runtime.

## Implementasi V1
`app/trust/engine.py` menerima relevance; route mengadaptasi Evidence.score menjadi relevance dan mengembalikan enam field publik: supports_claim, confidence, risk_level, requires_human, evidence_count, evidence_available. Issues/details internal tidak diekspos oleh penambahan recovery. Assessment route menggunakan evidence terhadap user_input; bukan sertifikat bahwa setiap klaim final benar. Grounding final tetap pemeriksaan terpisah.

`app/policy/engine.py` dipakai GateIntegration: reasoning tidak grounded atau confidence rendah diblokir; tindakan sensitif memerlukan review. Registry tool memakai default_tool_policy yang sudah ada dengan keputusan ALLOW/REQUIRE_CONFIRMATION/REQUIRE_HUMAN/DENY. Perbedaan interface existing ini tidak diganti atau digabung oleh kontrak. Full policy-to-final-chat action enforcement tidak disimpulkan dari presence atau health status.

## Approval dan audit
`app/approval/queue.py` mengikat approval dengan hash payload, masa berlaku, reviewer berbeda peminta dan konsumsi sekali; default TTL 60 menit. Snapshot approval dipersist ke AuditTrail dan integrity diperiksa saat restore. Implementasi menyatakan dukungan single application worker; competing writers tidak didukung. Persetujuan LLM tidak menggantikan reviewer manusia. Source/prod knowledge/schema/release memerlukan governance sesuai risiko.

## Penerimaan dan rollback
Permission, denial, expired/payload mismatch/reuse approval dan audit integrity perlu bukti tests. Metadata official/verified dalam snapshot tidak sama dengan approved oracle. Keberadaan kontrak tidak menutup deployment/security/oracle gate yang belum dibuktikan. Closure tidak mengubah trust/policy/approval runtime; rollback hanya metadata oracle dan dokumen baru, dengan backup checkpoint terpisah.

## Evidence dan change control

Source yang disebut adalah implementation reference. Bukti historis: `reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md`; hasil closure: `reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md`. Kontrak baru tidak mengubah source, test, konfigurasi atau database. Risiko: interpretasi dokumen melebihi evidence; karena itu gaps tetap eksplisit. Rollback dokumen: hapus hanya file baru ini setelah review, pertahankan kontrak sebelumnya.
