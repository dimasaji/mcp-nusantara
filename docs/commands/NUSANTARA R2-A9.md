# NUSANTARA R2-A9

## CONTROL PLANE HUMAN AUTHORIZATION & LIVE VERIFICATION INTEGRATION CONTRACT

**Master Developer Engineering System AI Contract**

**Repository:** `C:\Users\dmaza\mcp-starter`
**Branch:** `codex/fullroot-control-20261007`
**Control Plane:** existing Nusantara Control Plane
**Current Backend:** existing Nusantara Core
**Phase:** R2-A9
**Risk Level:** LEVEL C — CONTROLLED HUMAN AUTHORIZATION / LIVE VERIFICATION INTEGRATION
**Implementation Mode:** INSPECT → DESIGN → MINIMUM IMPLEMENTATION → TEST → EVIDENCE → HUMAN DECISION
**Default Authorization:** DISCOVERY ONLY until this contract is explicitly authorized
**Live Generation:** NOT AUTHORIZED by this contract unless explicitly stated in the Human Decision Gate below.

---

# 1. PURPOSE

R2-A9 establishes the controlled integration between:

```text
NUSANTARA CONTROL PLANE
        ↓
EVIDENCE
        ↓
TEST
        ↓
REVIEW
        ↓
HUMAN DECISION
        ↓
CONTROLLED AUTHORIZATION
        ↓
R2-A8 LIVE VERIFICATION
```

The purpose is **not** to redesign the Control Plane.

The purpose is to make the existing Control Plane capable of:

1. displaying trustworthy engineering evidence;
2. distinguishing evidence from test results;
3. presenting human-reviewable findings;
4. recording an explicit human decision;
5. enforcing that decision through the backend;
6. optionally issuing a bounded one-use authorization for R2-A8;
7. preventing the UI itself from becoming a security boundary;
8. preserving the existing NORMAL application behavior;
9. preventing UI actions from modifying provider, model, RAG, database, configuration, or public `/v1/chat` behavior.

R2-A9 must establish:

> **Human Decision → Backend Enforcement → Bounded Action**

and never:

> **UI Button → Assumed Authorization**

---

# 2. CURRENT BASELINE

The following status is inherited and must NOT be silently changed:

```text
R2-A8 REMEDIATION
    = IMPLEMENTED / TESTED

R2-A8
    = BLOCKED / NOT_VERIFIED

FULL RUNTIME IDENTITY
    = NOT_VERIFIED

Isolated test suite
    = 175 PASS
    = 0 failures
    = 0 errors
    = 0 skipped

Live PID 32796
    = NOT RESTARTED

Live R2-A8 generation
    = NOT EXECUTED

Trusted live arming
    = NOT YET INTEGRATED

Control Plane
    = EXISTING SYSTEM
    = MUST BE PRESERVED
```

R2-A9 must not reinterpret:

```text
175 PASS
```

as:

```text
RUNTIME IDENTITY VERIFIED
```

and must not reinterpret:

```text
R2-A8 REMEDIATION IMPLEMENTED
```

as:

```text
R2-A8 LIVE VERIFICATION PASSED
```

---

# 3. CORE ENGINEERING PRINCIPLE

The system shall maintain four distinct layers.

## Layer 1 — Evidence

```text
What the system can prove.
```

Examples:

* source snapshot;
* scoped loaded code;
* runtime instance;
* PID;
* provider identity;
* model identity;
* test evidence;
* receipt;
* configuration/profile;
* timestamps.

---

## Layer 2 — Test

```text
What was actually tested.
```

Examples:

* test case;
* test method;
* expected result;
* actual result;
* PASS/FAIL;
* test scope;
* isolated/live distinction.

---

## Layer 3 — Review

```text
What the evidence and test results mean.
```

Review must distinguish:

```text
PASS
PASS_SCOPED
IMPLEMENTED
IMPLEMENTED_PARTIAL
NOT_VERIFIED
BLOCKED
FAIL
ABORTED
```

Review must never promote evidence beyond its actual scope.

---

## Layer 4 — Human Decision

```text
What the authorized human decides.
```

Allowed decisions:

```text
APPROVE
REJECT
HOLD
ABORT
```

A human decision is an authorization decision.

It is NOT evidence that the underlying technical condition is true.

---

# 4. CONTROL PLANE TARGET UX

The existing conceptual Control Plane shall remain:

```text
SYSTEM
   ↓
EVIDENCE
   ↓
TEST
   ↓
REVIEW
   ↓
DECISION
```

Do not create a second Control Plane.

Do not create a second dashboard.

Do not create a parallel governance application.

Do not replace existing navigation unless inspection proves it is required.

---

# 5. UI RESPONSIBILITIES

The UI is responsible for:

### SYSTEM

Displaying:

* runtime status;
* configuration profile;
* backend availability;
* current verification state;
* known limitations.

### EVIDENCE

Displaying:

* source snapshot;
* scoped loaded code;
* runtime instance;
* process identity;
* provider identity;
* model identity;
* receipt;
* evidence timestamp;
* evidence scope.

### TEST

Displaying:

* available test cases;
* test description;
* expected result;
* actual result;
* execution scope;
* PASS/FAIL;
* human test status.

The UI must clearly distinguish:

```text
AUTOMATED ENGINEERING TEST
```

from:

```text
HUMAN TEST CASE
```

### REVIEW

Displaying:

* evidence;
* test results;
* limitations;
* blockers;
* contract status;
* reviewer findings.

### DECISION

Allowing an authorized human to explicitly select:

```text
APPROVE
REJECT
HOLD
ABORT
```

with:

* decision reason;
* decision timestamp;
* decision subject;
* decision scope;
* current evidence reference.

---

# 6. UI MUST NOT BE THE SECURITY BOUNDARY

The following is prohibited:

```text
if UI_button == "Approve":
    allow_generation()
```

The UI shall only request a decision.

The backend must independently validate:

```text
decision identity
decision scope
decision state
evidence state
authorization state
expiration
one-use constraint
runtime state
```

The backend must reject invalid or replayed requests even if a malicious client manually calls the API.

---

# 7. HUMAN DECISION MODEL

The canonical state machine is:

```text
NOT_READY
    │
    ▼
READY_FOR_REVIEW
    │
    ▼
UNDER_REVIEW
    │
    ├───────────────┐
    ▼               ▼
 APPROVE          REJECT
    │
    │
    ▼
AUTHORIZED
    │
    ▼
ARMED
    │
    ▼
ONE-USE ACTION
    │
    ├───────────────┐
    ▼               ▼
 CONSUMED         ABORTED
```

Alternative:

```text
UNDER_REVIEW
      │
      ▼
     HOLD
      │
      ▼
 NOT_AUTHORIZED
```

No state may jump directly from:

```text
NOT_VERIFIED
```

to:

```text
VERIFIED
```

through a UI action.

---

# 8. AUTHORIZATION BOUNDARY

R2-A9 must explicitly distinguish:

```text
REVIEW
≠
APPROVAL

APPROVAL
≠
VERIFICATION

VERIFICATION
≠
RUNTIME IDENTITY

RUNTIME IDENTITY
≠
SYSTEM HEALTH
```

A human can authorize a test without the system being verified.

Example:

```text
Runtime Identity:
NOT_VERIFIED

Human Decision:
APPROVE CONTROLLED TEST
```

This is valid.

It means:

> Human authorized the controlled test despite the current verification state.

It does NOT mean:

> Runtime identity is verified.

---

# 9. R2-A8 ARMING INTEGRATION

R2-A9 may integrate with the existing R2-A8 one-use permit mechanism.

However:

### The UI must NOT directly create the permit.

The permitted architecture is:

```text
Human UI
    ↓
Decision Request
    ↓
Backend Decision Validator
    ↓
Authorization Check
    ↓
Server-Side Arm
    ↓
One-Use Permit
    ↓
R2-A8 Controlled Execution
```

The UI must never receive:

* reusable secret;
* internal permit token;
* provider credentials;
* raw transport authorization;
* model credentials;
* configuration secrets.

The permit must remain server-owned.

---

# 10. ONE-USE AUTHORIZATION REQUIREMENTS

Any live verification authorization must be:

```text
server-owned
memory-scoped
time-limited
single-use
non-replayable
non-transferable
scope-bound
```

The backend must reject:

* second execution;
* concurrent execution;
* expired authorization;
* wrong scope;
* wrong runtime instance;
* wrong decision;
* wrong evidence version;
* unauthorized client;
* malformed request.

No automatic re-arm.

No automatic retry.

No fallback.

No second generation after failure.

---

# 11. HUMAN TEST CASE MODEL

R2-A9 shall support explicit human test cases.

Example:

```text
TEST ID:
R2-A8-HUMAN-001

TITLE:
Verify Live Runtime Identity

PRECONDITION:
R2-A8 remediation is IMPLEMENTED/TESTED.

EXPECTED:
Backend exposes controlled evidence consistent with
the authorized runtime process and provider execution.

ACTION:
Human initiates the authorized controlled verification.

RESULT:
Recorded as PASS / FAIL / BLOCKED / ABORTED.

DECISION:
Human explicitly records the decision.
```

The human test result must not be synthesized from UI state.

---

# 12. TEST EXECUTION RULE

The UI may initiate a test request.

The backend must independently perform:

```text
authorization validation
↓
scope validation
↓
runtime validation
↓
permit validation
↓
execution
↓
evidence collection
↓
result generation
```

The UI only displays the returned evidence/result.

---

# 13. EVIDENCE INTEGRITY

Every displayed evidence object must have a defined provenance.

At minimum:

```text
evidence_id
evidence_type
created_at
source
scope
status
```

Where applicable:

```text
runtime_instance_id
pid
source_snapshot
scoped_loaded_code
provider_id
model
request_id
invocation_id
```

The UI must not manufacture missing fields.

If data is unavailable:

```text
NOT_AVAILABLE
```

or:

```text
NOT_VERIFIED
```

must be shown.

Never:

```text
UNKNOWN → PASS
```

through UI defaults.

---

# 14. STATUS SEMANTICS

The following meanings are mandatory.

### PASS

The exact acceptance condition has been demonstrated.

### PASS_SCOPED

Only the explicitly stated scope has been demonstrated.

### IMPLEMENTED

The engineering change exists.

### IMPLEMENTED_TESTED

The engineering change exists and isolated tests pass.

### NOT_VERIFIED

Required evidence is absent.

### BLOCKED

A known prerequisite prevents verification.

### FAIL

The acceptance condition was executed and failed.

### ABORTED

Execution was intentionally stopped before completion.

The UI must preserve these distinctions.

---

# 15. NO FALSE POSITIVE UI

The following UI patterns are prohibited:

```text
green = everything verified
```

or:

```text
175 tests passed → Runtime Verified
```

or:

```text
Approve → Verified
```

or:

```text
Backend unavailable → PASS
```

or:

```text
missing evidence → PASS
```

Status must come from backend evidence.

---

# 16. REVIEW PANEL REQUIREMENTS

The REVIEW screen should expose, at minimum:

```text
Verification Status
Evidence Status
Test Status
Authorization Status
Human Decision
Current Blockers
Scope
Timestamp
```

Example:

```text
R2-A8

Implementation:
IMPLEMENTED / TESTED

Automated Tests:
175 PASS

Live Verification:
NOT_VERIFIED

Runtime Identity:
NOT_VERIFIED

Authorization:
NOT_AUTHORIZED

Human Decision:
PENDING

Blockers:
- live process loading not proven
- live verification not executed
```

The UI must not collapse these into one PASS indicator.

---

# 17. DECISION PANEL REQUIREMENTS

The DECISION panel shall display:

```text
Decision Subject
Current Evidence
Current Status
Scope
Risk
Required Action
```

Human options:

```text
[ APPROVE ]
[ HOLD ]
[ REJECT ]
[ ABORT ]
```

Before APPROVE:

```text
Show:
- what will happen
- what will NOT happen
- whether live process restart is required
- whether live generation will occur
- whether protected state may be touched
- exact scope
- expected evidence
```

The human must be able to understand the consequence before approval.

---

# 18. APPROVAL MUST BE SPECIFIC

Do not implement generic:

```text
APPROVE SYSTEM
```

Use scoped authorization such as:

```text
APPROVE R2-A8 CONTROLLED LIVE VERIFICATION
```

Potential future scopes:

```text
APPROVE TEST ONLY
APPROVE LIVE ATTESTATION
APPROVE SINGLE GENERATION
APPROVE SERVICE RESTART
```

Each is a different authorization.

Never infer one from another.

---

# 19. NO IMPLICIT AUTHORIZATION

The following do NOT constitute approval:

* opening the page;
* viewing evidence;
* running a test;
* selecting a test case;
* closing a dialog;
* refreshing the page;
* browser navigation;
* login alone;
* previous approval;
* approval of another phase;
* historical approval;
* developer statement;
* automated test PASS.

Authorization requires an explicit current decision.

---

# 20. DECISION RECORD

A decision record should contain:

```text
decision_id
subject
scope
decision
decision_reason
decision_time
review_state
evidence_reference
test_reference
authorization_expiry
```

Do not retain sensitive prompt/output/provider secrets.

Do not store credentials.

Do not store raw generated model content unless explicitly required by a separately authorized contract.

---

# 21. NORMAL APPLICATION PRESERVATION

R2-A9 must preserve:

```text
NORMAL profile
public /v1/chat
/v2/chat
/v2/dev
RAG
SQLite
WAL/SHM
provider selection
model selection
existing configuration precedence
existing Control Plane architecture
```

No change may be made merely because it makes the UI easier.

If UI requirements conflict with runtime architecture:

```text
STOP
```

and escalate.

---

# 22. ATTESTATION PRESERVATION

R2-A9 must preserve R2-A8 distinctions:

```text
SOURCE_SNAPSHOT
≠ ACTIVE_PROCESS_BUILD

SCOPED_LOADED_CODE
≠ FULL_APPLICATION_BUILD

ISOLATED TEST PROCESS
≠ LIVE SERVICE PROCESS

PROVIDER HEALTH
≠ PROVIDER GENERATION

PROVIDER RESPONSE
≠ FINAL ASGI DELIVERY

HUMAN APPROVAL
≠ TECHNICAL VERIFICATION
```

The UI must expose these distinctions rather than hiding them.

---

# 23. UI IMPLEMENTATION RULE

Before modifying UI source:

### MUST INSPECT

1. Existing Control Plane routes.
2. Existing page/component structure.
3. Existing state management.
4. Existing API client.
5. Existing evidence projection.
6. Existing SYSTEM/EVIDENCE/TEST/REVIEW/DECISION navigation.
7. Existing styling/design system.
8. Existing tests.
9. Existing backend control-plane endpoints.
10. Existing authorization/review implementation.

Do not assume the UI must be rebuilt.

---

# 24. MINIMUM CHANGE PRINCIPLE

After inspection, Developer must determine:

```text
EXISTING COMPONENT REUSABLE?
EXISTING ROUTE REUSABLE?
EXISTING API REUSABLE?
EXISTING STATE MODEL REUSABLE?
EXISTING REVIEW UI REUSABLE?
```

Prefer:

```text
EXTEND
```

over:

```text
REBUILD
```

No framework migration.

No dependency replacement.

No CSS/system redesign.

No new frontend framework.

No unrelated refactor.

---

# 25. API CONTRACT

Any new UI/backend API must be:

```text
minimal
read-oriented by default
scope-bound
server-authorized
evidence-backed
```

Read endpoints may expose:

```text
SYSTEM
EVIDENCE
TEST
REVIEW
DECISION STATE
```

Mutation endpoints must be limited to explicitly authorized governance actions.

No endpoint may accept:

```text
provider
model
RAG profile
database
configuration
arbitrary command
arbitrary URL
arbitrary prompt
arbitrary shell command
```

as a UI-controlled authorization parameter.

---

# 26. SERVER-SIDE VALIDATION

Every decision/mutation request must be validated server-side.

Minimum checks:

```text
request validity
session/context
decision scope
current evidence
current runtime state
authorization state
expiration
replay status
```

A client must not be able to forge:

```text
APPROVED
VERIFIED
PASS
AUTHORIZED
```

by changing JSON fields.

---

# 27. AUDITABILITY

Every governance action must be attributable to:

```text
who
what
when
why
scope
evidence
result
```

If existing audit infrastructure is sufficient:

> reuse it.

Do not create a parallel audit system.

If existing audit infrastructure is insufficient:

> STOP and document the gap.

Do not silently build an audit subsystem outside this contract.

---

# 28. SECURITY REQUIREMENTS

The implementation must reject:

* remote authorization;
* arbitrary origin authorization;
* cross-scope authorization;
* replayed decision;
* expired decision;
* forged status;
* forged evidence reference;
* client-controlled provider;
* client-controlled model;
* arbitrary endpoint;
* arbitrary prompt;
* arbitrary transport target.

The UI may be visually accessible from the Control Plane, but security must remain server-side.

---

# 29. LIVE SERVICE RULE

R2-A9 does NOT automatically authorize:

```text
restart PID 32796
```

or:

```text
service/nusantara-service.ps1
```

or:

```text
scripts/start-nusantara.bat
```

or:

```text
scheduled task
```

or any other lifecycle operation.

If live service lifecycle becomes necessary:

```text
STOP
→ prepare separate Human Decision Gate
```

---

# 30. LIVE GENERATION RULE

R2-A9 itself does not automatically authorize live model generation.

If the implementation reaches the point where generation is ready:

```text
STOP
```

and present:

```text
R2-A9 LIVE EXECUTION READINESS
```

for explicit human approval.

No implicit transition:

```text
UI implemented
→ generation allowed
```

---

# 31. MASTER DEVELOPER ENGINEERING STATE MACHINE

The AI Developer must operate using:

```text
DISCOVER
   ↓
INSPECT
   ↓
CONTRACT CHECK
   ↓
ARCHITECTURE REVIEW
   ↓
PLAN
   ↓
MINIMUM MODIFY
   ↓
UNIT TEST
   ↓
INTEGRATION TEST
   ↓
VALIDATE
   ↓
EVIDENCE
   ↓
HUMAN DECISION GATE
   ↓
CHECKPOINT
   ↓
PASS / STOP
```

Never skip directly:

```text
DISCOVER → MODIFY
```

or:

```text
UI request → implementation
```

---

# 32. MASTER DEVELOPER AI SKILL

The Developer shall behave as a:

> **Master Engineering System AI**

not as a generic coding assistant.

The AI must continuously maintain five internal questions:

### Q1 — WHAT IS AUTHORIZED?

Do not implement outside the current contract.

### Q2 — WHAT IS PROVEN?

Do not turn assumptions into evidence.

### Q3 — WHAT CHANGED?

Every source change must be attributable.

### Q4 — WHAT IS THE RISK?

Identify whether the action affects:

```text
UI
backend
runtime
provider
model
database
security
authorization
lifecycle
```

### Q5 — WHAT REQUIRES HUMAN DECISION?

Never make Level C/D decisions autonomously.

---

# 33. AI BEHAVIORAL RULES

The Developer AI MUST:

```text
inspect before modify
reuse before create
prove before claim
test before promote
stop before crossing scope
```

The Developer AI MUST NOT:

```text
guess
fabricate evidence
infer PASS
silently expand scope
silently repair unrelated code
rewrite existing architecture
restart production-like service without authorization
execute live generation without authorization
```

---

# 34. WORK PANEL

Before implementation the Developer must produce:

```text
R2-A9 WORK PANEL

OBJECTIVE:
Control Plane Human Authorization & Decision integration.

CURRENT STATE:
R2-A8 remediation IMPLEMENTED / TESTED.
R2-A8 live verification NOT_VERIFIED.

UI EXISTING:
<inspection result>

BACKEND EXISTING:
<inspection result>

REUSABLE COMPONENTS:
<list>

MINIMUM CHANGES:
<list>

FILES EXPECTED:
<list>

FILES EXCLUDED:
<list>

RISK:
LEVEL C

HUMAN DECISION REQUIRED:
YES/NO

LIVE ACTION:
NOT AUTHORIZED
```

No modification before this panel is reviewed internally.

---

# 35. TEST REQUIREMENTS

At minimum test:

## UI

* evidence rendering;
* NOT_VERIFIED rendering;
* PASS_SCOPED rendering;
* BLOCKED rendering;
* human decision states;
* stale decision handling;
* refresh handling;
* duplicate submission;
* rejected authorization;
* backend unavailable.

## Backend

* unauthorized decision rejected;
* invalid scope rejected;
* expired decision rejected;
* replay rejected;
* concurrent authorization rejected;
* forged status rejected;
* forged evidence rejected;
* provider/model override rejected;
* arbitrary endpoint rejected.

## Integration

Verify:

```text
UI
 ↓
existing Control Plane API
 ↓
backend validation
 ↓
decision state
 ↓
evidence
```

without live generation unless separately authorized.

---

# 36. HUMAN TEST SEPARATION

Automated test:

```text
Machine proves behavior.
```

Human test:

```text
Human validates operational/governance behavior.
```

They must not be merged into one PASS.

Example:

```text
AUTOMATED:
175 PASS

HUMAN:
NOT_EXECUTED

RUNTIME:
NOT_VERIFIED

AUTHORIZATION:
NOT_AUTHORIZED
```

This is a valid state.

---

# 37. EVIDENCE ARTIFACTS

R2-A9 must produce, at minimum:

```text
docs/reports/r2-a9-control-plane-20261008/
```

with:

```text
PREFLIGHT.md
UI_INSPECTION.md
ARCHITECTURE_REVIEW.md
IMPLEMENTATION_PLAN.md
TEST_RESULTS.md
EVIDENCE.md
DECISION_MODEL.md
SECURITY_REVIEW.md
DIFF_REVIEW.md
REPORT.md
```

Additional artifacts only when necessary.

---

# 38. DIFF CONTROL

Before implementation:

```text
GIT STATUS
BRANCH
HEAD
INHERITED DIRTY STATE
```

After implementation:

```text
OWNED CHANGES
INHERITED CHANGES
NEW FILES
MODIFIED FILES
DELETED FILES
```

Never:

```text
git reset --hard
git clean
global rollback
unrelated cleanup
```

without separate authorization.

---

# 39. ACCEPTANCE CRITERIA

R2-A9 implementation may be classified:

### PASS_SCOPED

when:

* existing Control Plane successfully presents evidence;
* evidence/status distinctions are preserved;
* human decision is explicit;
* backend enforces decision;
* one-use authorization is server-owned;
* replay/concurrency/expiry protections work;
* no unauthorized runtime/provider/model/configuration changes occur;
* existing UI architecture is preserved;
* automated tests pass.

### IMPLEMENTED_PARTIAL

when:

* UI and decision architecture exist;
* some integration remains incomplete;
* no false verification is claimed.

### BLOCKED

when:

* existing Control Plane cannot safely support the required authorization boundary;
* backend enforcement is insufficient;
* lifecycle integration is required but unauthorized;
* evidence provenance is incomplete.

### FAIL

when:

* authorization can be bypassed;
* UI can forge verification;
* scope is silently expanded;
* protected behavior changes unexpectedly;
* security/control requirement fails.

---

# 40. ABSOLUTE STOP CONDITIONS

Immediately STOP if:

```text
existing /v1/chat changes unexpectedly
provider selection changes
model selection changes
RAG changes
SQLite/WAL/SHM changes
configuration precedence changes
Control Plane architecture requires rebuild
new dependency is required
service restart becomes necessary
live generation becomes necessary
security boundary becomes UI-only
authorization cannot be enforced server-side
evidence cannot be provenance-bound
```

Then report:

```text
BLOCKER
EVIDENCE
IMPACT
MINIMUM REQUIRED DECISION
```

---

# 41. HUMAN DECISION GATE — HDG-R2-A9-001

## Authorization Request

I authorize the Master Developer Engineering System AI to:

* inspect the existing Control Plane;
* inspect existing SYSTEM/EVIDENCE/TEST/REVIEW/DECISION implementation;
* inspect existing backend evidence and decision interfaces;
* design the minimum R2-A9 UI + Human Decision integration;
* modify only the minimum required UI/backend files after inspection;
* implement server-enforced Human Decision state;
* implement evidence/status presentation;
* implement bounded authorization integration only if already supported by the inspected architecture.

## NOT AUTHORIZED

This gate does NOT authorize:

* service restart;
* PID 32796 restart;
* live generation;
* live provider invocation;
* R2-A8 execution;
* database mutation;
* RAG modification;
* model modification;
* provider replacement;
* configuration deployment;
* Control Plane rebuild;
* dependency migration;
* arbitrary shell execution;
* destructive Git operation.

If any becomes necessary:

> STOP and request a new Human Decision Gate.

---

# 42. REQUIRED DEVELOPER RESPONSE AFTER THIS CONTRACT

After receiving this contract, the Developer MUST NOT immediately code.

First return:

```text
R2-A9 PREFLIGHT

1. Repository
2. Branch
3. HEAD
4. Existing dirty state
5. Existing Control Plane structure
6. Existing SYSTEM implementation
7. Existing EVIDENCE implementation
8. Existing TEST implementation
9. Existing REVIEW implementation
10. Existing DECISION implementation
11. Existing backend endpoints
12. Existing authorization mechanisms
13. Existing reusable components
14. Files that would need modification
15. Files explicitly protected
16. Architecture conflicts
17. Security risks
18. Human Decision required?
19. LIVE ACTION required?
20. R2-A9 recommendation
```

Then:

```text
STOP
```

unless implementation is explicitly authorized.

---

# 43. MASTER ENGINEERING COMMAND

The Developer AI shall interpret this contract as:

> **INSPECT FIRST. DO NOT BUILD A NEW UI. REUSE THE EXISTING CONTROL PLANE.**

The desired outcome is:

```text
EXISTING CONTROL PLANE
        +
TRUSTWORTHY EVIDENCE
        +
SEPARATE HUMAN TEST
        +
EXPLICIT REVIEW
        +
SERVER-ENFORCED HUMAN DECISION
        +
BOUNDED ONE-USE AUTHORIZATION
```

not:

```text
NEW DASHBOARD
+
NEW GOVERNANCE SYSTEM
+
NEW AUTHORIZATION SYSTEM
```

---

# 44. FINAL GOVERNANCE RULE

The system must always preserve this hierarchy:

```text
HUMAN
  │
  │ Decision
  ▼
CONTROL PLANE
  │
  │ Request
  ▼
BACKEND POLICY / AUTHORIZATION
  │
  │ Enforced action
  ▼
RUNTIME
  │
  ▼
PROVIDER
  │
  ▼
MODEL
  │
  ▼
EVIDENCE
  │
  └──────────────► CONTROL PLANE
```

The Control Plane **observes and requests**.

The backend **enforces**.

The runtime **executes**.

The evidence **proves what happened**.

The human **decides whether the next controlled action is authorized**.

No layer may impersonate another.

---

# 45. R2-A9 SUCCESS DEFINITION

R2-A9 is successful when the Nusantara Control Plane can truthfully answer:

> **“Apa yang diketahui sistem?”**

through EVIDENCE,

> **“Apa yang telah diuji?”**

through TEST,

> **“Apa arti hasil tersebut?”**

through REVIEW,

and:

> **“Apa yang secara eksplisit diizinkan manusia untuk dilakukan berikutnya?”**

through DECISION,

without allowing the UI to fabricate, elevate, or bypass runtime authorization.

**R2-A9 does not automatically make R2-A8 PASS.**

**R2-A9 does not automatically make Runtime Identity VERIFIED.**

**R2-A9 establishes the governed Human Decision path required before any subsequent live verification.**

**END OF R2-A9 CONTRACT**
