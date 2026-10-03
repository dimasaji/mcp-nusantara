# NUSANTARA AI V1 — VERIFICATION WORK CONTRACT

**ID Dokumen:** NUSANTARA-V1-VERIFICATION-WORK-CONTRACT  
**Scope:** NUSANTARA AI V1  
**Status:** ACTIVE  
**Purpose:** Technical verification, controlled implementation, regression, security, and release governance.

---

## 1. TUJUAN

Dokumen ini menjadi kontrak kerja teknis untuk seluruh proses verifikasi dan pengembangan NUSANTARA AI V1.

Tujuan utamanya:

- memastikan pekerjaan berbasis evidence;
- mencegah perubahan arsitektur tanpa review;
- menjaga CORE V1 tetap stable;
- mencegah duplicate engine dan duplicate configuration truth;
- memastikan setiap phase diverifikasi sebelum dianggap selesai;
- memastikan Claude Code bertindak sebagai implementation executor, bukan pengambil keputusan arsitektur;
- memastikan perubahan dapat diuji, diaudit, dan di-rollback.

---

## 2. PRINSIP UTAMA

### 2.1 Core V1 Protected

CORE V1 dianggap:

**LOCKED / STABLE**

Perubahan terhadap core tidak boleh dilakukan hanya karena kebutuhan phase baru.

Jika diperlukan perubahan terhadap core:

1. identifikasi dependency;
2. analisis impact;
3. dokumentasikan risiko;
4. ajukan proposal;
5. lakukan approval manusia;
6. implementasi secara minimal;
7. jalankan regression test.

### 2.2 No Duplicate Engine

Tidak boleh membuat engine kedua untuk fungsi yang sudah dimiliki NUSANTARA.

Gunakan:

- adapter;
- interface;
- service boundary;
- bridge;
- integration layer.

Bukan copy atau rewrite engine.

### 2.3 Evidence Before Implementation

Presence di source code bukan bukti bahwa sebuah capability sudah PASS.

Setiap capability harus dibuktikan melalui:

- source inspection;
- contract verification;
- unit test;
- integration test;
- security check;
- regression test.

---

## 3. STATUS DEFINISI

### IMPLEMENTED_OR_PRESENT

Source code, module, class, endpoint, atau dokumentasi ditemukan.

Ini hanya berarti **ada**.

Bukan berarti capability sudah benar.

### VERIFY

Capability ditemukan tetapi bukti perilaku belum lengkap.

### PASS

Capability telah memenuhi seluruh verification criteria yang relevan.

Minimal:

- source;
- contract;
- unit test;
- integration test;
- security verification;
- regression verification.

### FAIL

Capability tidak memenuhi contract atau test.

### NOT_STARTED

Belum ditemukan implementation yang relevan atau belum dimulai.

---

## 4. URUTAN KERJA WAJIB

Semua pekerjaan phase mengikuti urutan:

**INSPECT**
→ **UNDERSTAND**
→ **MAP**
→ **RISK**
→ **PROPOSE**
→ **APPROVAL**
→ **IMPLEMENT**
→ **TEST**
→ **SECURITY**
→ **REGRESSION**
→ **DOCUMENT**
→ **REPORT**

Tidak boleh langsung melakukan implementation sebelum inspection dan mapping.

Untuk perubahan berisiko, approval manusia wajib dilakukan sebelum implementation.

---

## 5. PEMBAGIAN PERAN

### GPT / Architecture & Verification Controller

Bertugas:

- memahami architecture contract;
- membaca source;
- memetakan dependency;
- mengidentifikasi risiko;
- menentukan verification criteria;
- menilai hasil test;
- menjaga scope phase;
- menentukan apakah pekerjaan siap dilanjutkan.

GPT tidak boleh menganggap source presence sebagai PASS.

### Human Owner

Bertugas:

- memberikan approval untuk perubahan berisiko;
- menentukan keputusan produk/arsitektur;
- menyetujui perubahan terhadap protected core;
- menyetujui release.

### Claude Code / Implementation Executor

Claude Code digunakan sebagai executor implementation.

Claude Code wajib:

- membaca architecture contract;
- membaca verification work contract;
- membaca source yang relevan;
- mengikuti scope pekerjaan;
- tidak mengubah architecture decision secara sepihak;
- tidak membuat duplicate engine;
- tidak menghapus failing test;
- tidak melewati governance layer;
- tidak melakukan autonomous production self-modification.

---

## 6. ONE PHASE AT A TIME

Pekerjaan dilakukan satu phase pada satu waktu.

Tidak diperbolehkan memberikan instruction seperti:

> implement Phase 8 sampai Phase 21 sekaligus

Workflow yang benar:

1. pilih satu phase;
2. inspect;
3. map;
4. risk analysis;
5. define verification criteria;
6. approval jika diperlukan;
7. implement;
8. test;
9. security;
10. regression;
11. document;
12. report;
13. baru lanjut ke phase berikutnya.

---

## 7. PHASE VERIFICATION CONTRACT

### Phase 8 — MCP

Verify:

- MCP interface;
- session handling;
- schemas;
- transport;
- error handling;
- authorization/governance boundary;
- integration dengan V1.

Tidak boleh bypass policy/trust/tool governance.

### Phase 9 — Tool Governance

Verify:

- tool registration;
- permission;
- validation;
- approval;
- audit trail;
- failure handling;
- dangerous-operation protection.

### Phase 10 — Experience

Verify:

- user/session context;
- interaction events;
- response experience;
- history/context handling;
- error experience.

### Phase 11 — Feedback

Verify:

- feedback capture;
- event schema;
- persistence;
- traceability;
- feedback-to-evaluation boundary.

Feedback tidak boleh langsung mengubah production behavior secara autonomous.

### Phase 12 — Evaluation

Verify:

- evaluation scenarios;
- evaluator;
- metrics;
- reproducibility;
- regression dataset;
- pass/fail criteria.

### Phase 13 — Failure Analysis

Verify:

- failure capture;
- classification;
- root-cause evidence;
- reproducibility;
- linkage ke evaluation.

### Phase 14 — Gap Detection

Verify:

- gap detection logic;
- evidence;
- confidence;
- false-positive handling;
- linkage ke knowledge/research pipeline.

### Phase 15 — Knowledge Discovery

Verify:

- candidate discovery;
- source provenance;
- source verification;
- deduplication;
- candidate vs trusted knowledge distinction.

Discovered knowledge tidak otomatis menjadi trusted knowledge.

Gate 15 sub-gate numbering (hybrid resolution):

- Gate 15.1 — Runtime Health Truth
- Gate 15.2 — Engine Runtime Truth
- Gate 15.3 — Graph Operational Truth
- Gate 15.4 — Operational Synthesis
- Gate 15 FINAL — Knowledge Discovery Final Contract

All five belong to Knowledge Discovery. They must remain locked
once validated PASS. Do not retroactively renumber.

### Phase 15.5–15.7 — Change Planning / Change Governance

Verify:

- ChangePlan schema completeness (14 fields per Section 11
  of CLAUDE_CONTRACT.MD);
- deterministic validator without LLM lookup (Section 44);
- approval wiring into existing ApprovalQueue + AuditTrail;
- status transitions PROPOSED → VALIDATED → APPROVED → IMPLEMENTED;
- rejection of transitions that bypass approval or skip evidence;
- no autonomous source modification;
- evidence attachment required for VALIDATED and APPROVED;
- APPROVED must never be inferred from LLM response alone.

Sub-gate numbering:

- Gate 15.5 — Change Plan Schema
- Gate 15.6 — Change Plan Validator
- Gate 15.7 — Approval Wiring
- Gate 15 CHANGE PLANNING FINAL — Change Planning Engine Final
  Contract

### Phase 16 — Experiment

Verify:

- experiment isolation;
- hypothesis;
- baseline;
- measurable result;
- rollback;
- no uncontrolled production mutation.

### Phase 17 — Improvement Proposal

Verify:

- proposal schema;
- evidence;
- impact analysis;
- risk analysis;
- expected benefit;
- human review boundary.

Proposal bukan implementation.

### Phase 18 — Human Approval

Verify:

- approval queue;
- approver identity;
- decision;
- timestamp;
- scope;
- audit trail;
- rejection path.

### Phase 19 — V1.x Development

Verify:

- approved change;
- compatibility;
- versioning;
- migration safety;
- regression.

V1.x tidak boleh menjadi alasan untuk merusak CORE V1.

### Phase 20 — Regression / Security

Verify:

- full relevant regression;
- security tests;
- input validation;
- authorization;
- prompt injection resistance;
- data leakage;
- unsafe tool execution;
- grounding bypass;
- error leakage.

### Phase 21 — Release / Rollback

Verify:

- release artifact;
- version;
- release checklist;
- backup;
- rollback procedure;
- rollback verification;
- release audit trail.

Release hanya dilakukan setelah required gates PASS.

---

## 8. RAG / GROUNDING REQUIREMENT

Knowledge-grounded response wajib memperhatikan:

- source;
- provenance;
- evidence;
- confidence;
- verification status;
- version/conflict information jika tersedia.

Evidence kosong harus fail closed.

Jawaban tidak boleh mengarang:

- persyaratan;
- prosedur;
- angka;
- biaya;
- durasi;
- alamat;
- ketentuan layanan.

Grounding validation tidak boleh dianggap sempurna hanya berdasarkan satu test.

Adversarial regression harus mencakup sekurang-kurangnya:

- unsupported numeric claim;
- unsupported cost;
- unsupported duration;
- unsupported requirement;
- unsupported procedure;
- unsupported address;
- empty evidence;
- conflicting evidence;
- multi-sentence answer;
- prompt injection dalam evidence.

---

## 9. NO AUTONOMOUS SELF-MODIFICATION

NUSANTARA tidak boleh secara autonomous:

- mengubah source production;
- mengubah policy;
- mengubah trust rules;
- mengubah model routing;
- mengubah tool permission;
- mengubah knowledge trusted state;
- melakukan release.

AI boleh:

- mendeteksi;
- menganalisis;
- membuat proposal;
- membuat evidence;
- menjalankan experiment terisolasi.

Perubahan production memerlukan human approval sesuai risk level.

---

## 10. NO DESTRUCTIVE DEVELOPMENT

Dilarang:

- menghapus test yang gagal hanya agar test suite PASS;
- menghapus core module tanpa migration plan;
- destructive database change tanpa approval;
- mengganti engine dengan duplicate implementation;
- menghapus audit trail;
- menghapus evidence kegagalan.

Jika terdapat legacy code, tandai dan evaluasi.

Jangan menghapus hanya karena terlihat tidak digunakan.

---

## 11. REGRESSION RULE

Setiap perubahan harus diuji terhadap:

1. test baru;
2. test terkait;
3. integration test;
4. security test;
5. regression test.

Perubahan dianggap belum selesai jika regression yang relevan gagal.

---

## 12. RISK LEVEL

### LOW

Perubahan dokumentasi, test, atau perubahan lokal tanpa perubahan behavior kritis.

### MEDIUM

Perubahan behavior, API, storage, retrieval, routing, atau integration.

### HIGH

Perubahan:

- CORE V1;
- security;
- trust;
- policy;
- tool permission;
- production data;
- release;
- rollback;
- autonomous behavior.

HIGH risk wajib melalui human approval sebelum implementation.

---

## 13. AUDIT EVIDENCE

Setiap phase harus menghasilkan evidence yang dapat ditelusuri:

- file yang diperiksa;
- source location;
- test command;
- test result;
- failure jika ada;
- security result;
- regression result;
- keputusan status.

Jangan menulis PASS tanpa evidence.

---

## 14. DEFINITION OF DONE

Sebuah phase hanya dapat dinyatakan selesai apabila:

- scope jelas;
- implementation dipahami;
- contract diverifikasi;
- unit test relevan PASS;
- integration test relevan PASS;
- security check relevan PASS;
- regression relevan PASS;
- tidak ada unresolved critical issue;
- dokumentasi diperbarui;
- hasil dilaporkan.

---

## 15. CURRENT GOVERNANCE RULE

Untuk audit dan development saat ini:

**PRIMARY SCOPE = V1**

**PRIMARY CHAT PATH = /v1**

`/v2` tidak boleh menjadi alasan untuk mengubah atau merombak `/v1` sebelum V1 verification gates selesai.

V2 diperlakukan sebagai target architecture / future integration surface.

---

## 16. FINAL RULE

Aturan utama kontrak ini:

> VERIFY BEFORE MODIFY.

Dan:

> IMPLEMENTED_OR_PRESENT ≠ PASS.

NUSANTARA AI harus berkembang melalui verifikasi terkontrol, bukan melalui rewrite atau autonomous modification.
