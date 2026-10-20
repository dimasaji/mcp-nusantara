# R2 AUTHORIZATION CONTRACT

## Provider / Model Runtime Identity

**Document Class:** Master Engineering Authorization Contract
**Phase:** R2 — Provider / Model Runtime Identity
**Authorization Mode:** Human-Gated Engineering Authorization
**Execution Target:** Nusantara Core + Hermes
**Repository:** `C:\Users\dmaza\mcp-starter`
**Branch:** `codex/fullroot-control-20261007`
**Current Human Acceptance:** APPROVED
**Current Runtime Identity:** `NOT_VERIFIED`
**Current R2 Engineering Gate:** `CLOSED_PASS`
**R3 Engineering Evidence:** `14/14 PASS`

---

# 1. PURPOSE

Kontrak ini merupakan **otorisasi engineering eksplisit** untuk melakukan pekerjaan terbatas yang diperlukan guna memverifikasi dan/atau memperbaiki pembuktian:

> **Provider / Model Runtime Identity**

Kontrak ini TIDAK memberikan izin umum untuk melakukan refactor, redesign, cleanup, optimization, migration, atau perubahan arsitektur di luar scope R2.

Human Acceptance APPROVE merupakan hasil penerimaan manusia terhadap evidence dan Human Test.

**Human Acceptance APPROVE ≠ blanket engineering authorization.**

Engineering Agent wajib mematuhi seluruh batasan kontrak ini.

---

# 2. CURRENT VERIFIED BASELINE

Sebelum tindakan engineering apa pun, perlakukan kondisi berikut sebagai baseline:

```text
HIC-01 Human Acceptance       = APPROVED
Human Test                    = 8/8 PASS
R3 Evidence                   = 14/14 recorded PASS
R2 Engineering Gate           = CLOSED_PASS
Runtime Identity              = NOT_VERIFIED
Known Limitations             = 7
R2 Authorization              = THIS CONTRACT
```

Known limitations yang wajib tetap terlihat:

1. Git coverage PARTIAL karena sebagian inherited report directories inaccessible.
2. R3 RAG receipt adalah fixture, bukan production retrieval attestation.
3. Runtime identity bersifat historical; current live process/model `NOT_VERIFIED`.
4. R3 artifacts berada pada temporary storage; missing evidence tetap `NOT_VERIFIED`.
5. `data/knowledge/nusantara_knowledge.db-wal` = `NOT_VERIFIED`.
6. `data/knowledge/nusantara_knowledge.db-shm` = `NOT_VERIFIED`.
7. Live/current runtime identity tetap `NOT_VERIFIED`; live API atau historical receipt saja tidak cukup.

**Tidak satu pun limitation boleh dihapus, disamarkan, atau diubah menjadi PASS tanpa evidence yang sah.**

---

# 3. AUTHORIZATION OBJECTIVE

Engineering Agent hanya diizinkan untuk mencapai objective berikut:

> Membuktikan secara reproducible dan evidence-backed bahwa provider dan model yang benar-benar digunakan oleh live Nusantara Core + Hermes runtime dapat diidentifikasi secara deterministik.

Minimal identity yang harus dapat dibuktikan:

```text
Runtime Process
      ↓
Application
      ↓
Provider
      ↓
Model
      ↓
Model Version / Identifier
      ↓
Actual Runtime Request
```

Jika salah satu mata rantai belum dapat dibuktikan, hasil wajib:

```text
NOT_VERIFIED
```

Bukan:

```text
PASS
AVAILABLE
VERIFIED
AUTHORIZED
```

---

# 4. AUTHORIZED SCOPE

Engineering Agent BOLEH:

### 4.1 Inspect

* source code yang menentukan provider/model;
* configuration resolution;
* environment/configuration precedence;
* provider registry;
* model registry;
* composition root;
* runtime initialization;
* runtime health implementation;
* request dispatch;
* Ollama/provider integration;
* model selection;
* runtime metadata;
* existing R2 evidence;
* existing tests;
* existing logging/telemetry yang sudah tersedia.

### 4.2 Trace

Agent boleh membuat dependency/data-flow trace:

```text
Configuration
   ↓
Effective Configuration
   ↓
Provider Registry
   ↓
Model Registry
   ↓
Composition Root
   ↓
Runtime Initialization
   ↓
Request Dispatcher
   ↓
Actual Provider
   ↓
Actual Model
```

### 4.3 Implement minimal verification instrumentation

Agent boleh menambahkan atau memperbaiki mekanisme **read-only verification** yang diperlukan untuk membuktikan runtime identity.

Instrumentation harus:

* deterministic;
* local;
* auditable;
* reproducible;
* tidak mengubah business semantics;
* tidak mengubah authorization state;
* tidak mengubah R2/R3 result secara otomatis;
* tidak mengubah database knowledge;
* tidak melakukan self-approval.

### 4.4 Add/update tests

Agent boleh membuat atau memperbaiki test yang secara langsung menguji:

* provider resolution;
* model resolution;
* effective runtime identity;
* provider/model consistency;
* runtime identity mismatch;
* missing identity;
* stale/historical identity;
* live-vs-historical distinction.

### 4.5 Generate evidence

Agent boleh menghasilkan evidence R2 baru **hanya sebagai hasil verification yang benar-benar dilakukan**.

Evidence harus memiliki:

```text
timestamp
source
runtime identity
provider
model
verification method
result
hash / integrity identifier bila relevan
```

---

# 5. FORBIDDEN SCOPE

Agent DILARANG tanpa authorization tambahan:

### 5.1 Tidak boleh mengubah R3

Jangan mengubah:

```text
R3.1–R3.14
```

atau evidence yang telah dinyatakan PASS.

### 5.2 Tidak boleh memperbaiki WAL/SHM

DILARANG:

```text
repair WAL
repair SHM
recreate WAL
recreate SHM
delete WAL
delete SHM
rebuild database
vacuum database
migrate database
```

terhadap:

```text
data/knowledge/nusantara_knowledge.db-wal
data/knowledge/nusantara_knowledge.db-shm
```

kecuali terdapat authorization terpisah.

### 5.3 Tidak boleh mengubah knowledge database

Tidak boleh:

* insert;
* update;
* delete;
* rebuild;
* reindex;
* migrate;
* replace;

knowledge database sebagai bagian dari R2.

### 5.4 Tidak boleh mengubah governance state

Agent tidak boleh membuat endpoint atau mekanisme untuk:

```text
approve
authorize
promote
close
override
force-pass
```

R2/R3 secara otomatis.

### 5.5 Tidak boleh memalsukan runtime identity

DILARANG menggunakan:

```text
configured model = runtime model
historical receipt = live runtime
health endpoint = verified model
model inventory = live identity
```

sebagai pengganti live verification.

### 5.6 Tidak boleh melakukan broad refactor

DILARANG melakukan:

* unrelated cleanup;
* architecture rewrite;
* framework migration;
* dependency upgrade yang tidak diperlukan;
* frontend redesign;
* Control Plane redesign;
* unrelated performance optimization;
* renaming besar-besaran;
* formatting massal;
* repository cleanup.

### 5.7 Tidak boleh memperluas authorization

Jika agent menemukan masalah di luar R2:

```text
STOP
REPORT
DO NOT IMPLEMENT
```

---

# 6. CHANGE MINIMIZATION RULE

Gunakan prinsip:

> **Smallest Safe Change.**

Sebelum membuat perubahan:

1. identifikasi root cause;
2. identifikasi file yang benar-benar diperlukan;
3. tentukan perubahan minimum;
4. dokumentasikan alasan perubahan;
5. jangan menyentuh file di luar scope tanpa alasan teknis yang eksplisit.

Jika R2 dapat diverifikasi tanpa source modification, **jangan melakukan source modification**.

---

# 7. BASELINE CHECKPOINT

Sebelum implementation, Agent WAJIB mengumpulkan baseline.

Minimal:

```text
repository identity
branch
HEAD
worktree status
relevant source hashes
current R2 evidence
current R3 evidence
database hash
runtime status
provider inventory
model inventory
current runtime identity status
```

Baseline harus disimpan sebagai engineering evidence.

Agent tidak boleh melanjutkan implementation jika baseline tidak dapat diperoleh secara reliable.

---

# 8. RUNTIME IDENTITY CONTRACT

Runtime identity harus dibedakan menjadi:

### A. Configured Identity

Apa yang dikonfigurasikan.

```text
configured_provider
configured_model
```

### B. Resolved Identity

Apa yang dipilih oleh effective configuration.

```text
effective_provider
effective_model
```

### C. Live Identity

Apa yang benar-benar digunakan oleh running process.

```text
live_provider
live_model
```

### D. Historical Identity

Apa yang tercatat pada receipt/log sebelumnya.

```text
historical_provider
historical_model
```

**Keempat kategori tidak boleh diperlakukan sama.**

---

# 9. VERIFICATION REQUIREMENT

R2 dapat dinyatakan **LIVE VERIFIED** hanya jika evidence menunjukkan hubungan:

```text
running process
      +
actual request path
      +
actual provider
      +
actual model
```

dapat ditelusuri secara konsisten.

Minimal verification harus menjawab:

```text
WHO is serving?
WHICH PROVIDER?
WHICH MODEL?
FROM WHICH RUNNING PROCESS?
WHEN WAS IT VERIFIED?
HOW WAS IT VERIFIED?
```

---

# 10. NEGATIVE VERIFICATION

Agent WAJIB menguji kondisi kegagalan.

Minimal:

### Test R2-N01

Provider tidak tersedia.

Expected:

```text
NOT_VERIFIED / ERROR
```

bukan PASS.

### Test R2-N02

Model tidak tersedia.

Expected:

```text
NOT_VERIFIED / ERROR
```

### Test R2-N03

Configured model berbeda dengan live model.

Expected:

```text
MISMATCH
```

dan tidak boleh dipromosikan menjadi VERIFIED.

### Test R2-N04

Historical receipt tersedia tetapi live runtime tidak terbukti.

Expected:

```text
NOT_VERIFIED
```

### Test R2-N05

Model inventory tersedia tetapi actual request path tidak terbukti.

Expected:

```text
NOT_VERIFIED
```

---

# 11. EVIDENCE HIERARCHY

Prioritas evidence:

```text
LIVE RUNTIME EVIDENCE
        >
DIRECT PROVIDER RESPONSE
        >
EFFECTIVE CONFIGURATION
        >
MODEL/PROVIDER REGISTRY
        >
HISTORICAL RECEIPT
        >
STATIC SOURCE CLAIM
```

Evidence tingkat rendah tidak boleh digunakan untuk mengklaim hasil tingkat tinggi.

Contoh:

```text
Ollama model exists
```

tidak membuktikan:

```text
Nusantara runtime is currently using that model.
```

---

# 12. CONTROL PLANE BOUNDARY

Control Plane tetap:

```text
READ-ONLY ENGINEERING EVIDENCE
+
HUMAN TEST
+
HUMAN REVIEW
+
HUMAN DECISION
```

Control Plane TIDAK boleh menjadi:

```text
runtime repair console
database repair console
authorization bypass
production deployment console
```

Human Acceptance result tetap terpisah dari engineering evidence.

---

# 13. HUMAN DECISION BOUNDARY

Human APPROVE yang telah diberikan pada HIC-01 berarti:

```text
Human Acceptance = APPROVED
```

dan tidak boleh ditafsirkan sebagai:

```text
R2 Runtime Identity = VERIFIED
Production = AUTHORIZED
Deployment = AUTHORIZED
Database repair = AUTHORIZED
R3 evidence = modified
```

Semua itu memerlukan evidence/authorization tersendiri.

---

# 14. HARD STOP CONDITIONS

Agent WAJIB berhenti jika:

1. Runtime identity tidak dapat dibuktikan.
2. Provider/model mismatch ditemukan.
3. Evidence contradicted.
4. Existing R2/R3 evidence harus diubah untuk membuat test PASS.
5. WAL/SHM harus disentuh.
6. Knowledge database harus dimodifikasi.
7. Governance state harus dimutasi.
8. Scope perubahan tidak jelas.
9. Perubahan membutuhkan authorization baru.
10. Test gagal dan root cause belum jelas.
11. Agent perlu melakukan broad refactor.
12. Existing protected evidence harus dihapus.
13. Agent menemukan bahwa current runtime berbeda dari expected runtime.
14. Verification hanya dapat dilakukan menggunakan historical evidence.

Dalam kondisi tersebut:

```text
STOP
DO NOT PATCH AROUND THE RESULT
DO NOT FORCE PASS
REPORT FINDING
REQUEST NEW AUTHORIZATION IF NEEDED
```

---

# 15. ACCEPTANCE CRITERIA

R2 implementation hanya dapat diajukan sebagai **VERIFIED** jika seluruh kondisi berikut terpenuhi:

```text
[ ] Baseline captured
[ ] Provider resolved deterministically
[ ] Model resolved deterministically
[ ] Live runtime identified
[ ] Actual request path traced
[ ] Live provider confirmed
[ ] Live model confirmed
[ ] Runtime timestamp recorded
[ ] Positive verification passed
[ ] Negative tests passed
[ ] Mismatch test passed
[ ] Historical receipt correctly separated
[ ] No R3 evidence modified
[ ] No WAL/SHM modified
[ ] No knowledge DB modified
[ ] No governance state modified
[ ] No unauthorized scope expansion
[ ] Regression tests pass
[ ] Evidence integrity verified
[ ] Human review remains separate
```

Jika salah satu mandatory criterion gagal:

```text
R2 = NOT_VERIFIED
```

---

# 16. REQUIRED TEST MATRIX

Agent wajib menghasilkan minimal:

| ID     | Test                        | Expected      |
| ------ | --------------------------- | ------------- |
| R2-T01 | Resolve configured provider | PASS          |
| R2-T02 | Resolve configured model    | PASS          |
| R2-T03 | Resolve effective provider  | PASS          |
| R2-T04 | Resolve effective model     | PASS          |
| R2-T05 | Identify live process       | PASS          |
| R2-T06 | Verify live provider        | PASS          |
| R2-T07 | Verify live model           | PASS          |
| R2-T08 | Trace actual request        | PASS          |
| R2-T09 | Historical-only evidence    | NOT_VERIFIED  |
| R2-T10 | Inventory-only evidence     | NOT_VERIFIED  |
| R2-T11 | Provider mismatch           | FAIL/MISMATCH |
| R2-T12 | Model mismatch              | FAIL/MISMATCH |
| R2-T13 | Missing provider            | NOT_VERIFIED  |
| R2-T14 | Missing model               | NOT_VERIFIED  |
| R2-T15 | Regression suite            | PASS          |

Tidak boleh menghapus negative tests hanya karena menghasilkan FAIL/MISMATCH secara expected.

---

# 17. EVIDENCE RECEIPT CONTRACT

Setiap verification receipt minimal memiliki:

```json
{
  "phase": "R2",
  "gate": "Provider / Model Runtime Identity",
  "verification_type": "LIVE_RUNTIME",
  "timestamp": "<UTC timestamp>",
  "process": "<identified process>",
  "provider": "<actual provider>",
  "model": "<actual model>",
  "request_path": "<verified request path>",
  "result": "VERIFIED|NOT_VERIFIED|MISMATCH",
  "source": "<evidence source>",
  "integrity": {
    "sha256": "<hash>"
  }
}
```

Receipt tidak boleh dibuat dengan nilai yang ditebak.

---

# 18. REPORTING CONTRACT

Setelah implementation/testing selesai, Agent WAJIB melaporkan:

```text
R2 AUTHORIZATION EXECUTION REPORT

Authorization:
Scope:
Baseline:
Changes:
Files Changed:
Files Unchanged:
Tests:
Positive Verification:
Negative Verification:
Live Provider:
Live Model:
Historical Identity:
Evidence:
Integrity:
R3 Impact:
Database Impact:
WAL/SHM Impact:
Governance Impact:
Regression:
Remaining Limitations:
Final R2 Status:
```

---

# 19. STATUS SEMANTICS

Gunakan status secara ketat:

### VERIFIED

Hanya jika live runtime identity benar-benar terbukti.

### NOT_VERIFIED

Jika evidence belum cukup.

### MISMATCH

Jika configured/effective/live identity berbeda secara material.

### ERROR

Jika verification gagal karena runtime/provider failure.

### BLOCKED

Jika verification memerlukan authorization atau dependency di luar scope.

**Jangan menggunakan PASS sebagai sinonim VERIFIED.**

---

# 20. R2 CLOSURE RULE

R2 tidak boleh ditutup hanya karena:

```text
tests passed
```

R2 hanya dapat ditutup setelah:

```text
implementation
      ↓
verification
      ↓
evidence
      ↓
integrity check
      ↓
human review
      ↓
explicit authorization
      ↓
closure
```

---

# 21. NO SELF-AUTHORIZATION

Engineering Agent tidak memiliki kewenangan untuk mengotorisasi hasil pekerjaannya sendiri.

Agent hanya boleh menghasilkan:

```text
FINDING
EVIDENCE
TEST RESULT
IMPLEMENTATION RESULT
RECOMMENDATION
```

Keputusan final authorization tetap berada pada manusia yang berwenang.

---

# 22. FINAL GOVERNANCE RULE

Jika terdapat konflik antara:

```text
desired outcome
```

dan:

```text
evidence
```

maka:

> **EVIDENCE WINS.**

Jika evidence menunjukkan:

```text
NOT_VERIFIED
```

maka Agent WAJIB mempertahankan:

```text
NOT_VERIFIED
```

sampai evidence baru yang valid membuktikan sebaliknya.

---

# 23. MASTER EXECUTION DIRECTIVE

## Instruksi kepada Web Developer / ChatGPT Coding Agent

```text
You are operating under the R2 Authorization Contract.

DO NOT begin implementation until you have inspected and reported the current baseline.

Your authorization is limited strictly to Provider / Model Runtime Identity verification.

You may inspect configuration, provider/model resolution, composition root,
runtime initialization, request dispatch, provider integration, runtime identity,
tests, and existing evidence.

You may implement only the minimum changes required to establish deterministic,
reproducible, evidence-backed LIVE runtime identity verification.

Do not modify R3 evidence.
Do not modify the knowledge database.
Do not repair, recreate, delete, or modify WAL/SHM.
Do not alter governance state.
Do not create authorization bypasses.
Do not add automatic approval.
Do not convert NOT_VERIFIED into PASS without valid evidence.
Do not treat model inventory, configuration, health endpoint, or historical
receipts as proof of live runtime identity.

First perform READ-ONLY DISCOVERY.

Then produce:

1. baseline;
2. runtime identity trace;
3. gap/root-cause analysis;
4. minimum-change proposal;
5. affected files;
6. protected files;
7. test plan.

STOP and request confirmation if the proposed implementation exceeds this
authorization contract.

After authorized implementation:

1. run positive tests;
2. run negative tests;
3. test provider mismatch;
4. test model mismatch;
5. test historical-only evidence;
6. test inventory-only evidence;
7. verify regression suite;
8. verify R3 unchanged;
9. verify database unchanged;
10. verify WAL/SHM unchanged;
11. generate R2 evidence receipt;
12. generate final execution report.

Never self-authorize.

Never hide limitations.

If live runtime identity cannot be proven, final status MUST remain NOT_VERIFIED.

Evidence takes precedence over the desired outcome.

HARD STOP on any scope violation.
```

---

# 24. AUTHORIZATION STATE

```text
┌──────────────────────────────────────────────┐
│ R2 AUTHORIZATION CONTRACT                    │
├──────────────────────────────────────────────┤
│ Human Acceptance       APPROVED              │
│ Engineering R2         CLOSED_PASS           │
│ R3                     14/14 PASS             │
│ Runtime Identity       NOT_VERIFIED          │
│ Authorization Scope    R2 ONLY               │
│ Database Mutation      FORBIDDEN             │
│ WAL/SHM Mutation       FORBIDDEN             │
│ R3 Mutation             FORBIDDEN             │
│ Governance Mutation     FORBIDDEN             │
│ Self-Authorization      FORBIDDEN             │
└──────────────────────────────────────────────┘
```

**END OF R2 AUTHORIZATION CONTRACT**
