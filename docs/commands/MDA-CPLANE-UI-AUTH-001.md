# MDA-CPLANE-UI-AUTH-001

## NUSANTARA ENGINEERING CONTROL PLANE UI

### MASTER DEVELOPER ENGINE — UI AUTHORIZATION CONTRACT

**Status:** PROPOSED / AUTHORIZATION REQUIRED
**Contract Class:** Engineering Control Plane / Read-Only UI
**Target:** Nusantara Core + Hermes
**Workspace:** `C:\Users\dmaza\mcp-starter`
**Current Branch:** `codex/fullroot-control-20261007`
**Baseline:** R2 `CLOSED_PASS`
**Current Engineering State:** R3 `IMPLEMENTATION_PASS_WITH_CONDITIONS`
**R4:** LOCKED
**R5:** LOCKED
**MDE10:** NOT AUTHORIZED

---

# 1. CONTRACT PURPOSE

Kontrak ini memberikan otorisasi terbatas untuk merancang dan mengimplementasikan:

> **Nusantara Engineering Control Plane UI**

Control Plane bukan dashboard statistik biasa.

Control Plane adalah **engineering control surface** yang memberikan visibilitas terstruktur terhadap:

```text
SYSTEM
  ↓
PHASE
  ↓
CONTRACT
  ↓
SCOPE
  ↓
GATE
  ↓
AUTHORIZATION
  ↓
EVIDENCE
  ↓
VERIFICATION
  ↓
ACCEPTANCE
  ↓
CLOSE
```

UI harus memungkinkan engineer melihat:

* kondisi sistem;
* phase aktif;
* contract aktif;
* gate;
* authorization;
* evidence;
* verification;
* acceptance state;
* runtime identity;
* RAG profile;
* governance state;
* worktree state;
* blockers;
* warnings;
* limitations;
* historical phase state.

Control Plane **tidak menjadi autonomous developer agent**.

---

# 2. PRIMARY ENGINEERING PRINCIPLE

Control Plane harus:

```text
READ
↓
INTERPRET
↓
PRESENT
↓
TRACE
```

dan **bukan**:

```text
READ
↓
DECIDE
↓
MODIFY
↓
DEPLOY
```

Pada kontrak ini UI bersifat:

> **READ-ONLY BY DEFAULT**

Tidak boleh mengubah source code, production knowledge database, runtime configuration, model, embedding, index, atau governance state.

---

# 3. APPROVED TECHNOLOGY STACK

## 3.1 Frontend Language

Bahasa utama:

```text
TypeScript
```

JavaScript tanpa TypeScript **tidak digunakan sebagai bahasa utama**.

Seluruh domain object harus memiliki typed interface/schema.

---

# 4. FRONTEND STACK

## 4.1 Application Framework

```text
React
```

React digunakan sebagai UI application runtime.

---

## 4.2 Build Tool

```text
Vite
```

Vite digunakan sebagai development server dan production build system.

---

## 4.3 Routing

```text
TanStack Router
```

Routing harus typed dan eksplisit.

Minimal route:

```text
/
 /overview
 /roadmap
 /architecture
 /engineering
 /governance
 /verification
 /runtime
 /knowledge
```

---

# 5. DATA / SERVER STATE

Gunakan:

```text
TanStack Query
```

untuk:

* API query;
* refresh;
* caching;
* loading state;
* error state;
* query invalidation;
* polling jika nanti diperlukan.

Tidak boleh membuat state management global yang kompleks tanpa kebutuhan yang terbukti.

---

# 6. DATA VALIDATION

Gunakan:

```text
Zod
```

Semua data dari backend harus divalidasi sebelum digunakan oleh UI.

Contoh domain:

```text
Phase
Contract
Gate
Evidence
RuntimeIdentity
RAGProfile
WorktreeStatus
GovernanceState
VerificationResult
```

UI tidak boleh mengasumsikan response backend selalu valid.

---

# 7. VISUALIZATION ENGINE

Untuk architecture/dependency/phase graph:

```text
React Flow
```

digunakan sebagai visualization engine.

Minimal kemampuan:

```text
Node
Edge
Selection
Zoom
Pan
Collapse/Expand
Detail panel
Status indicator
Trace-to-source
```

Graph tidak boleh menjadi dekorasi.

Setiap node harus mempunyai semantic identity.

---

# 8. TESTING STACK

## Unit / Component

```text
Vitest
Testing Library
```

## End-to-End

```text
Playwright
```

Minimal E2E:

```text
Open Control Plane
↓
Overview loads
↓
R2 displayed CLOSED_PASS
↓
R3 displayed current
↓
R4 displayed LOCKED
↓
R5 displayed LOCKED
↓
MDE10 displayed NOT AUTHORIZED
```

---

# 9. BACKEND INTEGRATION

Backend Nusantara Core existing tetap:

```text
Python
FastAPI
```

Backend **tidak diganti** oleh framework frontend.

Control Plane harus mengonsumsi API existing terlebih dahulu.

Tidak boleh membuat backend kedua hanya untuk memenuhi kebutuhan UI.

---

# 10. API ARCHITECTURE

UI harus menggunakan typed API client.

Architecture:

```text
React / TypeScript
        │
        ▼
Typed API Client
        │
        ▼
Nusantara Core FastAPI
        │
        ├── Configuration
        ├── Runtime
        ├── RAG
        ├── Evidence
        ├── Observability
        └── Governance evidence
```

UI tidak boleh membaca database production secara langsung sebagai shortcut.

---

# 11. PRODUCTION KNOWLEDGE DATABASE PROTECTION

Protected database:

```text
data\knowledge\nusantara_knowledge.db
```

Status:

```text
PROTECTED
```

Control Plane:

```text
READ ONLY
```

Tidak boleh:

* INSERT;
* UPDATE;
* DELETE;
* ALTER;
* CREATE INDEX;
* rebuild embedding;
* rebuild FTS;
* modify WAL;
* modify SHM;
* migrate schema;
* compact database;
* regenerate knowledge.

Tidak boleh membuat UI feature yang secara tidak sengaja mengubah database tersebut.

---

# 12. NO CONTROL DATABASE

Pada fase ini:

```text
data\control\nusantara_control.db
```

**BELUM BOLEH DIBUAT.**

Control Plane harus memanfaatkan evidence yang sudah ada.

Sumber awal dapat berupa:

```text
repository state
contract documents
checkpoint artifacts
test results
runtime receipts
configuration snapshots
Git state
existing API
existing observability context
```

Jika kemudian diperlukan persistent Control Plane database, harus dibuat melalui contract terpisah.

---

# 13. PRIMARY UI INFORMATION ARCHITECTURE

Navigation canonical:

```text
NUSANTARA ENGINEERING CONTROL PLANE

├── Overview
├── Roadmap
├── Architecture
├── Engineering
├── Governance
├── Verification
├── Runtime
└── Knowledge
```

---

# 14. OVERVIEW

Overview merupakan halaman utama.

Minimal menampilkan:

```text
NUSANTARA CORE
SYSTEM STATUS

CURRENT PHASE
R3 — Effective RAG Profile

PHASE STATUS
IMPLEMENTATION_PASS_WITH_CONDITIONS

ACTIVE CONTRACT
MDA-R3-EFFECTIVE-RAG-001

R2
✓ CLOSED_PASS

R3
● IMPLEMENTATION_PASS_WITH_CONDITIONS

R4
🔒 LOCKED

R5
🔒 LOCKED

MDE10
🔒 NOT AUTHORIZED
```

Tambahkan:

```text
BLOCKERS
WARNINGS
WORKTREE
RUNTIME
RAG
GOVERNANCE
VERIFICATION
```

---

# 15. STATUS MUST BE DERIVED

Status tidak boleh hard-coded sebagai teks UI.

Contoh:

```text
R2 = CLOSED_PASS
```

harus berasal dari evidence/contract state.

Bukan:

```typescript
const status = "CLOSED_PASS";
```

tanpa source authority.

Canonical principle:

```text
Evidence → State → UI
```

bukan:

```text
UI → Assumed State
```

---

# 16. ROADMAP VIEW

Roadmap harus memperlihatkan:

```text
R1
Configuration Intelligence
        ↓
R2
Provider / Model Runtime Identity
        ↓
R3
Effective RAG Profile
        ↓
R4
Embedding / Index Compatibility
        ↓
R5
Runtime Enforcement
```

Namun UI wajib membedakan:

```text
EXISTING / VERIFIED
```

dengan:

```text
PROPOSED
```

dan:

```text
NOT AUTHORIZED
```

UI tidak boleh mengklaim phase yang belum memiliki authorization sebagai existing engineering fact.

---

# 17. ARCHITECTURE VIEW

Architecture view harus memperlihatkan hubungan:

```text
Configuration
      ↓
Effective Configuration
      ↓
Provider / Model
      ↓
Knowledge Engine
      ↓
RAG
      ↓
Embedding
      ↓
Retrieval
      ↓
Evidence
      ↓
LLM
      ↓
Response
```

Dan control layer:

```text
Contract
   ↓
Gate
   ↓
Evidence
   ↓
Verification
   ↓
Acceptance
```

---

# 18. ENGINEERING VIEW

Engineering page harus menjadi tempat engineer memahami pekerjaan aktif.

Minimal section:

```text
CURRENT OBJECTIVE

ACTIVE CONTRACT

AUTHORIZED SCOPE

CURRENT GATE

FINDINGS

BLOCKERS

WARNINGS

PROPOSED SOLUTION

IMPACT

CHANGED FILES

TEST RESULTS

VERIFICATION

LIMITATIONS

NEXT AUTHORIZED ACTION
```

Tidak ada tombol:

```text
AUTO IMPLEMENT
```

pada fase ini.

---

# 19. GOVERNANCE VIEW

Governance harus menampilkan:

```text
Authorization
Scope
Protected Assets
Change Boundary
Acceptance
Rollback
Commit State
Push State
```

Contoh:

```text
R2
CLOSED_PASS
IMMUTABLE

R3
IMPLEMENTATION_PASS_WITH_CONDITIONS

R4
LOCKED
REQUIRES AUTHORIZATION

R5
LOCKED
REQUIRES R4 CLOSURE
```

---

# 20. VERIFICATION VIEW

Verification menampilkan:

```text
Tests
Regression
Static Analysis
Runtime Verification
Evidence Hash
Artifact Hash
Protected Data Integrity
Scope Isolation
Worktree Isolation
```

Contoh R3:

```text
Focused Tests
29 PASS

Regression
157 PASS
0 FAIL

Query Parity
24 / 24

Static Syntax
6 / 6

Protected Data
UNCHANGED

Scope Isolation
PASS

Worktree Isolation
PASS
```

Nilai tersebut harus berasal dari evidence, bukan diketik ulang manual.

---

# 21. RUNTIME VIEW

Runtime view harus memperlihatkan:

```text
Provider
Configured Model
Effective Model
Actual Runtime Model
Runtime Build Identity
Process Identity
Health
Verification Status
```

Untuk R2:

```text
Actual Runtime Model
llama3.2:1b

Runtime Verification
RUNTIME_CONFIRMED
```

UI harus membedakan:

```text
CONFIGURATION CLAIM
```

dari:

```text
RUNTIME EVIDENCE
```

---

# 22. KNOWLEDGE VIEW

Knowledge view harus memperlihatkan:

```text
Knowledge Store
RAG Profile
Retrieval Strategy
Embedding Configuration
Embedding Status
Top-K
Candidate Count
Semantic Weight
Lexical Weight
Reranker
Relevance Gate
Provenance
```

Untuk R3:

```text
Strategy
canonical_hybrid_semantic_lexical_topk_rerank_gate

Top-K
2

Candidate Count
20

Semantic
0.70

Lexical
0.30

Absolute Gate
0.30

Relative Threshold
0.50
```

---

# 23. R3 EFFECTIVE RAG PROFILE

UI harus mampu menampilkan profile:

```text
profile_id
invocation_id
consumer
correlation_id
request_id
session_id
retrieval_strategy
top_k
candidate_count
semantic_weight
lexical_weight
absolute_gate
relative_threshold
resolved_gate
reranker
embedding_identity
knowledge_source
provenance
execution_outcome
```

Profile identity harus diperlakukan immutable untuk invocation tersebut.

---

# 24. TRACEABILITY

Setiap status material harus dapat ditelusuri:

```text
UI State
   ↓
Evidence
   ↓
Artifact
   ↓
Contract
   ↓
Gate
```

Contoh:

```text
R3 PASS
  ↓
R3.12 Regression
  ↓
closure-regression.xml
  ↓
MDA-R3
```

UI harus menampilkan source/reference bila tersedia.

---

# 25. NO FABRICATION

Control Plane dilarang membuat informasi yang tidak tersedia.

Jika evidence tidak tersedia:

```text
NOT_VERIFIED
```

Jika status belum diketahui:

```text
UNKNOWN
```

Jika belum authorized:

```text
NOT_AUTHORIZED
```

Jika dikunci:

```text
LOCKED
```

Jangan mengubahnya menjadi:

```text
PASS
```

hanya karena UI membutuhkan nilai.

---

# 26. ERROR STATE

UI wajib memiliki state:

```text
LOADING
READY
PARTIAL
UNKNOWN
NOT_VERIFIED
BLOCKED
LOCKED
ERROR
```

Tidak boleh menampilkan dashboard kosong seolah-olah sistem sehat ketika backend/evidence gagal dibaca.

---

# 27. WORKTREE INSPECTOR

Control Plane harus mampu menampilkan:

```text
Tracked Changes
Untracked Changes
Staged Changes
Modified Files
Ownership
Scope
```

Namun UI tidak boleh menghapus atau mengubah file.

R3 inherited changes harus tetap diperlakukan sebagai:

```text
PRE-EXISTING / INHERITED
```

apabila evidence mendukung status tersebut.

---

# 28. IMMUTABILITY RULE

Control Plane tidak boleh:

```text
git reset
git clean
git restore
git checkout
git amend
git rebase
git squash
```

Tidak boleh melakukan mutation terhadap repository pada kontrak ini.

---

# 29. SECURITY MODEL

Frontend tidak boleh menyimpan:

* API secret;
* provider secret;
* token;
* password;
* private key;
* production credential.

Secrets tetap berada pada backend/runtime environment.

---

# 30. NO DIRECT MODEL CONTROL

UI tidak boleh langsung:

```text
download model
delete model
switch production model
modify Ollama configuration
modify embedding model
rebuild index
```

Semua aktivitas tersebut berada di luar scope Control Plane v0.1.

---

# 31. DESIGN PRINCIPLE

Visual language:

```text
Engineering Console
```

bukan:

```text
Marketing Dashboard
```

Prioritas:

```text
Clarity
Traceability
Evidence
Status
Risk
Governance
```

bukan visual decoration.

---

# 32. COMPONENT ARCHITECTURE

Recommended structure:

```text
control-plane/
│
├── src/
│   ├── app/
│   ├── routes/
│   ├── components/
│   ├── features/
│   │   ├── overview/
│   │   ├── roadmap/
│   │   ├── architecture/
│   │   ├── engineering/
│   │   ├── governance/
│   │   ├── verification/
│   │   ├── runtime/
│   │   └── knowledge/
│   │
│   ├── domain/
│   ├── api/
│   ├── schemas/
│   ├── graph/
│   ├── hooks/
│   ├── utils/
│   └── main.tsx
│
├── tests/
├── e2e/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── playwright.config.ts
```

Exact directory placement remains subject to repository discovery.

Do not create the structure blindly before discovery.

---

# 33. BACKEND ADAPTER

Create a typed adapter layer:

```text
src/api/
```

Responsibilities:

```text
fetch phase state
fetch contract state
fetch runtime state
fetch RAG state
fetch verification state
fetch governance state
fetch worktree state
```

UI components must not directly call arbitrary URLs.

---

# 34. DOMAIN MODEL

Minimum TypeScript domain types:

```typescript
PhaseState
ContractState
GateState
EvidenceReference
RuntimeIdentity
RAGProfile
VerificationResult
GovernanceState
WorktreeState
SystemHealth
```

Domain objects must separate:

```text
identity
status
provenance
evidence
timestamp
```

---

# 35. REFRESH MODEL

Initial implementation:

```text
manual refresh
```

Optional:

```text
30–60 second polling
```

only where justified.

Do not create aggressive polling.

---

# 36. PERFORMANCE

Control Plane must remain responsive with:

```text
large graph
many evidence records
large worktree
multiple phases
```

Graph rendering must support progressive loading where necessary.

Do not load the entire repository into browser memory merely to render Overview.

---

# 37. ACCESS MODEL

Initial version:

```text
LOCAL ENGINEERING USE
```

No public deployment requirement.

Default bind should be local unless explicitly authorized otherwise.

---

# 38. OBSERVABILITY

Control Plane itself should expose UI diagnostics:

```text
API latency
API availability
last refresh
data source
data freshness
frontend build identity
```

But it must not alter Nusantara runtime observability.

---

# 39. BUILD IDENTITY

Every Control Plane build should expose:

```text
application version
git commit
build timestamp
build environment
```

Example:

```text
Control Plane
v0.1.0

Build
<commit>

Environment
development
```

Build timestamp must not be used as the sole identity.

---

# 40. ACCEPTANCE GATES

## CPLANE-01

Technology stack verified.

Required:

```text
TypeScript
React
Vite
TanStack Router
TanStack Query
Zod
```

---

## CPLANE-02

No HTML-only implementation.

PASS requires:

```text
React + TypeScript application
```

---

## CPLANE-03

Backend integration verified.

PASS requires:

```text
Typed API client
FastAPI integration
```

---

## CPLANE-04

Overview verified.

PASS requires:

```text
Current phase
Contract
Gate
R2 state
R3 state
R4 lock
R5 lock
MDE10 authorization state
```

---

## CPLANE-05

Evidence traceability verified.

Every material state must have source/evidence reference where available.

---

## CPLANE-06

No fabrication verified.

Missing evidence must resolve to:

```text
UNKNOWN
NOT_VERIFIED
NOT_AUTHORIZED
LOCKED
```

as appropriate.

---

## CPLANE-07

Production DB protection verified.

Hash must remain unchanged:

```text
51C5445A43CAC61C7763D6AA24BCBB1401C0491CA83A2601E0E5814751325625
```

---

## CPLANE-08

Repository mutation protection verified.

No:

```text
reset
clean
restore
rebase
amend
squash
```

performed.

---

## CPLANE-09

Test coverage verified.

Minimum:

```text
Vitest
Testing Library
Playwright
```

---

## CPLANE-10

Graph visualization verified.

Architecture graph must support:

```text
nodes
edges
selection
zoom
detail
traceability
```

---

## CPLANE-11

Runtime identity view verified.

R2 identity chain must be represented separately:

```text
Configured Model
→ Effective Model
→ Selected Provider
→ Actual Runtime Model
→ Runtime Build Identity
```

---

## CPLANE-12

R3 profile verified.

Effective RAG Profile must be rendered from actual evidence.

---

## CPLANE-13

Read-only enforcement verified.

UI must not modify:

```text
source
production DB
runtime model
embedding
index
configuration
governance state
```

---

## CPLANE-14

E2E acceptance verified.

Critical path:

```text
Open
→ Overview
→ Roadmap
→ Architecture
→ R3
→ Runtime
→ Verification
```

must work.

---

# 41. IMPLEMENTATION PHASES

Implementation must follow:

```text
CPLANE-0
Discovery
      ↓
CPLANE-1
Architecture
      ↓
CPLANE-2
Typed Data Layer
      ↓
CPLANE-3
Overview
      ↓
CPLANE-4
Roadmap + Architecture
      ↓
CPLANE-5
Engineering + Governance
      ↓
CPLANE-6
Runtime + Knowledge
      ↓
CPLANE-7
Verification
      ↓
CPLANE-8
E2E + Hardening
      ↓
CPLANE-9
Acceptance
```

No phase may silently skip its gate.

---

# 42. DISCOVERY-FIRST RULE

Before implementation:

1. inspect repository;
2. inspect existing UI;
3. inspect existing API;
4. inspect existing observability;
5. inspect existing Graphify output;
6. inspect existing contracts;
7. identify reusable components;
8. identify collision risk;
9. define exact file boundary;
10. record baseline.

Do not immediately scaffold a second application without checking existing UI architecture.

---

# 43. CHANGE BOUNDARY

The exact implementation boundary must be established after discovery.

At authorization time:

```text
SOURCE FILES = UNKNOWN
```

is acceptable.

After discovery:

```text
AUTHORIZED FILE SET
```

must be explicitly recorded.

Any file outside the authorized boundary:

```text
OUT_OF_SCOPE
```

unless separately authorized.

---

# 44. PROTECTED ASSETS

The following remain protected:

```text
data\knowledge\nusantara_knowledge.db

R2 evidence
R2 acceptance records
R3 implementation evidence
existing production knowledge
existing runtime configuration
existing model installation
existing embedding/index
```

---

# 45. ROLLBACK

Rollback must be:

```text
isolated
non-destructive
evidence-based
```

No broad repository restore.

No:

```text
git clean
git reset --hard
```

Rollback may only revert Control Plane-owned changes after ownership is proven.

---

# 46. COMMIT POLICY

This contract does not automatically authorize commit.

Default:

```text
IMPLEMENTATION = AUTHORIZED
COMMIT = NOT AUTHORIZED
PUSH = NOT AUTHORIZED
```

Commit requires separate owner decision unless explicitly included in a later acceptance authorization.

---

# 47. AUTONOMY BOUNDARY

The Control Plane is:

```text
OBSERVABILITY + ENGINEERING GOVERNANCE UI
```

It is not:

```text
AUTONOMOUS SOFTWARE ENGINEER
```

No automatic:

```text
code generation
code modification
git mutation
deployment
model switching
database migration
production release
```

under this contract.

---

# 48. SUCCESS CRITERIA

The Control Plane is successful when an engineer can open one application and answer:

```text
Where is Nusantara now?

What phase is active?

What contract governs it?

What gate is active?

What is authorized?

What is blocked?

What changed?

Why did it change?

What evidence proves it?

What runtime is actually running?

What RAG configuration is actually consumed?

What remains unverified?

What can be done next?

What is NOT authorized?
```

without manually reconstructing the answer from multiple folders.

---

# 49. FINAL GOVERNANCE RULE

The Control Plane must never become the source of truth merely because it displays the truth.

Canonical authority remains:

```text
SOURCE
↓
CONTRACT
↓
EVIDENCE
↓
VERIFICATION
↓
ACCEPTANCE
↓
CONTROL PLANE
```

The UI is therefore:

> **A projection of engineering truth, not the authority that creates engineering truth.**

---

# 50. AUTHORIZATION STATEMENT

This contract authorizes the development of:

> **Nusantara Engineering Control Plane UI v0.1**

using:

```text
TypeScript
React
Vite
TanStack Router
TanStack Query
Zod
React Flow
Vitest
Testing Library
Playwright
```

with existing:

```text
Python
FastAPI
Nusantara Core
Hermes
```

as backend/runtime foundation.

It does **not** authorize:

```text
production database modification
runtime architecture replacement
model replacement
embedding/index modification
MDE10 implementation
autonomous developer behavior
production deployment
repository-wide refactoring
```

Final state of this contract:

```text
CONTRACT STATUS
PROPOSED

IMPLEMENTATION
NOT YET AUTHORIZED

COMMIT
NOT AUTHORIZED

PUSH
NOT AUTHORIZED
```

Owner acceptance is required before implementation begins.
