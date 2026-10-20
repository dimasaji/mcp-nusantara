# ROADMAP_STATUS — V2 Phase 0–21

Pembaruan 2026-10-06. Nomor di sini mengikuti roadmap V2; penomoran V1 dalam run_tests.py berbeda. Laporan 2026-10-05 merupakan bukti historis.

Sesuai verification contract, VERIFY berarti masih ada kriteria yang belum terbukti. Tes yang lulus membuktikan lingkup yang diuji, bukan seluruh blueprint atau kesiapan produksi. Semua phase sudah diperiksa; seluruh phase belum dapat dinyatakan PASS.

| Phase | Status menyeluruh | Implementasi/verifikasi terbaru | Kriteria tersisa |
|---|---|---|---|
| 0 Discovery | VERIFY | Baseline, risk register, audit gap dan dependency graph tersedia | Inventaris target produksi |
| 1 Architecture | VERIFY | Adapter menggunakan engine yang ada | Review akhir arsitektur/deployment |
| 2 Hardening | VERIFY | Stage V1 bounded, event loop responsif, worker timeout, provider 503, konteks/token dibatasi | Thread Python tidak dapat dibunuh saat timeout; SLA end-to-end |
| 3 Observability | VERIFY | Stage/request trace, token usage, rotasi telemetry, monitoring UI | Retensi audit dan kapasitas produksi |
| 4 Trust | VERIFY | Trust memeriksa jawaban dan mengembalikan provenance | Kalibrasi authority dan verifikasi faktual |
| 5 Policy | VERIFY | Policy V1 dipakai; auth/admin dan approval-bound payload diuji | Matriks izin dan identitas produksi |
| 6 Memory | VERIFY | Chat V2 opt-in, sesi acak, isolasi, persistence, TTL, delete dan batas history diuji; purge saat akses baca/tulis, create dan pembukaan store terbukti menghapus file kedaluwarsa | Episodic/vector memory belum dibuktikan; retensi saat layanan idle belum dijadwalkan |
| 7 RAG | VERIFY | Engine existing dipertahankan; metadata retrieval/trust tersedia | Knowledge domain yang disahkan, parser PDF/DOCX end-to-end dan dataset representatif |
| 8 MCP | VERIFY | Client SDK nyata initialize/list/call melalui stdio dan governed registry | Integrasi host produksi; transport jaringan/auth |
| 9 Tools | VERIFY | Tool read-only, penolakan injection/unknown tool dan audit diuji | Isolasi OS/container untuk tool berisiko |
| 10 Experience | VERIFY | Analisis event/feedback tersedia di API admin dan UI | Korelasi pengalaman produksi |
| 11 Feedback | VERIFY | Tombol feedback chat terhubung request ID; backend diuji | Uji pengguna seluruh alur pada model nyata |
| 12 Evaluation | VERIFY | API nyata, 12 skenario, records/error/hash dataset, baseline dan deteksi regresi | Oracle wilayah/SOP dan ambang kualitas; skor leksikal bukan verifikasi fakta |
| 13 Failure analysis | VERIFY | Analisis existing terhubung event/feedback | Validasi klasifikasi lintas request produksi |
| 14 Gap detection | VERIFY | Gap dapat menghasilkan proposal melalui API | Confidence heuristik belum terkalibrasi |
| 15 Discovery | VERIFY | HTTPS allowlist host eksplisit, DNS pinned publik, batas ukuran, kandidat durable/review | Sumber resmi, fetch domain nyata, promosi berapproval dan pencarian RAG end-to-end |
| 16 Experiment | VERIFY | Mesin eksperimen dan pembanding existing diuji | Dataset/eksperimen representatif dan penjadwalan bila diperlukan |
| 17 Proposal | VERIFY | Proposal API dari gap, persistence dan antrean review diuji | Proposal domain nyata dan keputusan manusia |
| 18 Human approval | VERIFY | UI browser, audit snapshot, restart dan consume sekali diuji | Identitas masih admin-token; single worker; audit legacy tanpa snapshot tidak direkonstruksi |
| 19 Development | VERIFY | Branch Git nyata dibuat setelah approval consumed/payload cocok | Change request nyata, implementasi kandidat dan review |
| 20 Regression/security | VERIFY | Regresi lengkap, compile, auth, injection, leakage, secret scan, health/chat load dijalankan | Gate fakta, SLA dan beban representatif |
| 21 Release/rollback | VERIFY | Backup checksum, restore aman, fault injection staging dan health pulih | Readiness PASS, approval manusia, target deployment; belum rilis produksi |

## Bukti

- reports/MEMORY_RETENTION_2026-10-06.md: tes terarah retensi sesi, V2 core dan context budget; 39 tes serta 4 subtes lulus. Tidak mengubah gate release.
- audit_reports/ALL_PHASES_FINAL_2026-10-06.xml: regresi lengkap terbaru.
- RELEASE_READINESS_REPORT.md: gate terkini; bukan otomatis PASS ketika unit test lulus.
- audit_reports/EVAL_V1_2026-10-06.json: baseline historis layanan utama, tidak ditimpa kandidat.
- audit_reports/EVAL_V1_STAGING_FINAL_2026-10-06.json: pengukuran ulang kandidat staging.
- audit_reports/LOAD_HEALTH_2026-10-06.json dan LOAD_CHAT_2026-10-06.json: health/chat terpisah, sampel kecil bukan SLA.
- audit_reports/REVIEW_UI_2026-10-06.png: UI dengan fixture staging yang ditolak.
- audit_reports/ALL_PHASES_WORK_2026-10-06.txt: scope, hasil dan cara menjalankan.

Baseline lama yang menyatakan HTTP/MCP/persistence/Git/rollback belum pernah diuji kini digantikan bukti tersebut. Ini tidak berarti seluruh kriteria phase terpenuhi.

## Menutup gate

1. Tentukan wilayah layanan/SOP resmi, review oracle dan ambang kualitas, sahkan knowledge melalui approval.
2. Benchmark dan load representatif pada target; perbaiki kegagalan sebelum rilis.
3. Lengkapi kriteria tersisa per phase sesuai matriks.
4. Approval release setelah readiness PASS; ulangi backup/restore pada target sebelum deployment.
