# NUSANTARA AI — V1 ARCHITECTURE CONTRACT

**Document ID:** NUSANTARA-ARCHITECTURE-CONTRACT-V1
**Repository:** mcp-starter
**Status:** FINAL
**Scope:** V1 Core + V1 API + V2 Extension Boundary

## 1. TUJUAN

Dokumen ini mengunci arsitektur NUSANTARA AI agar pengembangan berikutnya tidak membuat Core Engine kedua, menduplikasi Hermes, membuat source of truth ganda, atau mengubah Core V1 tanpa kontrol.

## 2. PRINSIP UTAMA

- V1 Core adalah foundation.
- Hermes V1 tidak boleh diduplikasi.
- V2 adalah extension layer, bukan Core baru.
- Tidak boleh ada duplicate source of truth.
- `/v1` dipertahankan sebagai compatibility boundary.
- Perubahan berisiko memerlukan human approval.
- Tidak boleh ada destructive change tanpa migration dan rollback plan.
- R&D tidak boleh otomatis mengubah production.
- Runtime evidence lebih kuat daripada sekadar keberadaan file/module.

## 3. V1 CORE

V1 Core terdiri dari:

- LanguageEngine
- ProblemEngine
- ReasoningEngine
- ModelRouter / Provider abstraction
- HermesAgent sebagai orchestrator V1

Execution path:

User
→ FastAPI `/v1`
→ HermesAgent
→ LanguageEngine
→ ProblemEngine
→ ReasoningEngine
→ Model / Provider

## 4. HERMES V1

Lokasi utama:

`app/hermes/agent.py`

Hermes V1 menggunakan:

- LanguageEngine
- ProblemEngine
- ProblemDetector
- ProblemClassifier
- ReasoningEngine
- ModelRouter / Provider

Tidak boleh dibuat Hermes kedua hanya untuk menggantikan atau menduplikasi fungsi Hermes V1.

## 5. KNOWLEDGE / RAG

Knowledge dan RAG merupakan service/layer pengetahuan.

Lokasi:

- `app/knowledge/`
- `app/rag/`

Keberadaan KnowledgeEngine tidak otomatis berarti RAG sudah menjadi bagian internal HermesAgent.

Integrasi RAG harus dibuktikan melalui execution path dan test.

## 6. V2

V2 menggunakan:

- `/v2`
- `app/v2/orchestrator.py`
- `app/v2/wiring.py`

V2 merupakan extension/orchestration layer di atas foundation V1.

V2 tidak boleh membuat duplicate implementation dari Core V1.

## 7. V2 → V1 ADAPTER

V2 dapat menggunakan komponen V1 melalui adapter.

Saat ini adapter yang teridentifikasi:

- V1 PolicyEngine
- V1 TrustEngine

Prinsip:

V2 → Adapter → V1 Component

bukan:

V2 → Duplicate Component

## 8. SINGLE SOURCE OF TRUTH

Tidak diperbolehkan membuat implementasi aktif kedua untuk tanggung jawab yang sama.

Contoh yang dilarang:

- HermesAgent + HermesAgentV2 yang menduplikasi Hermes
- PolicyEngine V1 + PolicyEngine V2-copy
- TrustEngine V1 + TrustEngine V2-copy
- konfigurasi aktif dengan dua sumber kebenaran

## 9. MEMORY

Memory merupakan extension/service layer.

Memory harus memiliki:

- session boundary
- retention policy
- storage policy
- governance
- security controls
- explicit write policy

Percakapan tidak boleh otomatis disimpan seluruhnya tanpa policy.

## 10. POLICY

Policy harus dipisahkan dari execution.

Policy bertanggung jawab terhadap keputusan seperti:

- ALLOW
- DENY
- REQUIRE REVIEW

V2 harus menggunakan PolicyEngine V1 atau adapter resmi jika fungsi tersebut sudah tersedia.

## 11. TRUST

Trust digunakan untuk menilai dukungan evidence terhadap claim.

Trust dapat menghasilkan:

- verification
- confidence
- evidence_count
- requires_human
- issues

Confidence bukan jaminan kebenaran fakta.

## 12. MCP DAN TOOLS

MCP dan Tools merupakan controlled capability layer.

Tool execution harus memiliki governance yang jelas, termasuk bila diperlukan:

- permission
- risk_level
- timeout
- audit_requirement

Arbitrary shell execution tidak boleh menjadi default capability.

Keberadaan module MCP/Tools tidak otomatis berarti sudah aktif pada `/v1/chat` atau `/v2/chat`.

## 13. OBSERVABILITY

Observability harus mempertahankan correlation/request ID untuk tracing.

Informasi minimal yang berguna:

- request_id
- session_id
- timestamp
- action
- result

## 14. AUDIT

Aktivitas berisiko harus dapat diaudit.

Audit tidak boleh menjadi jalur untuk mengubah Core secara langsung.

## 15. R&D

R&D menggunakan alur:

Events / Feedback
→ Failure Analysis
→ Gap Detection
→ Knowledge Discovery
→ Experiment
→ Improvement Proposal
→ Human Approval
→ Change Request
→ Test / Evaluation
→ Release Check
→ Manual Release

Tidak diperbolehkan:

R&D → automatic production modification

## 16. HUMAN APPROVAL

Perubahan yang memengaruhi:

- Core
- Policy
- Security
- Tools
- MCP
- Production knowledge
- database/schema
- production behavior
- release

harus melalui approval sesuai risk level.

## 17. ROLLBACK

Perubahan penting harus memiliki rollback strategy.

Jika perubahan gagal:

Change
→ Test FAIL
→ Rollback
→ kembali ke baseline yang aman

Rollback tidak boleh merusak baseline V1.

## 18. LEGACY / BACKUP

File backup atau legacy tidak otomatis merupakan runtime implementation.

Status harus dibedakan:

- ACTIVE
- ARCHIVED
- LEGACY
- BACKUP
- UNVERIFIED
- MISSING

Runtime source ditentukan berdasarkan dependency/import/execution evidence.

## 19. TESTING

Perubahan arsitektur harus diuji sesuai tingkat risikonya.

Minimum:

- Unit Test
- Integration Test
- API Test
- Regression Test
- Security Check

Keberadaan test tidak sama dengan test PASS.

## 20. VERIFIED ARCHITECTURE BASELINE

Arsitektur yang telah teridentifikasi:

NUSANTARA AI
|
+-- V1
|   +-- API `/v1`
|   |   +-- HermesAgent
|   |       +-- LanguageEngine
|   |       +-- ProblemEngine
|   |       +-- ReasoningEngine
|   |       +-- ModelRouter / Provider
|   |
|   +-- Knowledge / RAG services
|   +-- Workflow
|   +-- Handoff
|
+-- V2
    +-- API `/v2`
    +-- V2Orchestrator
        +-- LanguageEngine
        +-- Knowledge retrieval
        +-- V1 PolicyEngine via adapter
        +-- V1 TrustEngine via adapter
        +-- Model Provider
        +-- Audit
        +-- Recorder / Experience

## 21. CURRENT GAPS

Komponen berikut tidak boleh dianggap fully integrated hanya berdasarkan keberadaan source code:

- Memory
- MCP
- Tools
- Full RAG integration into Hermes
- Full V2 memory integration
- Full V2 MCP/tool execution
- Complete production R&D loop

Masing-masing harus diverifikasi melalui runtime evidence dan test.

## 22. CHANGE CONTROL

Setiap perubahan arsitektur harus mengikuti:

INSPECT
→ UNDERSTAND
→ MAP
→ RISK
→ PROPOSE
→ APPROVAL jika diperlukan
→ IMPLEMENT
→ TEST
→ SECURITY
→ REGRESSION
→ DOCUMENT
→ REPORT

## 23. ACCEPTANCE CRITERIA

Architecture Contract dianggap terpenuhi apabila:

- V1 Core dapat diidentifikasi.
- Hermes V1 tetap menjadi orchestrator V1.
- Tidak ada duplicate Core Engine.
- `/v1` tetap dipertahankan.
- V2 tidak menduplikasi Core V1.
- Adapter V2 → V1 digunakan bila diperlukan.
- Policy dipisahkan dari execution.
- Trust memiliki evidence boundary.
- Memory memiliki governance.
- MCP/Tools memiliki governance.
- R&D tidak dapat otomatis mengubah production.
- Human approval tersedia untuk perubahan berisiko.
- Regression test tersedia.
- Rollback tersedia.
- Dokumentasi sesuai runtime evidence.

## 24. ARCHITECTURAL DECISION

Keputusan dasar NUSANTARA AI:

1. V1 Core dipertahankan sebagai foundation.
2. Hermes V1 tidak diduplikasi.
3. V2 adalah extension/orchestration layer.
4. V2 boleh menggunakan komponen V1 melalui adapter/interface.
5. Tidak boleh ada duplicate source of truth.
6. `/v1` tidak diganti secara diam-diam oleh `/v2`.
7. R&D tidak memiliki jalur otomatis menuju production.
8. Human approval diperlukan untuk perubahan berisiko.
9. Dokumentasi harus mengikuti runtime evidence.
10. Perubahan penting harus memiliki rollback plan.

## 25. FINAL RULE

> NUSANTARA AI tidak berkembang dengan mengganti Core yang sudah bekerja, tetapi dengan memperkuat Core V1 dan menambahkan extension layer yang terkontrol.

> V1 adalah foundation. Hermes adalah orchestrator V1. V2 adalah orchestration dan governance extension. Tidak boleh ada Core kedua.

> AI boleh menemukan masalah dan mengusulkan perbaikan, tetapi perubahan terhadap sistem produksi tetap berada di bawah kontrol manusia.

---

**END OF NUSANTARA AI V1 ARCHITECTURE CONTRACT**
