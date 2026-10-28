# NUSANTARA V1 — Final Closure Report

Tanggal: 2026-10-06. Command: `docs/commands/NUSANTARA-V1-OPEN-GATES-CLOSURE.md`.

**V1 ACCEPTANCE = FAIL / HOLD**

Eksekusi command selesai sampai keputusan akhir yang dapat dibuktikan. V1 belum diterima: mandatory security masih SKIP, dua oracle REVIEW_REQUIRED, satu MISSING, dan container/production deployment NOT_RUN. Phase 0–4 dan baseline tidak diulang. Final regression closure dijalankan tepat satu kali.

## 1. Gate status

| Gate closure | Hasil | Evidence |
|---|---|---|
| Phase 5 Knowledge/RAG | VERIFY / OPEN official knowledge | V1_RECOVERY_RAG.json historis; V1_CLOSURE_ORACLE_AUDIT.json |
| Phase 6 Oracle | AUDITED_WITH_GAPS | V1_CLOSURE_ORACLE_AUDIT.json |
| Enam missing contracts | CLOSED dokumentasi; compliance runtime tetap mengikuti evidence | docs/contracts/; hashes kontrak lama pada audit/integrity |
| Phase 8 Filesystem security | SKIP_PRIVILEGE / OPEN | V1_CLOSURE_FILESYSTEM.xml; V1_FINAL_CLOSURE.xml |
| Phase 10 Container/production | NOT_RUN / OPEN | V1_CLOSURE_ENVIRONMENT.json |
| Targeted checks | PASS: 31 tests, 4 subtests | V1_CLOSURE_TARGETED.xml |
| Final regression | 240 passed, 0 failed, 0 errors, 1 skipped, 28 subtests passed | V1_FINAL_CLOSURE.xml |
| Secret scan | PASS_SCOPED: 0 findings | V1_CLOSURE_SECURITY.json |

Recovery phase numbers above differ from the architecture GATES capability numbering; no renumbering or administrative PASS was applied to docs/audit/GATES.md.

## 2. Changes

- Oracle schema 2 menambahkan source_authority, service_region, version, effective_date, authoritative_status dan metadata review. Semua pertanyaan, expected_document, jawaban, required_evidence, intent dan status oracle sebelumnya tetap sama.
- Enam dokumen baru: Runtime Execution, Intelligence Model, Knowledge RAG, Agent Orchestration Boundary, Tool MCP API, Trust Policy Approval. Dua kontrak existing tidak ditimpa; hash terverifikasi sama.
- Kontrak memisahkan implementasi existing, acceptance requirements dan gaps. Agent contract hanya boundary/lifecycle/permission/tools/trust/policy/approval/audit/timeout/budget/rollback; tidak membuat runtime baru.
- Checkpoint memuat closure steps 1–7, evidence dan resume rule. Snapshot checkpoint lama tersimpan untuk audit. Historical XML/JSON recovery tetap digunakan sebagai bukti historis.
- Tidak mengubah `/v2`, engine, model, security logic, test, configuration truth atau knowledge DB; tidak memasang dependency, mengaktifkan tool, merilis atau me-restart layanan pengguna.

Alasan: menutup kekurangan dokumen dan menghilangkan metadata oracle yang ambigu. Risiko utama adalah snapshot/fixture dianggap fakta layanan yang berlaku; status review, nilai null dan batas bukti dicatat eksplisit. Perubahan oracle JSON mengubah source fingerprint, meski perilaku model/retrieval tidak berubah.

## 3. Tests

Targeted contract/runtime identity/trust/approval/tool governance/stage budget/evaluation harness: **31 passed, 4 subtests passed** dalam 6.19 detik.

Targeted mandatory filesystem: **1 skipped** dalam 0.12 detik, pesan `Windows membutuhkan privilege untuk membuat symlink`. Tidak ada logic/test yang dilemahkan.

Final regression native `.venv/Scripts/python.exe`: **240 passed, 1 skipped, 28 subtests passed** dalam 90.63 detik. JUnit mencatat 269 testcase termasuk subtests, **0 failures, 0 errors**, 1 skipped. Git integration menggunakan executable existing. Regresi akhir tidak diulang.

Ada satu warning deprecation Starlette/httpx existing; tidak memasang dependency untuk menutup warning.

## 4. Evidence dan integrity

Semua nama artifact di tabel berada di `reports/` kecuali docs/contracts. Bukti tambahan:

- `V1_CLOSURE_INTEGRITY.json`: hash kedua knowledge DB tidak berubah; semua field oracle lama tetap sama; hash kontrak existing tetap sama; backup availability/integrity diperiksa.
- `V1_CLOSURE_BUILD_ID.json`: current source fingerprint **sha256:1f6298a5c04d9a751cf3f16b461ba376429970669758a77cdd595f61d6d91b8d**. Endpoint identity equality dibuktikan targeted TestClient; ini tidak membuktikan deployment proses candidate/produksi build terbaru.
- `V1_RECOVERY_ORACLE_SOURCE_PINS.json`: source pins historis tetap cocok dengan snapshot Markdown yang diaudit.
- `V1_RECOVERY_PROGRESS.json`: completed closure dan gate tersisa; checkpoint sebelumnya di `v1-closure-backup-20261006/reports/V1_RECOVERY_PROGRESS.json`.
- `prepare_v1_closure.py`: persiapan satu kali dengan guard jika audit sudah ada; membaca SQLite mode read-only, tidak ingest.

Graphify diperbarui AST saja: 4410 nodes, 8787 edges, 307 communities. Beberapa direktori temp terlindung tidak terindeks; semantic document extraction/LLM labeling tidak dijalankan. Tidak ada Graphify/Agent/LangGraph runtime baru.

## 5. Knowledge/oracle per kasus

| Kasus | Source/authority/wilayah | Versi/tanggal berlaku | Status |
|---|---|---|---|
| ktp-definition-local | V1 legacy DB, test fixture, evaluasi lokal | SHA256 text fixture; effective_date null/not applicable | PROJECT_FIXTURE; evidence text cocok |
| paspor-definition-local | V1 legacy DB, benchmark fixture, evaluasi lokal | SHA256 text fixture; effective_date null/not applicable | PROJECT_FIXTURE; definisi tidak membuktikan syarat |
| nasi-goreng-local | V1 legacy DB, benchmark fixture, evaluasi lokal | SHA256 text fixture; effective_date null/not applicable | PROJECT_FIXTURE; evidence text cocok |
| tangerang-ktp-pemula-snapshot | Dukcapil snapshot declared official, Kota Tangerang | SHA256 full Markdown; published 2025-12-03; effective_date null | REVIEW_REQUIRED; tidak ada di default V1 DB |
| tangerang-sop-data-pribadi-snapshot | SOP snapshot declared official, Kota Tangerang | SHA256 Markdown/PDF; revisi tertulis Agustus 2018; effective_date null | REVIEW_REQUIRED; runtime document ID unknown |
| paspor-requirements-missing | Tidak tersedia; wilayah belum ditentukan | version/effective_date null | MISSING; kasus dihentikan sampai sumber sesuai tersedia |
| unknown-service-negative | Synthetic test, evaluasi lokal | synthetic-negative-v1; effective date not applicable | NEGATIVE_CASE; harus clarify/refuse tanpa fabrikasi |

Expected document/answer/required evidence/source untuk ketujuh kasus tercantum lengkap di audit JSON dan oracle. Tidak menambahkan fakta layanan baru.

Tangerang: full Markdown hash cocok pin recovery. Manifest/source header KTP menyatakan hash content yang berbeda dari full Markdown; derivasi hash content belum dibuktikan independen. Published date tidak menjadi effective date. Snapshot 2022/2024 memiliki persyaratan/konteks berbeda sehingga konflik dan validitas saat ini perlu review.

SOP: PDF original hash cocok SOURCE_HASH; teks `Nomor SOP PIAK-03` tersedia. SERVICE/UNIT blank, SCENARIO kedatangan membutuhkan review, tanggal pengesahan kosong. Nomor SOP yang terbaca tidak membuktikan validity layanan saat ini. Tidak ada review manusia/approval produksi yang diasumsikan.

## 6. Security

Privilege list tidak memuat SeCreateSymbolicLinkPrivilege. Environment diperlukan: akun Windows dengan privilege symlink, atau Developer Mode yang benar-benar memungkinkan creation; alternatif controlled Linux runner. Test harus memperoleh hasil nyata di environment tersebut sebelum mandatory gate PASS.

Scanner existing menghasilkan 0 findings. Exclusions dan perlakuan unreadable files tetap existing; scope statis ini bukan bukti seluruh secret/risk runtime tidak ada. Filesystem gate tetap OPEN meski seluruh test lainnya lulus.

## 7. Deployment

Docker tidak ditemukan di PATH maupun lokasi default Docker Desktop. Dockerfile, compose utama dan compose audit diperiksa; compose menentukan topology localhost/candidate, bukan production host yang teridentifikasi.

Build, container start, health, `/v1/health`, knowledge/chat container, identity container, representative workload, stop, restart dan rollback: **NOT_RUN**. Target produksi: **OPEN_NOT_DEFINED**. Docker tidak diinstal otomatis. Tidak ada candidate DB baru untuk deployment karena deployment tidak dijalankan; tidak ada database produksi yang diubah.

Bukti candidate lokal recovery sebelumnya tetap historis. Build sekarang berubah karena metadata oracle; bukti tersebut tidak dipakai untuk mengklaim container/production PASS terbaru. Layanan pengguna port 8000/8002 tidak dihentikan/restart oleh closure.

## 8. Rollback

Backup oracle dan checkpoint sebelum closure tersedia di `reports/v1-closure-backup-20261006/`; hash tersimpan dalam integrity artifact. File backup dibaca untuk membuktikan seluruh field oracle lama tetap sama. Restore nyata tidak dijalankan karena perubahan closure tidak gagal.

Rollback perubahan ini: review diff pengguna, pulihkan hanya metadata oracle yang diubah dari backup dan hapus selektif enam kontrak baru jika dibutuhkan; checkpoint/audit/evidence closure dipertahankan sebagai histori. Jangan melakukan reset working tree atau mengubah DB. Rollback produksi/container belum dilakukan atau dibuktikan: **NOT_RUN**.

## 9. Remaining gaps dan keputusan

1. Review authority, conflict, versi, tanggal berlaku dan approval dua sumber Tangerang; runtime knowledge resmi V1 belum tersedia melalui jalur approved.
2. Sumber resmi syarat paspor untuk wilayah layanan yang ditentukan belum tersedia.
3. Mandatory symlink escape test membutuhkan environment dengan privilege dan hasil nyata.
4. Docker/container runner serta target produksi yang ditentukan; evidence workload, stop/restart dan rollback pada candidate terisolasi belum tersedia.

**V1 ACCEPTANCE = FAIL / HOLD.** Command closure selesai dengan open mandatory gates terbukti. Lanjut hanya gate tersisa setelah evidence/environment baru tersedia; jangan ulang Phase 0–4, baseline, persiapan closure, atau regression akhir tanpa perubahan relevan. Tidak melanjutkan implementasi Agent/LangGraph/Graphify runtime.
