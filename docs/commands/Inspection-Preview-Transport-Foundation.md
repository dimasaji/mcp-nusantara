# NUSANTARA NORMAL DEVCORE

## Inspection Preview Transport Foundation — Authorization Contract

**Date:** 2026-10-08
**Repository:** `C:\Users\dmaza\mcp-starter`
**Branch:** `codex/fullroot-control-20261007`

---

# 1. HUMAN DECISION

Target runtime profile:

```text
NORMAL
```

The purpose of this authorization is to establish the **minimum server-enforced transport** required for the Control Plane UI to request a genuine DevCore `inspection_preview`.

This authorization is separate from the previous UI-only contract because discovery proved that the existing `/v2/dev` endpoint does not itself guarantee preview-only semantics.

---

# 2. OBJECTIVE

Establish this bounded path:

```text
CONTROL PLANE
     │
     │ authenticated preview request
     ▼
NORMAL API
     │
     ▼
DEVCORE
     │
     │ preview-only
     ▼
inspection_preview
     │
     ▼
CONTROL PLANE
```

The resulting transport must guarantee that a preview request cannot silently become a general DevCore execution request.

---

# 3. AUTHORITY

## Authorized

Developer may:

* inspect existing `/v2/dev` implementation;
* inspect existing authentication mechanism;
* inspect NORMAL route composition;
* implement the minimum preview-only server boundary;
* add the minimum request/response types required;
* reuse existing authentication;
* add focused backend tests;
* add focused transport tests;
* validate that preview requests terminate before source/tool/model execution;
* update documentation/evidence;
* perform AST-only graph synchronization if required.

## Not Authorized

Developer must NOT:

* modify ATTESTATION composition;
* mount NORMAL routes into ATTESTATION;
* weaken authentication;
* create a new secret;
* expose admin credentials to frontend source;
* add a second authority source;
* modify authorization policy;
* modify RAG;
* modify provider/model;
* modify database/index/WAL/SHM;
* restart service;
* deploy;
* activate production;
* change runtime identity/provenance;
* execute arbitrary DevCore requests from the preview path;
* change `/v1/chat`;
* change `/v2/chat`;
* redesign `/v2/dev`.

---

# 4. AUTHENTICATION REQUIREMENT

The existing server-side admin authentication mechanism must be reused.

The implementation MUST NOT:

```text
store secret in frontend
hard-code token
create new credential
bypass _require_admin
accept unauthenticated preview requests
```

The Control Plane must eventually be able to authenticate using the existing supported mechanism.

If the existing frontend cannot safely receive/use the existing authentication credential without an additional credential-delivery design:

```text
STOP
REPORT GAP
DO NOT INVENT A SECRET DELIVERY MECHANISM
```

---

# 5. API DESIGN

Preferred design:

```text
POST /v2/dev/inspection-preview
```

The exact path may be adjusted only if existing project conventions make another narrowly scoped route materially safer.

Request should contain only the minimum necessary data, conceptually:

```json
{
  "session_id": "...",
  "goal": "Perbaiki RAG Nusantara"
}
```

No execution instruction should be accepted.

The preview route MUST NOT expose a generic:

```text
user_input
```

execution surface if doing so would allow arbitrary DevCore behavior.

---

# 6. SERVER-ENFORCED PREVIEW BOUNDARY

The endpoint must establish:

```text
PREVIEW_ONLY = TRUE
```

by server-side control flow.

A client must not be able to request:

```text
preview=false
execute=true
write=true
authorize=true
```

or equivalent bypass semantics.

The server determines the operation.

---

# 7. REQUIRED BEHAVIOR

For supported goals:

```text
POST inspection-preview
        ↓
DevCore goal interpretation
        ↓
inspection_preview
        ↓
HTTP response
```

The request must terminate before:

```text
source resolution
source reads
tool execution
model generation
provider invocation
database access
runtime lifecycle
write operation
```

unless an existing pure planning dependency is demonstrably required and remains within the preview-only boundary.

The implementation must follow the actual existing DevCore architecture rather than inventing a parallel planner.

---

# 8. SUPPORTED GOALS

The server must preserve the existing five reviewed DevCore goals:

```text
Perbaiki RAG Nusantara

Periksa kenapa jawaban AI kurang akurat

Buat Nusantara lebih cepat

Periksa konfigurasi provider

Cari masalah pada Developer Engine
```

Unknown engineering goals must remain:

```text
CLARIFICATION_REQUIRED
```

The transport must not broaden the finite planner into a general natural-language execution interface.

---

# 9. RESTRICTED GOALS

Examples:

```text
Restart Nusantara
Deploy Nusantara
Delete database
Reset runtime
Authorize operation
Activate provider
```

must remain:

```text
HUMAN_DECISION_REQUIRED
```

and must not execute the requested operation.

---

# 10. RESPONSE CONTRACT

The response must expose the genuine DevCore result.

Minimum:

```text
inspection_preview
```

containing the already established fields:

```text
goal
understanding
intent
target
discovery
likely_files
plan
expected_evidence
risk
write_required
runtime_required
provider_required
database_required
human_decision
next_step
```

Additional fields may be retained.

The transport must not fabricate:

```text
root_cause
evidence
file existence
risk
authorization
execution result
```

---

# 11. AUTHORIZATION SEMANTICS

This endpoint is:

```text
AUTHORIZED FOR PREVIEW REQUEST
```

It is NOT:

```text
AUTHORIZED FOR SOURCE WRITE
AUTHORIZED FOR EXECUTION
AUTHORIZED FOR RUNTIME MUTATION
AUTHORIZED FOR PROVIDER OPERATION
AUTHORIZED FOR DATABASE MUTATION
```

Existing admin authentication proves access to the endpoint; it does not convert the preview into general execution authority.

---

# 12. DEVCORE INTEGRATION

Reuse the already implemented:

```text
app/devcore/inspection.py
app/devcore/router.py
app/devcore/core.py
```

as appropriate.

Do not duplicate the planner in:

```text
v2_routes.py
```

The API layer should transport the request to the existing DevCore preview capability rather than reproduce its semantics.

---

# 13. `/v2/dev` PRESERVATION

Existing:

```text
POST /v2/dev
```

behavior must remain intact unless a minimal shared internal refactor is strictly necessary.

Do not weaken or silently alter:

* existing authentication;
* existing source inspection;
* find/list behavior;
* grounding;
* modification refusal;
* unavailable-model fallback;
* existing response fields;
* existing audit behavior.

No public `/v2/dev` redesign is authorized.

---

# 14. NORMAL COMPOSITION

The new preview transport belongs only to the intended NORMAL profile.

Explicitly:

```text
NORMAL
 └── inspection-preview transport

ATTESTATION
 └── unchanged
```

Do not:

```text
mount v2 into ATTESTATION
change evidence-only composition
change runtime profile selection
```

---

# 15. FRONTEND AUTHENTICATION BOUNDARY

This contract may inspect the existing Control Plane authentication/session mechanism sufficiently to establish how the UI will later authenticate.

It may make the minimum server-side change necessary to support that existing mechanism.

It must NOT:

* expose an admin secret in JavaScript;
* put a server token into source code;
* persist a server token in localStorage merely to make the UI work;
* introduce a second authentication system;
* weaken CORS/authentication as a shortcut.

If secure delivery of the existing credential cannot be established within current architecture:

```text
STOP
```

and report:

```text
AUTHENTICATION_DELIVERY_GAP
```

No workaround is authorized.

---

# 16. CORS / COMPOSITION

Do not modify `app/main.py` CORS or route composition merely to bypass the discovered transport boundary.

If the existing NORMAL Control Plane origin cannot communicate with the new endpoint under current configuration:

```text
STOP
REPORT
```

A separate authorization is required for any CORS/composition change.

---

# 17. TEST REQUIREMENTS

Focused tests MUST prove:

### Authentication

```text
unauthenticated → rejected
valid existing admin authentication → accepted
```

No authentication bypass.

### Preview

Supported goal:

```text
inspection_preview returned
```

### Ambiguous

```text
CLARIFICATION_REQUIRED
```

### Restricted

```text
HUMAN_DECISION_REQUIRED
```

### No execution

Use no-operation/sentinel boundaries to prove preview requests do not invoke:

```text
provider
model generation
source tools
database
runtime lifecycle
write operations
```

### Existing behavior

Run relevant existing DevCore regression tests.

No existing assertion may be weakened.

---

# 18. NEGATIVE SECURITY TESTS

At minimum test attempts resembling:

```text
preview=false
execute=true
write=true
authorize=true
restart
delete
deploy
```

and confirm they cannot turn the preview route into an execution surface.

Also test arbitrary non-template text and confirm it does not accidentally enter the general model/source-analysis path.

---

# 19. LIVE OPERATION

No live service restart is authorized.

No deployment is authorized.

No production activation is authorized.

If source tests pass while the existing process has not loaded the change:

```text
LIVE LOADED STATE = NOT_VERIFIED
```

Do not claim otherwise.

---

# 20. ACCEPTANCE CRITERIA

## PASS_SCOPED

only if:

* [ ] NORMAL-only transport established.
* [ ] Existing admin authentication reused.
* [ ] No credential bypass.
* [ ] Preview-only behavior is server-enforced.
* [ ] Supported goals return genuine `inspection_preview`.
* [ ] Ambiguous goals remain `CLARIFICATION_REQUIRED`.
* [ ] Restricted operations remain `HUMAN_DECISION_REQUIRED`.
* [ ] No provider/model generation occurs.
* [ ] No source/tool execution occurs.
* [ ] No database access/mutation occurs.
* [ ] No runtime lifecycle occurs.
* [ ] No source write occurs.
* [ ] ATTESTATION composition unchanged.
* [ ] `/v1/chat` unchanged.
* [ ] `/v2/chat` unchanged.
* [ ] Existing `/v2/dev` semantics preserved.
* [ ] Focused tests pass.
* [ ] Relevant DevCore regression passes.
* [ ] Authentication negative tests pass.
* [ ] Preview boundary negative tests pass.
* [ ] No new authority source created.
* [ ] No new secret created.
* [ ] Evidence is complete.

---

# 21. FAILURE RULE

If implementation requires any of:

```text
CORS change
ATTESTATION composition change
new authentication architecture
new credential provisioning
public API redesign
provider change
runtime change
database change
authorization change
```

then:

```text
STOP
REPORT GAP
DO NOT IMPLEMENT
```

Do not reinterpret this contract as authorization for those changes.

---

# 22. REQUIRED REPORT

Final report must state:

```text
Repository
Branch
HEAD
Profile
Endpoint
Authentication method reused
Files changed
Before/after behavior
Preview boundary evidence
Authentication evidence
Negative test evidence
DevCore regression results
Provider status
Database status
Runtime status
ATTESTATION status
Known limitations
Final status
```

Clearly distinguish:

```text
SOURCE-LEVEL VERIFIED
```

from:

```text
LIVE SERVICE VERIFIED
```

---

# 23. PRESERVATION

Preserve inherited dirty worktree.

Do not run:

```text
git reset
git clean
git checkout
git restore
```

Do not remove unrelated changes.

---

# 24. FINAL STOP

After the minimum NORMAL transport is implemented and validated:

```text
STOP
```

Do not automatically proceed to:

```text
Control Plane UI implementation
Human Review execution
Inspection execution
Source implementation
RAG repair
Provider repair
Runtime changes
R2 assurance
Gate promotion
```

The next stage will be the previously defined:

```text
inspection_preview
        ↓
Control Plane UI
```

using the now-established transport.

---

# 25. FINAL ARCHITECTURE TARGET

```text
                         HUMAN
                           │
                           ▼
                  CONTROL PLANE UI
                           │
                           │ authenticated
                           ▼
             POST /v2/dev/inspection-preview
                           │
                           ▼
                    NORMAL API
                           │
                           ▼
                       DEVCORE
                           │
                  server-enforced
                    PREVIEW ONLY
                           │
                           ▼
                 inspection_preview
                           │
                           ▼
                  CONTROL PLANE UI
                           │
                           ▼
                     HUMAN REVIEW
                           │
                           ▼
                         STOP
```

The essential invariant is:

> **The UI can request a preview, but the UI cannot turn the preview request into execution.**

---

# AUTHORIZATION DECISION

**Human decision: APPROVED**

```text
Target Profile:
NORMAL

Scope:
Minimum server-enforced inspection-preview transport

Authentication:
Reuse existing admin authentication

Write Authorization:
NONE

Runtime Authorization:
NONE

Provider Authorization:
NONE

Database Authorization:
NONE

ATTESTATION Modification:
NOT AUTHORIZED

R2 Assurance:
NOT AUTHORIZED

Next Gate:
PASS_SCOPED transport validation → Control Plane UI integration
```
