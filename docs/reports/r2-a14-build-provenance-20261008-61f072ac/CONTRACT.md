# R2-A14 — BUILD PROVENANCE & RUNTIME BINDING

# BOUNDED DEVELOPMENT ENVELOPE

Date: 2026-10-08

## PRECONDITION

R2-A13 completed with:

PROCESS_IDENTITY = VERIFIED within bounded observation
ACTIVE_PROCESS_BUILD = NOT_DIRECTLY_VERIFIED
Runtime Identity = NOT_VERIFIED
R2-A8 = BLOCKED / NOT_VERIFIED
R2-A9 = HOLD

R2-A13 established that the existing runtime projection cannot prove that the active process is executing the current application build.

Do NOT repeat R2-A12 or R2-A13.

---

# OBJECTIVE

Develop the minimum technically sound foundation required to establish a deterministic and trusted relationship between:

REPOSITORY
↓
CLOSED BUILD DEFINITION
↓
SOURCE / ARTIFACT BUILD ID
↓
LOADED RUNTIME PROVENANCE
↓
PROCESS IDENTITY
↓
RUNTIME INSTANCE
↓
ACTIVE PROCESS BUILD
↓
RUNTIME IDENTITY

The objective is to DESIGN AND IMPLEMENT THE MINIMUM BINDING MECHANISM.

Do not activate live runtime verification.

Do not promote any gate.

---

# AUTONOMOUS ENGINEERING AUTHORIZATION

Developer is authorized to perform the complete bounded engineering workflow without asking for approval for each individual engineering step:

1. inspect existing implementation;
2. inspect existing runtime identity / attestation implementation;
3. inspect existing source-build calculation;
4. inspect existing registered-code manifest;
5. identify the smallest architecture-compatible provenance mechanism;
6. implement the minimum required source changes;
7. create focused regression tests;
8. run only the required focused tests;
9. create evidence and report;
10. inspect Git before/after;
11. STOP after evidence review.

This is one bounded Development Envelope.

No additional approval is required for individual source inspection, implementation, focused testing or evidence creation.

---

# CORE ENGINEERING REQUIREMENT

The implementation must define what constitutes the COMPLETE APPLICATION BUILD.

A build identity MUST NOT be declared complete merely because:

* PID matches;
* process start time matches;
* repository path matches;
* Git HEAD matches;
* one source snapshot matches;
* selected registered-code hashes match;
* endpoint-generated identity matches itself;
* a client supplies an expected hash;
* a boolean flag claims full verification.

These are insufficient individually.

---

# REQUIRED BUILD MODEL

Define a closed build manifest or equivalent deterministic build definition containing the complete set of inputs that constitute the application runtime build.

The mechanism must explicitly distinguish:

EXPECTED_BUILD_ID
from
OBSERVED_LOADED_BUILD_ID

and:

SOURCE_BUILD_ID
from
ACTIVE_PROCESS_BUILD

and:

APPLICATION_BUILD_ID
from
PROVIDER_RUNTIME_IDENTITY.

Do not merge these concepts.

---

# REQUIRED IDENTITY CHAIN

The resulting architecture must support:

PROCESS_IDENTITY
↓
RUNTIME_INSTANCE_ID
↓
EXPECTED_BUILD_ID
↓
OBSERVED_LOADED_BUILD_ID
↓
ACTIVE_PROCESS_BUILD
↓
RUNTIME_IDENTITY

The final assessment must be fail-closed.

Rules:

MATCH
→ VERIFIED

MISMATCH
→ NOT_VERIFIED

MISSING
→ NOT_VERIFIED

MALFORMED
→ NOT_VERIFIED

INCOMPLETE
→ NOT_VERIFIED

UNTRUSTED
→ NOT_VERIFIED

UNOBSERVABLE
→ NOT_VERIFIED

Do not downgrade these states into warnings that permit VERIFIED.

---

# TRUST REQUIREMENT

The provenance mechanism must establish a trustworthy relationship between the build definition and the code/artifacts actually loaded by the running process.

Do not claim that a disk hash proves loaded memory.

Do not claim that a registered handler hash proves the complete application build.

Do not claim that import-time source snapshot proves complete loaded provenance.

If complete loaded provenance cannot be established within the current architecture, explicitly report:

ACTIVE_PROCESS_BUILD = NOT_DIRECTLY_VERIFIED

and explain the remaining boundary.

Do not fabricate a stronger result.

---

# MINIMUM IMPLEMENTATION PRINCIPLE

Preserve the existing architecture.

Prefer:

* existing runtime identity structures;
* existing attestation structures;
* existing build/source identity functions;
* existing registered-code manifest mechanisms;
* existing fail-closed assessment paths.

Avoid introducing a parallel identity architecture unless technically unavoidable.

Make the smallest source change necessary.

Do not redesign unrelated components.

---

# REQUIRED FOCUSED TEST MATRIX

Create focused tests for the new mechanism.

At minimum:

A. complete matching build provenance
→ VERIFIED

B. build mismatch
→ NOT_VERIFIED

C. missing expected build identity
→ NOT_VERIFIED

D. missing observed loaded identity
→ NOT_VERIFIED

E. malformed provenance
→ NOT_VERIFIED

F. incomplete build manifest
→ NOT_VERIFIED

G. untrusted provenance
→ NOT_VERIFIED

H. deterministic repeated assessment
→ identical result

I. process identity mismatch
→ NOT_VERIFIED

J. runtime instance mismatch
→ NOT_VERIFIED

K. provider/model remains uninvoked

L. authorization remains unactivated

M. protected state remains unchanged

N. existing R2-A11 regression remains passing

O. existing runtime-attestation regression remains passing

Do not claim any test that was not actually executed.

---

# LIVE RUNTIME RESTRICTION

ABSOLUTELY DO NOT:

* restart Nusantara service;
* stop the existing process;
* start another application process;
* reload application code;
* manufacture a fresh runtime;
* invoke provider generation;
* invoke model health/list-model;
* call `/v2/chat`;
* activate authorization;
* grant;
* reserve;
* dispatch;
* invoke MCP;
* mutate RAG;
* mutate database;
* mutate embeddings/indexes.

The currently running process MUST remain untouched.

---

# RESTART RULE

If implementation of the new mechanism requires a process restart or reload to become active:

STOP.

Do not restart.

Report exactly:

RUNTIME_RESTART_REQUIRED = YES

and:

IMPLEMENTATION_READY_FOR_ACTIVATION = YES

The mechanism may be tested using isolated/fresh-process test fixtures where this does not affect the existing running service.

A test subprocess is permitted only when:

* it is isolated;
* it does not bind port 8000;
* it does not invoke a provider;
* it does not activate authorization;
* it does not mutate protected state;
* it does not replace the existing runtime.

---

# CONTROL PLANE RESTRICTION

Do NOT modify:

* Control Plane routes;
* Control Plane UX;
* Control Plane schemas;
* SYSTEM/EVIDENCE/TEST/REVIEW/DECISION navigation;
* human decision logic.

R2-A14 is backend/runtime provenance only.

---

# PROVIDER / MODEL RESTRICTION

Provider/model identity is explicitly OUT OF SCOPE.

Do not:

* invoke Ollama;
* invoke llama3.2:1b;
* perform model health checks;
* list models;
* generate text;
* call `/v2/chat`;
* establish provider runtime identity.

Expected result:

PROVIDER_RUNTIME_IDENTITY = NOT_INVOKED

---

# DATABASE / RAG RESTRICTION

Do not:

* open the Nusantara knowledge database;
* inspect WAL/SHM;
* modify database;
* modify RAG configuration;
* rebuild indexes;
* regenerate embeddings;
* change knowledge files.

Protected state must remain unchanged.

---

# GIT RESTRICTION

Allowed:

* git status;
* git diff;
* git diff --stat;
* git rev-parse;
* read-only repository inspection.

Forbidden:

* git reset;
* git clean;
* git checkout;
* git restore;
* git commit;
* git push;
* destructive branch operations.

Preserve all existing user work.

---

# EVIDENCE REQUIREMENTS

Create one new report-owned directory:

docs/reports/r2-a14-build-provenance-<date>-<unique-id>/

Record:

1. repository identity;
2. branch;
3. HEAD;
4. Git before/after;
5. exact application files changed;
6. exact tests created;
7. exact tests executed;
8. actual test output;
9. expected build definition;
10. expected build identity;
11. observed loaded provenance;
12. process identity;
13. runtime instance identity;
14. active-process-build assessment;
15. mismatch behavior;
16. missing/malformed behavior;
17. determinism evidence;
18. provider/model isolation;
19. authorization isolation;
20. protected-state safety;
21. restart requirement;
22. limitations;
23. scope violations.

Do not overwrite previous R2-A12 or R2-A13 evidence.

---

# ACCEPTANCE CRITERIA

R2-A14 may report:

PASS_SCOPED

only if the minimum provenance mechanism is actually implemented and its focused tests pass.

Otherwise report:

BLOCKED

or:

NOT_IMPLEMENTED

Do NOT manufacture PASS.

Even if the implementation is PASS_SCOPED, this does NOT authorize:

R2-A8
R2-A9
provider/model verification
/v2/chat
live runtime activation
authorization activation
Control Plane changes
RAG/database changes.

---

# REQUIRED FINAL REPORT

Return exactly this summary structure:

R2-A14 STATUS

Implementation:
PASS_SCOPED / BLOCKED / NOT_IMPLEMENTED

Build Definition:
COMPLETE / INCOMPLETE

EXPECTED_BUILD_ID:
ACTUAL VALUE

OBSERVED_LOADED_BUILD_ID:
ACTUAL VALUE / NOT_OBSERVABLE

PROCESS_IDENTITY:
VERIFIED / NOT_VERIFIED / NOT_OBSERVABLE

RUNTIME_INSTANCE_ID:
ACTUAL VALUE / NOT_OBSERVABLE

ACTIVE_PROCESS_BUILD:
VERIFIED / NOT_VERIFIED / NOT_DIRECTLY_VERIFIED

Runtime Identity:
VERIFIED / NOT_VERIFIED

Focused Tests:
ACTUAL RESULT

Provider/model:
NOT_INVOKED

Authorization:
NOT_ACTIVATED

Protected state:
UNCHANGED / VIOLATION

Git preservation:
PASS / VIOLATION

RUNTIME_RESTART_REQUIRED:
YES / NO

IMPLEMENTATION_READY_FOR_ACTIVATION:
YES / NO

Scope violations:
NONE / DETAILS

Remaining limitation:
ACTUAL TECHNICAL LIMITATION

---

# FINAL STOP CONDITION

STOP after evidence review.

Do NOT automatically continue to:

R2-A8
R2-A9
provider/model verification
/v2/chat
live runtime activation
authorization activation
Control Plane integration
RAG/database work.

Human decision is required before any activation or restart.

END OF R2-A14 DEVELOPMENT ENVELOPE
