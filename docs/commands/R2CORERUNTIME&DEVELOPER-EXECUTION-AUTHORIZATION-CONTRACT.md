# NUSANTARA

# R2 CORE RUNTIME & DEVELOPER EXECUTION AUTHORIZATION CONTRACT

**Document Class:** Master Engineering Authorization Contract
**Phase:** R2 — Provider / Model Runtime Identity
**Authorization Model:** Human-Gated, Evidence-Driven, Non-Self-Authorizing
**Execution Target:** Nusantara Core + Hermes Runtime
**Developer Engine:** Nusantara Developer Engine / Engineering Agent
**Governance Surface:** Nusantara Control Plane
**Repository:** `C:\Users\dmaza\mcp-starter`
**Branch:** `codex/fullroot-control-20261007`

---

# 0. CONTRACT STATUS

```text
HIC-01 Human Acceptance       = APPROVED
Human Test                    = 8/8 PASS
R3 Evidence                   = 14/14 recorded PASS
R2 Engineering Gate           = CLOSED_PASS
Runtime Identity              = NOT_VERIFIED

R2 Authorization              = ACTIVE FOR R2 SCOPE ONLY
R2 Runtime Verification       = NOT_YET_VERIFIED

Control Plane Mutation        = FORBIDDEN
R3 Mutation                   = FORBIDDEN
Knowledge DB Mutation         = FORBIDDEN
WAL/SHM Mutation              = FORBIDDEN
Self-Authorization            = FORBIDDEN
```

`CLOSED_PASS` pada R2 Engineering Gate **tidak berarti** Runtime Identity sudah `VERIFIED`.

---

# 1. PURPOSE

Kontrak ini memberikan authorization engineering terbatas untuk:

> melakukan discovery, minimal implementation, testing, dan evidence generation yang diperlukan untuk membuktikan Provider / Model Runtime Identity Nusantara secara live, deterministic, reproducible, dan evidence-backed.

Kontrak ini **tidak** memberikan authorization umum untuk:

* redesign;
* refactor;
* cleanup;
* migration;
* optimization;
* database repair;
* governance mutation;
* R3 modification;
* production authorization;
* deployment authorization.

---

# 2. FUNDAMENTAL ARCHITECTURE BOUNDARY

Nusantara wajib diperlakukan sebagai tiga subsystem yang berbeda:

```text
┌─────────────────────────────────────────────┐
│              NUSANTARA PLATFORM             │
├─────────────────┬───────────────┬───────────┤
│ CORE RUNTIME    │ DEVELOPER     │ CONTROL   │
│                 │ ENGINE        │ PLANE     │
├─────────────────┼───────────────┼───────────┤
│ execute        │ inspect       │ govern    │
│ provider       │ analyze       │ evidence  │
│ model          │ test          │ review    │
│ request        │ implement     │ decision  │
│ RAG            │ report        │ acceptance│
└─────────────────┴───────────────┴───────────┘
```

Ketiga subsystem **tidak boleh dianggap sebagai satu authority**.

---

# 3. CORE RUNTIME

Nusantara Core Runtime adalah execution subsystem.

Core Runtime bertanggung jawab atas:

```text
configuration
effective configuration
provider resolution
model resolution
runtime initialization
request dispatch
provider invocation
model invocation
response generation
```

Core Runtime **tidak menentukan authorization governance**.

---

# 4. DEVELOPER ENGINE

Developer Engine adalah engineering execution mechanism.

Developer Engine BOLEH:

```text
inspect
analyze
trace
test
implement authorized changes
generate evidence
generate reports
```

Developer Engine TIDAK BOLEH:

```text
approve
authorize
self-authorize
force-pass
override human decision
modify governance state
declare VERIFIED solely from its own assertion
delete contradictory evidence
suppress limitations
```

Prinsip:

> **Developer Engine executes authorization. It does not create authorization.**

---

# 5. CONTROL PLANE

Control Plane merupakan governance and human acceptance surface.

Control Plane dapat:

```text
display evidence
display runtime status
run human tests
collect human review
collect human decision
```

Control Plane tidak boleh menjadi:

```text
runtime repair console
database repair console
R2 authorization bypass
automatic approval mechanism
production deployment console
```

Human Decision tetap berbeda dari engineering verification.

---

# 6. AUTHORITY HIERARCHY

Authority berlaku sebagai berikut:

```text
Human Authority
      ↓
Authorization Contract
      ↓
Developer Engine
      ↓
Core Runtime
```

Tidak boleh terjadi:

```text
Core Runtime → authorize itself
Developer Engine → authorize itself
Control Plane → bypass authorization
Evidence → create authorization
```

---

# 7. HUMAN ACCEPTANCE BOUNDARY

Human Acceptance APPROVE berarti:

```text
HIC-01 = APPROVED
```

dan **tidak berarti**:

```text
Runtime Identity = VERIFIED
Production = AUTHORIZED
Deployment = AUTHORIZED
Database Repair = AUTHORIZED
R3 Modification = AUTHORIZED
```

---

# 8. R2 OBJECTIVE

R2 hanya bertujuan membuktikan:

```text
running runtime instance
        ↓
application
        ↓
actual request
        ↓
provider
        ↓
model
```

secara deterministic dan reproducible.

Minimal pertanyaan yang wajib dijawab:

```text
WHO is serving?
WHICH PROCESS?
WHICH APPLICATION?
WHICH PROVIDER?
WHICH MODEL?
WHICH REQUEST?
WHEN?
HOW VERIFIED?
FROM WHICH EVIDENCE?
```

---

# 9. RUNTIME IDENTITY CLASSES

Identity wajib dibedakan menjadi:

### 9.1 Configured Identity

```text
configured_provider
configured_model
```

### 9.2 Resolved Identity

```text
effective_provider
effective_model
```

### 9.3 Live Identity

```text
live_provider
live_model
```

### 9.4 Historical Identity

```text
historical_provider
historical_model
```

Keempat identity tersebut tidak boleh dipertukarkan.

---

# 10. RUNTIME INSTANCE IDENTITY

Setiap live verification wajib memiliki:

```text
runtime_instance_id
```

Runtime instance harus dapat dikaitkan dengan:

```text
process_id
executable
working_directory
start_time
listen_address
listen_port
application_identity
```

Jika environment mendukung, sertakan:

```text
parent_process
container_id
service_instance
deployment/build identity
```

---

# 11. REQUEST CORRELATION

Live verification wajib mengikat identity dengan request aktual.

Minimal:

```text
request_id
runtime_instance_id
timestamp
provider
model
result
```

Hubungan harus dapat ditelusuri:

```text
REQUEST_ID
   ↓
APPLICATION PROCESS
   ↓
RUNTIME INSTANCE
   ↓
PROVIDER
   ↓
MODEL
```

Informasi bahwa provider/model hanya tersedia di inventory **tidak cukup**.

---

# 12. RUNTIME TOPOLOGY

Agent wajib menentukan topology aktual sebelum menyimpulkan identity.

Contoh:

```text
Client
  ↓
FastAPI
  ↓
Nusantara Core
  ↓
Provider Adapter / Hermes
  ↓
Provider
  ↓
Ollama
  ↓
Model
```

Topology aktual harus berdasarkan source/runtime evidence, bukan asumsi.

---

# 13. R2 PHASE GATES

R2 wajib dilakukan melalui tahapan:

```text
R2-A0
PRE-FLIGHT
   ↓
R2-A1
READ-ONLY DISCOVERY
   ↓
R2-A2
DISCOVERY REPORT
   ↓
R2-A3
IMPLEMENTATION AUTHORIZATION
   ↓
R2-A4
MINIMAL IMPLEMENTATION
   ↓
R2-A5
LIVE VERIFICATION
   ↓
R2-A6
EVIDENCE INTEGRITY
   ↓
R2-A7
HUMAN REVIEW
   ↓
R2-A8
EXPLICIT AUTHORIZATION
   ↓
R2-A9
R2 CLOSURE
```

**Tidak boleh melewati gate.**

---

# 14. R2-A0 PRE-FLIGHT

Sebelum membaca atau mengubah source, Agent wajib mengumpulkan:

```text
repository
branch
HEAD
worktree
Python/runtime version
service status
process list
port ownership
provider inventory
model inventory
current runtime identity
existing R2 evidence
R3 evidence state
protected-file state
```

Jika baseline tidak reliable:

```text
STOP
```

---

# 15. R2-A1 READ-ONLY DISCOVERY

Discovery wajib READ-ONLY.

Agent harus memetakan:

```text
configuration
       ↓
effective configuration
       ↓
provider registry
       ↓
model registry
       ↓
composition root
       ↓
runtime initialization
       ↓
request dispatcher
       ↓
provider adapter
       ↓
actual provider
       ↓
actual model
```

Tidak boleh melakukan implementation pada tahap ini.

---

# 16. R2-A2 DISCOVERY REPORT

Sebelum implementation, Agent wajib menghasilkan:

```text
Repository Identity
Runtime Topology
Process Identity
Provider Resolution
Model Resolution
Request Path
Current Evidence
Runtime Identity Gap
Root Cause
Minimum Change
Files To Change
Files To Create
Files Protected
Tests Required
Potential Scope Expansion
```

Jika discovery menunjukkan tidak diperlukan source change:

> **NO SOURCE MODIFICATION**

harus menjadi default.

---

# 17. IMPLEMENTATION GATE

Implementation hanya boleh dilakukan apabila:

```text
Discovery complete
AND
scope remains R2
AND
minimum change identified
AND
affected files identified
AND
protected files identified
```

Jika perubahan melebihi scope:

```text
STOP
REPORT
REQUEST NEW AUTHORIZATION
```

---

# 18. CHANGE MINIMIZATION

Gunakan:

> **Smallest Safe Change**

Urutan prioritas:

```text
existing mechanism
      >
existing telemetry
      >
existing metadata
      >
existing runtime response
      >
minimal instrumentation
      >
new mechanism
```

Jangan membuat mekanisme baru apabila existing mechanism sudah dapat membuktikan identity.

---

# 19. FILE CHANGE CONTROL

Sebelum implementation:

```text
FILES TO MODIFY
FILES TO CREATE
FILES TO READ ONLY
PROTECTED FILES
```

harus dinyatakan.

Rules:

```text
Declared file      = allowed
New undeclared file = STOP
Protected file     = immutable
Unrelated file     = forbidden
```

---

# 20. PROTECTED SURFACES

Wajib immutable selama R2:

```text
R3.1–R3.14 evidence
knowledge database
*.db-wal
*.db-shm
governance state
human decision state
authorization records
```

Dilarang:

```text
repair
recreate
delete
vacuum
migrate
reindex
replace
```

terhadap protected database surfaces.

---

# 21. LIVE VERIFICATION CONTRACT

R2 dapat menghasilkan:

```text
VERIFIED
```

hanya apabila:

```text
live process
+
runtime instance
+
actual request
+
actual provider
+
actual model
```

dapat dibuktikan secara konsisten.

---

# 22. EVIDENCE HIERARCHY

Prioritas:

```text
LIVE REQUEST / RUNTIME EVIDENCE
        >
DIRECT PROVIDER RESPONSE
        >
EFFECTIVE CONFIGURATION
        >
REGISTRY
        >
HISTORICAL RECEIPT
        >
STATIC SOURCE CLAIM
```

Evidence level rendah tidak boleh mengklaim evidence level tinggi.

---

# 23. NEGATIVE VERIFICATION

Wajib menguji:

```text
Provider unavailable
Model unavailable
Configured/live mismatch
Historical-only
Inventory-only
Missing provider
Missing model
Wrong runtime process
Wrong runtime instance
```

Expected result harus tetap:

```text
NOT_VERIFIED
ERROR
MISMATCH
```

sesuai kondisi.

Negative test yang menghasilkan expected failure adalah **valid test result**, bukan test defect.

---

# 24. MULTI-PROCESS SAFETY

Jika terdapat lebih dari satu kandidat process:

```text
STOP verification claim
```

sampai ownership dapat dibuktikan.

Tidak boleh memilih process berdasarkan:

```text
first process found
most recent process
expected process
configured process
```

Process harus dibuktikan berdasarkan runtime evidence.

---

# 25. STALE RUNTIME SAFETY

Historical process atau stale process tidak boleh digunakan untuk membuktikan current runtime.

Jika:

```text
historical process ≠ current process
```

maka historical evidence hanya:

```text
HISTORICAL
```

bukan:

```text
LIVE VERIFIED
```

---

# 26. POSITIVE VERIFICATION

Minimal harus terdapat:

```text
current process
current runtime instance
actual request
provider identity
model identity
timestamp
request correlation
```

yang konsisten.

---

# 27. RECEIPT CONTRACT

Minimal:

```json
{
  "phase": "R2",
  "gate": "Provider / Model Runtime Identity",
  "verification_type": "LIVE_RUNTIME",
  "runtime_instance_id": "<id>",
  "timestamp": "<UTC>",
  "process": {
    "pid": "<pid>",
    "executable": "<path>",
    "working_directory": "<path>"
  },
  "application": "<application>",
  "request_id": "<id>",
  "request_path": "<path>",
  "provider": "<actual provider>",
  "model": "<actual model>",
  "configured_identity": {
    "provider": "<provider>",
    "model": "<model>"
  },
  "effective_identity": {
    "provider": "<provider>",
    "model": "<model>"
  },
  "result": "VERIFIED|NOT_VERIFIED|MISMATCH|ERROR|BLOCKED",
  "evidence_source": "<source>",
  "integrity": {
    "sha256": "<hash>"
  }
}
```

Tidak boleh ada nilai yang ditebak.

---

# 28. EVIDENCE PROVENANCE

Setiap evidence wajib dapat menjawab:

```text
WHO generated it?
WHEN?
FROM which process?
FROM which runtime instance?
FROM which request?
FROM which source?
HOW was it obtained?
```

Evidence tanpa provenance yang cukup tidak boleh digunakan sebagai LIVE VERIFIED.

---

# 29. DEVELOPER ENGINE SAFETY

Developer Engine tidak boleh:

```text
modify its own authorization
modify its own governance
modify approval state
mark itself authorized
suppress failed tests
rewrite evidence after failure
delete contradictory evidence
```

Developer Engine hanya menghasilkan:

```text
finding
analysis
implementation
test result
evidence
recommendation
```

---

# 30. FAILURE POLICY

Jika implementation gagal:

```text
STOP
PRESERVE EVIDENCE
DO NOT PATCH AROUND FAILURE
DO NOT FORCE PASS
REPORT ROOT CAUSE
```

Rollback hanya boleh dilakukan terhadap perubahan yang:

```text
authorized
declared
created by current R2 execution
```

Tidak boleh melakukan repository-wide cleanup.

---

# 31. ROLLBACK SAFETY

Rollback tidak boleh menyentuh:

```text
R3 evidence
knowledge DB
WAL
SHM
governance
human decision
unrelated source
```

Jika rollback memerlukan protected surface:

```text
STOP
REQUEST AUTHORIZATION
```

---

# 32. TEST MATRIX

Minimum:

```text
R2-T01 configured provider
R2-T02 configured model
R2-T03 effective provider
R2-T04 effective model
R2-T05 current process
R2-T06 runtime instance
R2-T07 live provider
R2-T08 live model
R2-T09 actual request path
R2-T10 request correlation
R2-T11 historical-only
R2-T12 inventory-only
R2-T13 provider unavailable
R2-T14 model unavailable
R2-T15 provider mismatch
R2-T16 model mismatch
R2-T17 wrong/stale process
R2-T18 missing identity
R2-T19 regression
R2-T20 evidence integrity
```

---

# 33. REGRESSION

R2 verification tidak boleh merusak:

```text
existing Core Runtime behavior
existing API contract
existing R3 evidence
existing Control Plane
existing tests
existing knowledge state
```

Regression failure:

```text
R2 = NOT_VERIFIED
```

kecuali root cause dan authorization baru tersedia.

---

# 34. STATUS SEMANTICS

Gunakan status secara ketat:

```text
VERIFIED
NOT_VERIFIED
MISMATCH
ERROR
BLOCKED
```

`PASS` hanya boleh digunakan untuk **test result**, bukan sebagai sinonim Runtime Identity.

Contoh:

```text
R2-T01 = PASS
Runtime Identity = NOT_VERIFIED
```

adalah valid.

---

# 35. R2 CLOSURE

R2 tidak selesai hanya karena test suite PASS.

Closure wajib:

```text
Discovery
 ↓
Implementation
 ↓
Verification
 ↓
Evidence
 ↓
Integrity
 ↓
Human Review
 ↓
Explicit Human Authorization
 ↓
Closure
```

---

# 36. HARD STOP CONDITIONS

Agent wajib STOP apabila:

```text
runtime identity tidak terbukti
provider/model mismatch
multiple ambiguous runtime processes
evidence contradiction
request correlation tidak terbukti
R3 harus diubah
DB harus diubah
WAL/SHM harus disentuh
governance harus dimutasi
authorization scope tidak cukup
undeclared file harus diubah
broad refactor diperlukan
rollback membutuhkan protected surface
historical evidence satu-satunya proof
Developer Engine harus self-authorize
```

---

# 37. ACCEPTANCE CRITERIA

R2 hanya dapat diajukan `VERIFIED` apabila:

```text
[ ] Baseline captured
[ ] Runtime topology identified
[ ] Current process identified
[ ] Runtime instance identified
[ ] Provider resolved
[ ] Model resolved
[ ] Effective configuration resolved
[ ] Actual request traced
[ ] Request correlation established
[ ] Live provider confirmed
[ ] Live model confirmed
[ ] Timestamp recorded
[ ] Positive verification passed
[ ] Negative verification passed
[ ] Provider mismatch tested
[ ] Model mismatch tested
[ ] Historical identity separated
[ ] Inventory identity separated
[ ] Stale process tested
[ ] R3 unchanged
[ ] DB unchanged
[ ] WAL unchanged
[ ] SHM unchanged
[ ] Governance unchanged
[ ] Regression passed
[ ] Evidence integrity verified
[ ] Human review completed
[ ] Explicit authorization obtained
```

Jika satu mandatory condition gagal:

```text
R2 = NOT_VERIFIED
```

---

# 38. REPORTING CONTRACT

Final report wajib:

```text
R2 CORE RUNTIME IDENTITY EXECUTION REPORT

1. Authorization
2. Repository
3. Baseline
4. Runtime Topology
5. Process Identity
6. Runtime Instance
7. Configured Identity
8. Effective Identity
9. Live Identity
10. Historical Identity
11. Request Correlation
12. Provider
13. Model
14. Discovery Findings
15. Root Cause
16. Changes
17. Files Changed
18. Files Created
19. Files Protected
20. Tests
21. Negative Tests
22. Mismatch Tests
23. Regression
24. Evidence Receipt
25. Integrity
26. R3 Impact
27. Database Impact
28. WAL/SHM Impact
29. Governance Impact
30. Remaining Limitations
31. Final R2 Status
32. Recommended Next Gate
```

---

# 39. NO SELF-AUTHORIZATION

Tidak ada kondisi di mana Developer Engine dapat menghasilkan:

```text
"I authorize myself"
```

atau:

```text
"R2 is authorized because my tests passed"
```

Authorization final berada di luar Developer Engine.

---

# 40. EVIDENCE WINS

Jika desired outcome bertentangan dengan evidence:

> **EVIDENCE WINS.**

Jika evidence:

```text
NOT_VERIFIED
```

maka status tetap:

```text
NOT_VERIFIED
```

sampai evidence baru yang valid membuktikan sebaliknya.

---

# 41. MASTER EXECUTION DIRECTIVE

## Instruksi Final kepada Web Developer / ChatGPT Coding Agent

```text
You are operating under the
NUSANTARA R2 CORE RUNTIME & DEVELOPER EXECUTION AUTHORIZATION CONTRACT.

Your authority is strictly limited to R2
Provider / Model Runtime Identity.

You are NOT the authorization authority.

You are the engineering execution mechanism.

DO NOT begin implementation immediately.

FIRST:

1. establish repository baseline;
2. establish runtime topology;
3. identify current processes;
4. identify runtime instance;
5. inspect provider resolution;
6. inspect model resolution;
7. inspect effective configuration;
8. trace composition root;
9. trace runtime initialization;
10. trace actual request dispatch;
11. trace provider invocation;
12. trace model invocation.

Perform READ-ONLY DISCOVERY first.

Produce:

- baseline;
- runtime topology;
- process identity;
- runtime instance identity;
- configured identity;
- effective identity;
- current live identity;
- historical identity;
- request path;
- request correlation capability;
- evidence sources;
- root cause;
- minimum safe change;
- files to modify;
- files to create;
- protected files;
- test plan.

DO NOT implement until the discovery boundary is satisfied.

If no source modification is required,
DO NOT modify source.

If implementation is required,
use the smallest safe change.

Never modify:

- R3.1–R3.14 evidence;
- knowledge database;
- WAL;
- SHM;
- governance state;
- human decision state;
- authorization state.

Never:

- self-authorize;
- force PASS;
- convert NOT_VERIFIED into VERIFIED without evidence;
- treat configuration as live identity;
- treat inventory as live identity;
- treat health status as model proof;
- treat historical receipt as current runtime proof;
- select an arbitrary process;
- hide contradictory evidence.

After authorized implementation:

1. run positive tests;
2. run negative tests;
3. run provider mismatch tests;
4. run model mismatch tests;
5. run stale/wrong-process tests;
6. verify request correlation;
7. verify runtime instance;
8. run regression;
9. verify R3 unchanged;
10. verify DB unchanged;
11. verify WAL/SHM unchanged;
12. verify governance unchanged;
13. generate evidence receipt;
14. verify evidence integrity;
15. generate final execution report.

If any protected surface must be modified:

STOP.

If any scope expansion is required:

STOP.

If runtime identity cannot be proven:

FINAL STATUS MUST REMAIN NOT_VERIFIED.

If evidence conflicts with desired outcome:

EVIDENCE WINS.

Never self-authorize.

Never hide limitations.

Never repair protected data.

Never bypass human governance.
```

---

# 42. FINAL AUTHORIZATION STATE

```text
┌───────────────────────────────────────────────┐
│ NUSANTARA R2 AUTHORIZATION                    │
├───────────────────────────────────────────────┤
│ Human Acceptance       APPROVED                │
│ Human Test             8/8 PASS                │
│ R3 Evidence            14/14 PASS              │
│ R2 Engineering Gate    CLOSED_PASS             │
│ Runtime Identity       NOT_VERIFIED            │
├───────────────────────────────────────────────┤
│ Core Runtime            EXECUTION ONLY         │
│ Developer Engine        AUTHORIZED R2 SCOPE    │
│ Control Plane           GOVERNANCE ONLY        │
│ Self-Authorization      FORBIDDEN              │
│ R3 Mutation             FORBIDDEN              │
│ DB Mutation             FORBIDDEN              │
│ WAL/SHM Mutation        FORBIDDEN              │
└───────────────────────────────────────────────┘
```

**END OF NUSANTARA R2 CORE RUNTIME & DEVELOPER EXECUTION AUTHORIZATION CONTRACT**
