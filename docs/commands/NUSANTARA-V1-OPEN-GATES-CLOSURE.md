Anda adalah Senior Principal AI Systems Engineer, Master Developer, QA Engineer, Security Engineer, dan Release Engineer untuk proyek NUSANTARA.

Baca terlebih dahulu:

* `reports/V1_RECOVERY_PROGRESS.json`
* `reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md`
* `docs/commands/NUSANTARA V1 RECOVERY MASTER.md`
* `docs/audit/GATES.md`
* seluruh contract yang sudah tersedia di `docs/contracts/`

TUJUAN:
Menutup OPEN MANDATORY GATES yang tercatat pada checkpoint tanpa mengulang pekerjaan yang sudah selesai dan tanpa mengubah arsitektur V1.

ATURAN KERAS:

1. V1 adalah scope utama.
2. Jangan mengubah `/v2`.
3. Jangan membuat Agent/LangGraph/Graphify runtime.
4. Jangan mengganti Hermes, LanguageEngine, KnowledgeEngine, TrustEngine, PolicyEngine, atau configuration truth.
5. Jangan menghapus test.
6. Jangan melemahkan security test.
7. Jangan membuat oracle/fakta resmi secara asumsi.
8. Jangan mengubah database produksi.
9. Jangan menginstal dependency baru kecuali benar-benar diperlukan dan mendapat persetujuan.
10. Jangan mengulang Phase 0–4 atau baseline yang sudah selesai.
11. Baca checkpoint sebelum melakukan perubahan.
12. Setiap perubahan harus mempunyai alasan, risiko, evidence, dan rollback.
13. Jika sebuah gate tidak dapat dibuktikan, tandai OPEN/NOT_RUN; jangan mengubahnya menjadi PASS secara administratif.

==================================================
STEP 1 — PHASE 5/6: KNOWLEDGE + ORACLE
======================================

Buka:

`app/evaluation/datasets/v1_recovery_oracle.json`

dan:

* `reports/V1_RECOVERY_KNOWLEDGE_INVENTORY.json`
* `reports/V1_RECOVERY_RAG.json`
* `reports/V1_RECOVERY_ORACLE_SOURCE_PINS.json`

Audit seluruh 7 kasus.

Khusus:

* KTP
* Paspor
* Nasi Goreng
* negative retrieval
* dua kasus Tangerang
* kasus passport requirements yang masih MISSING

Untuk setiap kasus tentukan:

* expected_document
* expected_answer
* required_evidence
* source
* source authority
* wilayah layanan
* versi
* tanggal berlaku
* status authoritative
* status oracle

JANGAN mengubah MISSING menjadi PASS tanpa sumber yang benar-benar mendukungnya.

Untuk sumber Tangerang, gunakan hanya snapshot/sumber yang sudah tersedia dan lakukan review metadata sumber.

Jika memerlukan data resmi baru tetapi belum tersedia:
STOP pada kasus tersebut dan tandai `REVIEW_REQUIRED` atau `MISSING`.

Jangan ingest atau promote knowledge production tanpa governance approval.

==================================================
STEP 2 — CONTRACT CLOSURE
=========================

Buat hanya contract yang benar-benar masih missing:

* `docs/contracts/NUSANTARA-RUNTIME-EXECUTION-CONTRACT-V1.md`
* `docs/contracts/NUSANTARA-INTELLIGENCE-MODEL-CONTRACT-V1.md`
* `docs/contracts/NUSANTARA-KNOWLEDGE-RAG-CONTRACT-V1.md`
* `docs/contracts/NUSANTARA-AGENT-ORCHESTRATION-CONTRACT-V1.md`
* `docs/contracts/NUSANTARA-TOOL-MCP-API-CONTRACT-V1.md`
* `docs/contracts/NUSANTARA-TRUST-POLICY-APPROVAL-CONTRACT-V1.md`

Jangan overwrite contract yang sudah ada.

Kontrak harus konsisten dengan implementation V1 saat ini.

Agent Orchestration Contract hanya mendefinisikan boundary, lifecycle, permission, tool access, trust, policy, approval, audit, timeout, budget dan rollback.

JANGAN mengimplementasikan Agent runtime.

==================================================
STEP 3 — PHASE 8: FILESYSTEM SECURITY
=====================================

Periksa apakah environment saat ini mempunyai privilege yang diperlukan.

Jalankan:

`.venv/Scripts/python.exe -m pytest tests/v2/test_devcore.py::TestSecurityGate::test_symlink_outside_workspace_blocked -o addopts='' -p no:cacheprovider -q -rs`

Jika SKIP karena privilege:

* jangan ubah test;
* jangan ubah security logic;
* jangan klaim PASS;
* dokumentasikan requirement environment.

Jika privilege tersedia:
jalankan test sampai mendapatkan hasil nyata PASS/FAIL.

==================================================
STEP 4 — PHASE 10: DEPLOYMENT
=============================

Periksa target deployment yang benar-benar ditentukan oleh proyek.

Jangan menganggap localhost sebagai production.

Jika Docker tersedia:

* build image;
* start container;
* health check;
* `/v1/health`;
* `/v1/knowledge/search`;
* `/v1/chat`;
* runtime identity;
* representative workload;
* stop;
* restart;
* rollback.

Jika Docker tidak tersedia:
jangan menginstalnya otomatis.
Dokumentasikan NOT_RUN dan alasan.

Jika target production belum ditentukan:
jangan membuat asumsi.
Dokumentasikan deployment target sebagai OPEN.

Gunakan candidate database/knowledge terisolasi untuk verification.

==================================================
STEP 5 — UPDATE CHECKPOINT
==========================

Update:

`reports/V1_RECOVERY_PROGRESS.json`

hanya untuk pekerjaan yang benar-benar telah dibuktikan.

Jangan mengubah historical evidence.

Update status Phase 5, 6, 8, dan 10 secara akurat.

==================================================
STEP 6 — TARGETED TESTING
=========================

Setelah perubahan, jalankan hanya test yang relevan.

Jangan menjalankan seluruh regression berulang kali jika tidak diperlukan.

Jika perubahan menyentuh runtime/contract/RAG/security:
jalankan targeted tests terlebih dahulu.

Setelah seluruh open gates selesai atau mencapai kondisi final yang dapat dipertanggungjawabkan, jalankan final regression sekali:

`.venv/Scripts/python.exe -m pytest tests -o addopts='' -p no:cacheprovider --basetemp=reports/v1-final-closure-tmp --junitxml=reports/V1_FINAL_CLOSURE.xml -q`

Target:

* 0 FAIL
* 0 ERROR
* mandatory security test tidak SKIP

==================================================
STEP 7 — FINAL DECISION
=======================

Buat:

`reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md`

Isi:

1. Gate status
2. Changes
3. Tests
4. Evidence
5. Remaining gaps
6. Security status
7. Knowledge/oracle status
8. Deployment status
9. Rollback status
10. V1 acceptance decision

Hanya gunakan:

`V1 ACCEPTED`

jika seluruh mandatory gates benar-benar PASS.

Jika masih ada:

* mandatory SKIP,
* REVIEW_REQUIRED,
* MISSING,
* NOT_RUN,
* deployment yang belum diverifikasi,

maka hasil harus:

`V1 ACCEPTANCE = FAIL / HOLD`

Jangan melakukan Agent/LangGraph/Graphify runtime setelah command ini.

STOP setelah open gates ditutup atau status finalnya terbukti.
