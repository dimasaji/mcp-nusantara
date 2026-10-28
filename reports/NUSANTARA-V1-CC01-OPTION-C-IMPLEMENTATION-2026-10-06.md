# NUSANTARA V1 — CC-01 Opsi C: Laporan Implementasi dan VERIFY

Tanggal: 2026-10-06 (Asia/Jakarta)

## Hasil

**SELESAI untuk scope utama Opsi C. Verifikasi implementasi: PASS_SCOPED. Penerimaan keseluruhan V1: FAIL / HOLD.**

User memilih Opsi C, lalu menyetujui implementasi route, test baru, dan verifikasi melalui “Ya,,lanjukan”. Proposal sebelumnya tetap menjadi bukti historis PROPOSAL_ONLY; persetujuan implementasi dicatat terpisah di `V1_CC01_IMPLEMENTATION_PROGRESS.json`.

Respons sukses `/v1/chat` kini dibangun melalui proyeksi eksplisit dengan schema Pydantic bertipe ketat. Context internal `gate_pipeline` dan `developer_core`, termasuk salinan reasoning/policy/memory di dalamnya, tidak masuk keluaran publik. Exception umum yang ditangkap route mengembalikan HTTP 500 dengan pesan tetap `Terjadi kesalahan internal server` tanpa teks exception.

## Scope dan integritas

- File runtime yang diubah: `app/api/routes.py`.
- Test baru: `tests/test_v1_response_projection.py`.
- Backup sebelum implementasi: `reports/v1-cc01-option-c-backup-20261006/app/api/routes.py`. Hash backup cocok dengan baseline working tree user sebelum implementasi.
- Audit 299 file baseline: hanya `app/api/routes.py` berubah. Seluruh 298 file baseline lain tetap identik, termasuk existing tests, engines, `/v2`, contracts, konfigurasi, kedua database, dan checkpoint historis yang tercakup.
- Perubahan user yang sudah ada sebelum pekerjaan ini dipertahankan. Diff implementasi diperiksa terhadap backup working tree, bukan hanya terhadap Git HEAD.
- Graph AST diperbarui sesuai instruksi proyek: 4.619 nodes, 9.143 edges, 330 communities. Tidak menjalankan ekstraksi semantik atau pelabelan LLM. Graphify melaporkan beberapa direktori laporan sementara tidak dapat dibaca serta ekstraksi PDF dilewati karena pypdf tidak tersedia; pembaruan graph kode selesai.

## Respons publik Opsi C

| Bagian | Field yang dikembalikan |
| --- | --- |
| Root | session_id, response, trust, model, provider_status, latency_ms, grounding, understanding, problem, evidence, timestamp |
| trust | supports_claim, confidence, risk_level, requires_human, evidence_count, evidence_available |
| grounding | enabled, grounded, reason |
| understanding | intent |
| problem | goal berupa string atau null |
| Setiap evidence | document_id, title, chunk, score |

Field tambahan tidak disalin ke respons. `understanding.input/output/entities/metadata`, `trust.issues/details`, `grounding.unsupported_sentences`, dan `evidence.source/metadata` tidak dipublikasikan. Reason grounding dibatasi ke kode yang dikenal; nilai lain menjadi `not_evaluated`. Goal non-scalar menjadi null tanpa serialisasi object internal.

Perhitungan trust, jawaban, dan pemilihan evidence tetap menggunakan pipeline yang ada. Test membandingkan nilai trust, jawaban, dan empat field citation untuk memastikan nilainya dipertahankan. Proyeksi citation tidak menetapkan sumber menjadi otoritatif dan tidak menerapkan kontrol akses knowledge.

Schema menolak nilai numerik non-finite/di luar rentang serta tipe yang tidak sesuai. Batas meliputi session_id 128 karakter, model 256, document_id 256, title 1.024, chunk 20.000, evidence maksimal 20 item, intent/reason 128, goal 2.000, dan timestamp 64. Confidence/score berada pada rentang 0–1. Jawaban tidak dipotong. Pelanggaran schema pada route menghasilkan kegagalan tertutup HTTP 500 yang tersanitasi, bukan pemotongan diam-diam.

## Bukti VERIFY

| Pemeriksaan | Hasil | Bukti |
| --- | --- | --- |
| Test terarah akhir | 49 passed, 4 subtests passed, 0 failed | `V1_CC01_TARGETED_FIXED.xml` |
| Regresi penuh — satu run | 267 passed, 28 subtests passed, 1 skipped, 0 failed, 0 errors; 78,41 detik | `V1_CC01_REGRESSION.xml` |
| Static security scan yang tersedia | 0 findings, PASS_SCOPED | `V1_CC01_SECURITY.json` |
| Hash protected baseline | 298 identik; satu perubahan runtime yang diizinkan | `V1_CC01_OPTION_C_IMPLEMENTATION.json` |
| Backup working tree | Cocok dengan hash baseline route | `V1_CC01_OPTION_C_IMPLEMENTATION.json` |

JUnit menghitung subtest sebagai testcase tambahan: targeted akhir 53 testcase; regresi penuh 296 testcase termasuk satu skip. Angka ringkasan pytest di atas memisahkan test dan subtest.

Test baru menguji allowlist root/nested, unknown keys, salinan internal di developer snapshot, context None/kosong/rusak, trust dan citation, reason/goal yang tidak aman, numeric bounds, citation berlebih, header korelasi, penutupan provider, dan pemanggilan memory internal. Cabang HTTP mencakup evidence fast path, Ollama, offline, unsupported, missing, requires_human, policy-sensitive, serta local_rule melalui fixture sintetis. Helper local_rule saat ini tidak menghasilkan jawaban dalam implementasi nyata; fixture ini bukan bukti jalur live aktif.

Test juga memeriksa HTTP 500 umum, 503/504 yang sudah dibatasi, ProviderUnavailableError yang mempertahankan shared handler, dan validasi input kosong sebelum pipeline. Pengujian HTTP memakai TestClient dan dependency mock terisolasi; ini bukan bukti deployment atau keberhasilan provider live.

Percobaan targeted awal disimpan di `V1_CC01_TARGETED.xml`: 27 passed, 1 failed. Penyebabnya ekspektasi test baru bahwa context reasoning internal null menghasilkan 200, sementara kode internal lama memang gagal sebelum proyeksi. Ekspektasi test baru dikoreksi menjadi HTTP 500 tersanitasi. Existing tests tidak diubah dan perilaku engine tidak diperbaiki di luar scope.

Satu skip regresi adalah test symlink Windows yang membutuhkan privilege sistem. Skip ini belum memenuhi gate keamanan wajib. Warning Starlette/httpx yang ada tidak menyebabkan kegagalan test. Static scan memiliki cakupan dan pengecualian scanner yang ada; hasil nol temuan bukan sertifikasi keamanan keseluruhan.

## Dampak kompatibilitas dan batas hasil

UI yang membaca response, intent, goal, model, latency, serta title/score/count evidence mempertahankan field yang diperlukan. Drawer JSON UI kini menerima proyeksi publik. Evaluator yang memakai response serta evidence.chunk/document_id tetap mempunyai field tersebut.

Client yang menggunakan `understanding.input/output`, context internal, atau metadata citation mengalami perubahan bentuk respons yang disengaja oleh Opsi C. Script standalone `scripts/test_api_contract.py` masih memiliki assertion legacy input/output; script tersebut tidak diubah atau dilemahkan, dan tidak termasuk klaim regresi pytest sukses. Kompatibilitas client eksternal yang belum diinventarisasi: **NOT_PROVEN**.

Shared exception handlers, framework validation, dan endpoint lain tidak termasuk implementasi ini. Validasi HTTP 422 masih dapat membawa input dalam detail validasi; handler provider/shared dapat membawa message/details/path/request URL sesuai perilaku yang ada. Hasil ini tidak mengklaim seluruh error response atau seluruh API sudah memenuhi proyeksi Opsi C. Perubahan shared handler memerlukan scope lanjutan.

## Gate V1 yang masih terbuka

- Oracle: dua snapshot REVIEW_REQUIRED dan satu kasus persyaratan paspor MISSING; fixture tidak dipromosikan menjadi sumber resmi.
- Test symlink Windows wajib masih SKIPPED karena privilege belum tersedia.
- Deployment, workload, restart, dan rollback operasional: NOT_RUN; Docker/target produksi belum dibuktikan.
- Temuan compliance CC-02 sampai CC-06, termasuk wiring orchestration/provider dan ownership/TTL/cap memory, tidak ditutup oleh perubahan proyeksi ini.
- Keputusan freeze/compliance historis tidak ditulis ulang. Penutupan CC-01 scope utama telah diverifikasi pada source dan test, tetapi re-acceptance/freeze V1 keseluruhan membutuhkan audit gate lanjutan.

Service user yang sudah berjalan tidak direstart. Source build identity dalam evidence adalah identitas source kandidat setelah perubahan; tidak membuktikan service lama sudah memuat build ini. Tidak ada deploy, perubahan database/configuration, engine baru, atau agent runtime baru.

## Checkpoint dan pemulihan

Checkpoint implementasi ditandai COMPLETE dengan satu run regresi penuh. Resume membaca checkpoint ini dan tidak mengulangi pekerjaan yang sudah lulus. Bukti recovery/closure/compliance/proposal sebelumnya dipertahankan.

Backup hanya untuk pemulihan selektif terhadap perubahan Opsi C, setelah memeriksa perubahan user yang lebih baru. Jangan melakukan reset working tree global. Backup mengandung perilaku proyeksi lama yang membuka context internal; bila rollback diperlukan, tahan kandidat/release sampai batas respons aman diverifikasi. Rollback produksi belum diuji.

**Keputusan akhir: implementasi utama Opsi C selesai dan terverifikasi; V1 tetap FAIL / HOLD.**
