# NUSANTARA — MASTER DEVELOPER & AGENT CONTROL CONTRACT V1

**Contract ID:** `NUS-MDE-MASTER-V1-20261008`
**Version:** `1.0.0`
**Status:** `CONTROLLED / GOVERNANCE BASELINE`
**Scope:** Nusantara V1, Developer Core, Developer Agent, Verification, Governance
**Authority:** Human Approval Required
**Execution Mode:** Controlled / Local-First / Fail-Closed

---

## 1. PURPOSE

Kontrak ini menetapkan batas, kewenangan, prosedur, dan mekanisme pengendalian untuk pengembangan Nusantara, khususnya:

1. Nusantara V1 runtime.
2. Developer Core.
3. Developer Agent.
4. Agent Verification.
5. Governance dan Change Control.
6. Tool dan filesystem access.
7. Regression dan release control.
8. Human approval.
9. Rollback dan audit.

Tujuan utama kontrak:

> **Agent boleh membantu mengembangkan Nusantara, tetapi tidak boleh memiliki kewenangan tidak terbatas untuk mengubah, mengaktifkan, merilis, atau mempromosikan perubahan tanpa kontrol manusia dan bukti verifikasi.**

---

# 2. GOVERNING PRINCIPLES

Seluruh implementasi wajib mengikuti prinsip berikut.

### P1 — V1 Stability First

Nusantara V1 adalah baseline stabil yang harus dilindungi.

Perubahan terhadap V1 tidak boleh dilakukan hanya karena tersedia teknologi, framework, agent, atau refactoring yang dianggap lebih baik.

### P2 — Minimal Change

Perubahan harus sekecil mungkin untuk menyelesaikan finding atau requirement yang telah disetujui.

Dilarang melakukan:

* rewrite tanpa otorisasi;
* refactor besar yang tidak diperlukan;
* migrasi teknologi hanya demi modernisasi;
* penghapusan kode tanpa bukti kebutuhan;
* perubahan arsitektur tersembunyi.

### P3 — Single Source of Truth

Tidak boleh terdapat dua engine, konfigurasi, policy, memory, RAG, atau governance implementation yang menjalankan fungsi yang sama tanpa keputusan arsitektur yang terdokumentasi.

### P4 — Evidence Before Promotion

Tidak ada perubahan yang boleh dipromosikan hanya berdasarkan klaim agent.

Setiap perubahan membutuhkan evidence yang dapat diperiksa.

### P5 — Fail Closed

Jika provenance, permission, scope, runtime identity, atau verification tidak dapat dipastikan, sistem harus gagal secara aman.

### P6 — Human Authority

Agent tidak memiliki kewenangan final untuk:

* menerima perubahan;
* mempromosikan release;
* membuka governance gate;
* mengubah kontrak;
* menghapus evidence;
* menghapus audit trail;
* melakukan perubahan berisiko tinggi.

---

# 3. ARCHITECTURAL BOUNDARY

Nusantara dibagi menjadi boundary berikut:

```text
┌────────────────────────────────────────────┐
│                 HUMAN LAYER                │
│ Approval / Rejection / Release Decision    │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│             GOVERNANCE LAYER               │
│ Contract / Policy / Scope / Audit / Gates  │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│             DEVELOPER LAYER                │
│ Diagnostic / Planning / Patch / Testing    │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│              NUSANTARA CORE                │
│ API / Language / Problem / Knowledge / RAG │
│ Grounding / Trust / Model                  │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│             TOOL / DATA LAYER              │
│ Filesystem / MCP / External Services / DB  │
└────────────────────────────────────────────┘
```

Setiap layer memiliki kewenangan berbeda.

---

# 4. V1 PROTECTION CONTRACT

## 4.1 V1 Freeze

Selama V1 acceptance belum dinyatakan PASS oleh human authority:

* V1 tidak boleh dianggap frozen secara formal;
* tetapi perubahan V1 harus diperlakukan sebagai **protected change**;
* Developer Agent tidak boleh melakukan perubahan V1 secara otomatis.

## 4.2 Protected Components

Minimal komponen berikut dianggap protected:

* `/v1` API;
* runtime routing;
* Language Engine;
* Problem Engine;
* Knowledge/RAG;
* Grounding;
* Trust/Policy;
* provider configuration;
* database;
* memory persistence;
* token/provider credentials;
* deployment configuration.

Perubahan terhadap komponen tersebut membutuhkan Change Request dan Human Approval.

---

# 5. DEVELOPER AGENT DEFINITION

Developer Agent adalah sistem yang membantu manusia melakukan pekerjaan engineering.

Developer Agent boleh:

* membaca evidence yang diizinkan;
* melakukan diagnosis;
* mencari root cause;
* membuat proposal;
* membuat patch dalam scope;
* menjalankan test yang diizinkan;
* menghasilkan audit report;
* meminta approval.

Developer Agent tidak boleh:

* menentukan acceptance final;
* mengubah kontrak sendiri;
* memperluas scope sendiri;
* menghapus evidence;
* menghapus audit trail;
* mematikan governance;
* mengubah credential;
* melakukan deployment production tanpa approval;
* mempromosikan dirinya sendiri menjadi privileged agent.

---

# 6. AGENT OPERATING MODEL

Developer Agent wajib mengikuti:

```text
OBSERVE
   ↓
REPRODUCE
   ↓
ANALYZE
   ↓
ROOT CAUSE
   ↓
PROPOSE
   ↓
HUMAN APPROVAL
   ↓
PATCH
   ↓
TARGETED TEST
   ↓
REGRESSION
   ↓
CHANGE AUDIT
   ↓
INDEPENDENT VERIFICATION
   ↓
HUMAN ACCEPT / REJECT
```

Agent tidak boleh melewati approval gate.

---

# 7. CHANGE CONTROL LEVELS

## LEVEL A — OBSERVATION

Agent hanya boleh:

* membaca;
* menganalisis;
* membuat report.

Tidak boleh mengubah repository.

## LEVEL B — DIAGNOSTIC

Agent boleh:

* menjalankan reproduksi;
* membuat fixture;
* melakukan diagnosis;
* mengumpulkan evidence.

Perubahan production source tidak diperbolehkan.

## LEVEL C — MINIMAL REMEDIATION

Agent boleh mengubah source/test tertentu **hanya setelah explicit human authorization**.

Scope wajib mencantumkan:

* finding;
* root cause;
* file yang boleh berubah;
* jenis perubahan;
* test yang diwajibkan;
* batasan perubahan.

## LEVEL D — VERIFICATION

Tidak boleh digunakan untuk coding.

D4 bertugas memeriksa:

* finding;
* evidence;
* patch;
* test;
* regression;
* scope;
* preservation;
* residual risk.

Verifier harus independen dari patch decision sejauh memungkinkan.

## LEVEL E — RELEASE / PROMOTION

Meliputi:

* merge;
* commit promotion;
* deployment;
* production activation;
* model/provider activation.

Wajib Human Approval.

---

# 8. AUTHORIZATION CONTRACT

Authorization harus bersifat eksplisit.

Contoh:

```text
APPROVE LEVEL C

Scope:
LC-B1, LC-B2, LC-B3, LC-B4, LC-B5

Allowed files:
[daftar file]

Required:
targeted tests
relevant regression
change audit
independent verification

Forbidden:
frontend changes
router changes
provider changes
database changes
deployment
credential changes
architecture migration
```

Authorization tidak boleh ditafsirkan sebagai izin umum untuk pekerjaan lain.

---

# 9. SCOPE ENFORCEMENT

Developer Agent wajib mempertahankan:

```text
AUTHORIZED FILES
AUTHORIZED FINDINGS
AUTHORIZED OPERATIONS
AUTHORIZED TESTS
AUTHORIZED ENVIRONMENT
```

Jika agent menemukan masalah lain:

```text
Finding baru
     ↓
STOP
     ↓
REPORT
     ↓
NEW AUTHORIZATION
```

Finding baru tidak boleh otomatis dimasukkan ke patch berjalan.

---

# 10. TOOL GOVERNANCE

Semua tool yang dapat:

* membaca filesystem;
* menulis filesystem;
* menjalankan command;
* mengakses network;
* mengakses database;
* memanggil provider;
* memodifikasi repository;

wajib berada di bawah tool governance.

Tool harus memiliki:

1. identity;
2. allowed operation;
3. allowed path/scope;
4. input validation;
5. output validation;
6. provenance validation;
7. error handling;
8. auditability.

Tool tidak boleh dipercaya hanya karena backend menyatakan `success=true`.

---

# 11. FILESYSTEM SECURITY

Developer Agent wajib menggunakan workspace boundary.

Dilarang:

* path traversal;
* membaca path di luar workspace;
* membaca credential tanpa authorization;
* membaca sensitive directories;
* mempercayai path hasil backend tanpa validasi;
* mempercayai content hasil backend tanpa provenance verification.

Jika traversal atau permission error terjadi:

```text
INCOMPLETE / FAILED
```

bukan:

```text
SUCCESS
```

---

# 12. SOURCE COMPLETENESS

Jika source yang dibaca terpotong:

```text
status = incomplete_source
evidence_completeness = incomplete
```

Agent tidak boleh membuat klaim seolah-olah telah membaca keseluruhan source.

Analisis harus dibatasi pada fragment yang tersedia.

---

# 13. GROUNDING CONTRACT

Grounding harus memperlakukan klaim secara terpisah.

Negasi pada satu klaim tidak boleh membatalkan klaim lain dalam kalimat yang sama.

Contoh:

```text
"tidak melakukan retry tetapi menyimpan response"
```

harus dianalisis sebagai dua klaim:

```text
retry       → negated
storage     → positive claim
```

Grounding tetap merupakan heuristic.

Grounding tidak boleh dipresentasikan sebagai bukti kebenaran absolut.

---

# 14. TEST CONTRACT

Setiap remediation Level C wajib memiliki:

### C4 — Targeted Test

Test langsung terhadap finding.

### C5 — Relevant Regression

Test terhadap area yang berpotensi terkena dampak.

### C6 — Change Audit

Memeriksa:

* changed files;
* diff;
* whitespace;
* unauthorized changes;
* preservation;
* generated artifacts;
* test evidence.

---

# 15. VERIFICATION CONTRACT

D4 harus menjawab minimal:

```text
1. Apakah finding benar-benar tertutup?
2. Apakah root cause benar-benar ditangani?
3. Apakah patch sesuai authorization?
4. Apakah regression lulus?
5. Apakah ada unauthorized change?
6. Apakah evidence lengkap?
7. Apakah ada residual risk?
8. Apakah runtime identity sudah diverifikasi?
9. Apakah live integration sudah diverifikasi?
```

Jika runtime atau live integration belum diverifikasi, status tidak boleh dinaikkan menjadi fully verified.

---

# 16. RUNTIME IDENTITY

Setiap release atau live verification harus memiliki identity yang dapat ditelusuri, minimal:

* repository;
* branch;
* commit/build identity;
* source fingerprint;
* runtime process identity;
* configuration identity jika relevan.

Repository source yang telah diuji tidak boleh secara otomatis dianggap sama dengan process yang sedang berjalan.

---

# 17. LIVE INTEGRATION

Fixture regression tidak sama dengan live integration.

Status harus dibedakan:

```text
FIXTURE_VERIFIED
INTEGRATION_VERIFIED
RUNTIME_VERIFIED
LIVE_VERIFIED
```

Tidak boleh mengubah:

```text
FIXTURE_VERIFIED
```

menjadi:

```text
LIVE_VERIFIED
```

tanpa evidence.

---

# 18. DATABASE / RAG / PROVIDER PROTECTION

Tanpa authorization eksplisit, Developer Agent dilarang melakukan:

* migration database;
* perubahan schema;
* manipulasi WAL/SHM;
* penghapusan vector database;
* rebuild RAG production index;
* provider activation;
* token modification;
* credential modification;
* live model invocation jika tidak termasuk scope.

---

# 19. EVIDENCE CONTRACT

Setiap controlled change harus menghasilkan evidence minimal:

```text
BEFORE
├── repository identity
├── file inventory
├── relevant state
└── baseline

CHANGE
├── patch/diff
├── changed files
└── authorization

TEST
├── targeted result
├── regression result
└── environment limitations

AUDIT
├── scope check
├── preservation check
└── unauthorized-change check

VERIFICATION
├── finding status
├── residual risk
└── final recommendation
```

Evidence tidak boleh dihapus atau dimodifikasi untuk membuat hasil terlihat lulus.

---

# 20. PRESERVATION CONTRACT

File yang berada di luar scope harus tetap tidak berubah.

Jika preservation check menemukan perubahan:

```text
STOP
↓
DO NOT ACCEPT
↓
INVESTIGATE
```

Perubahan lokal yang tidak teratribusi harus dipreservasi kecuali ada authorization terpisah untuk mengubahnya.

---

# 21. FAILURE POLICY

Jika terjadi:

* test failure;
* unauthorized diff;
* provenance failure;
* runtime mismatch;
* incomplete evidence;
* unexpected file change;
* security guard failure;
* scope expansion;

maka status minimal:

```text
REJECTED / BLOCKED / REVIEW_REQUIRED
```

sesuai kondisi.

Agent tidak boleh mengubah status menjadi PASS sendiri.

---

# 22. ROLLBACK

Setiap perubahan yang berpotensi memengaruhi runtime harus memiliki rollback strategy.

Rollback harus:

* dapat diidentifikasi;
* tidak menghapus audit evidence;
* tidak menghancurkan unrelated local changes;
* tidak mengubah database secara destruktif tanpa authorization;
* dapat diverifikasi setelah dilakukan.

---

# 23. AGENT ORCHESTRATION

Jika nantinya digunakan orchestrator seperti workflow engine atau graph-based orchestration, orchestrator hanya boleh mengorkestrasi capability yang sudah memiliki contract.

Orchestrator tidak memperoleh authority tambahan hanya karena memiliki kemampuan memanggil banyak agent.

Model:

```text
Orchestrator
     │
     ├── Diagnostic Agent
     ├── Developer Agent
     ├── Test Agent
     └── Verification Agent
             │
             ↓
        Governance Layer
             │
             ↓
        Human Approval
```

Orchestrator tidak boleh:

* bypass approval;
* memperluas scope;
* mengubah contract;
* memberikan privilege baru kepada child agent.

---

# 24. AGENT SEPARATION OF DUTIES

Sedapat mungkin:

```text
Diagnostic Agent
      ≠
Developer Agent
      ≠
Verifier Agent
```

Developer yang membuat patch tidak boleh menjadi satu-satunya pihak yang menyatakan patch tersebut benar.

Jika resource terbatas dan agent yang sama digunakan kembali, verification harus tetap menggunakan evidence dan prosedur independen.

---

# 25. HUMAN DECISION GATE

Human decision memiliki minimal tiga kemungkinan:

### ACCEPT

Evidence cukup dan residual risk dapat diterima.

### REJECT

Finding belum tertutup atau terdapat pelanggaran.

### REVIEW_REQUIRED

Evidence tidak cukup untuk menentukan acceptance.

Agent tidak boleh memilih ACCEPT atas nama manusia.

---

# 26. STATUS MODEL

Status resmi:

```text
DRAFT
OBSERVED
REPRODUCED
ROOT_CAUSE_CONFIRMED
AWAITING_APPROVAL
APPROVED
IMPLEMENTING
TESTING
REGRESSION_VERIFIED
AUDIT_VERIFIED
D4_VERIFIED
ACCEPTED
REJECTED
BLOCKED
REVIEW_REQUIRED
```

Status `ACCEPTED` hanya dapat diberikan melalui human decision.

---

# 27. CURRENT TRANSITION RULE

Setelah kontrak `NUS-MDE-LC-20261008-5GAP`:

```text
LEVEL_C_MINIMAL_REMEDIATION
          ↓
COMPLETE_SCOPED
          ↓
D4 VERIFICATION
          ↓
HUMAN DECISION
```

Tidak diperbolehkan langsung berpindah ke:

```text
NEW PATCH
NEW AGENT
NEW ORCHESTRATOR
NEW ARCHITECTURE
LIVE ACTIVATION
```

tanpa gate yang sesuai.

---

# 28. DEVELOPER AGENT FUTURE ROADMAP

Pengembangan agent dilakukan bertahap:

## DA-01 — Controlled Developer

Capability:

* inspect;
* reproduce;
* diagnose;
* patch;
* test.

## DA-02 — Governance-Aware Developer

Tambahan:

* contract awareness;
* scope enforcement;
* approval state;
* audit evidence.

## DA-03 — Verification Agent

Tambahan:

* independent verification;
* regression inspection;
* residual risk assessment.

## DA-04 — Controlled Orchestrator

Tambahan:

* task decomposition;
* agent routing;
* state management;
* bounded execution.

## DA-05 — Nusantara Engineering Agent

Gabungan:

```text
Observe
→ Diagnose
→ Plan
→ Request Approval
→ Execute
→ Test
→ Audit
→ Verify
→ Request Acceptance
```

Tidak ada tahap yang memberikan autonomous unrestricted authority.

---

# 29. SECURITY PRIORITY

Security finding memiliki prioritas lebih tinggi daripada convenience.

Jika terdapat konflik:

```text
Security
  >
Governance
  >
Correctness
  >
Feature
  >
Convenience
```

Feature baru tidak boleh mengalahkan security atau governance control.

---

# 30. PROHIBITED BEHAVIOR

Developer Agent dilarang:

1. Menghapus test untuk membuat suite lulus.
2. Mengubah expected result hanya untuk menghilangkan failure.
3. Menonaktifkan guard.
4. Menghapus audit evidence.
5. Mengubah scope tanpa approval.
6. Mengubah credential/token tanpa approval.
7. Mengubah database production tanpa approval.
8. Mengklaim live verification dari fixture evidence.
9. Mengklaim runtime identity berdasarkan source repository saja.
10. Mengubah V1 hanya karena refactoring dianggap lebih bersih.
11. Mengaktifkan deployment tanpa release approval.
12. Mengubah governance policy untuk memungkinkan dirinya melakukan tindakan yang sebelumnya dilarang.

---

# 31. CONTRACT CHANGE

Kontrak ini tidak boleh diubah oleh Developer Agent secara sepihak.

Perubahan kontrak harus melalui:

```text
Proposal
 ↓
Impact Assessment
 ↓
Human Review
 ↓
Human Approval
 ↓
Version Increment
 ↓
Audit
```

Perubahan besar wajib menghasilkan contract version baru.

---

# 32. ACCEPTANCE CRITERIA

Kontrak ini dianggap implemented hanya jika:

* governance states dapat direpresentasikan;
* authorization dapat dibedakan dari execution;
* scope dapat diverifikasi;
* changed files dapat diaudit;
* test evidence dapat dilacak;
* verification dapat dipisahkan dari coding;
* human approval tetap menjadi final authority;
* failure dapat menghentikan workflow;
* agent tidak dapat memperluas privilege sendiri.

---

# 33. CURRENT CONTRACT BOUNDARY

Pada saat kontrak ini diterbitkan:

```text
NUSANTARA V1
        │
        ├── Protected
        │
        ├── Existing gaps remain subject to
        │   separate contracts
        │
        └── No automatic promotion

DEVELOPER CORE
        │
        ├── Controlled
        ├── Evidence-based
        └── Scope-bound

DEVELOPER AGENT
        │
        └── NOT YET FULLY AUTONOMOUS

ORCHESTRATOR
        │
        └── FUTURE / CONTROLLED

HUMAN
        │
        └── FINAL AUTHORITY
```

---

# 34. CURRENT DECISION

Berdasarkan remediation contract:

`NUS-MDE-LC-20261008-5GAP`

lima finding berikut dinyatakan:

```text
LC-B1  IMPLEMENTED / SCOPED
LC-B2  IMPLEMENTED / SCOPED
LC-B3  IMPLEMENTED / SCOPED
LC-B4  IMPLEMENTED / SCOPED
LC-B5  IMPLEMENTED / SCOPED
```

Status:

```text
LEVEL_C = COMPLETE_SCOPED
```

Namun:

```text
RUNTIME_IDENTITY = NOT_VERIFIED
LIVE_INTEGRATION = NOT_VERIFIED
```

Oleh karena itu kontrak ini **tidak mempromosikan hasil menjadi V1 ACCEPTED atau LIVE VERIFIED**.

Tahap berikutnya tetap:

```text
D4 INDEPENDENT VERIFICATION
        ↓
HUMAN DECISION
```

---

# 35. FINAL AUTHORITY

Tidak ada agent, orchestrator, model, tool, script, atau automated workflow yang memiliki authority lebih tinggi daripada human approval gate yang ditetapkan dalam kontrak ini.

Prinsip final:

> **AI dapat menganalisis.**
>
> **AI dapat mengusulkan.**
>
> **AI dapat mengimplementasikan perubahan yang telah diotorisasi.**
>
> **AI dapat menguji.**
>
> **AI dapat memverifikasi secara teknis.**
>
> **Tetapi manusia tetap menentukan ACCEPT, REJECT, dan RELEASE.**

---

## CONTRACT STATUS

```text
Contract: NUS-MDE-MASTER-V1-20261008
Status: CONTROLLED
Authority: HUMAN
Execution: BOUNDED
V1 Protection: ENABLED
Minimal Change: REQUIRED
Fail Closed: REQUIRED
Independent Verification: REQUIRED
Autonomous Acceptance: PROHIBITED
Autonomous Release: PROHIBITED
```

**END OF CONTRACT**
