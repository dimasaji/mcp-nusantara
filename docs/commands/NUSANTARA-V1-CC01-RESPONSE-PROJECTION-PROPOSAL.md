# NUSANTARA V1 — CC-01 RESPONSE PROJECTION PROPOSAL

**Mode:** ANALYSIS + PROPOSAL ONLY
**Scope:** V1 `/v1/chat` public response boundary
**Date:** 2026-10-06
**Risk:** HIGH
**Change authorization:** NONE
**Runtime modification:** FORBIDDEN

---

## 0. OBJECTIVE

Perform a controlled analysis of finding **CC-01** from:

* `reports/V1_CONTRACT_COMPLIANCE.json`
* `reports/NUSANTARA-V1-CONTRACT-COMPLIANCE-ADDENDUM-2026-10-06.md`

The finding is:
a
> `/v1/chat` exposes raw `gate_pipeline` containing internal reasoning, policy and memory state outside the nested public `trust` allowlist.

The objective of this command is ONLY to produce a **scoped remediation proposal**.a

This command MUST NOT implement the remediation.

---

# 1. GOVERNANCE RULES

Read before analysis:

1. `docs/contracts/NUSANTARA-ARCHITECTURE-CONTRACT-V1.md`
2. `docs/contracts/NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md`
3. `docs/contracts/NUSANTARA-RUNTIME-EXECUTION-CONTRACT-V1.md`
4. `docs/contracts/NUSANTARA-INTELLIGENCE-MODEL-CONTRACT-V1.md`
5. `docs/contracts/NUSANTARA-KNOWLEDGE-RAG-CONTRACT-V1.md`
6. `docs/contracts/NUSANTARA-AGENT-ORCHESTRATION-CONTRACT-V1.md`
7. `docs/contracts/NUSANTARA-TOOL-MCP-API-CONTRACT-V1.md`
8. `docs/contracts/NUSANTARA-TRUST-POLICY-APPROVAL-CONTRACT-V1.md`
9. `docs/audit/GATES.md`
10. `reports/V1_CONTRACT_COMPLIANCE.json`
11. `docs/audit/NUSANTARA-V1-CONTRACT-COMPLIANCE-ADDENDUM-2026-10-06.md`

The following governance constraints are mandatory:

* Evidence before acceptance.
* No silent architecture change.
* No engine replacement.
* No duplicate engine.
* No duplicate configuration authority.
* No destructive database change.
* No `/v2` modification.
* No Agent runtime implementation.
* No LangGraph implementation.
* No Graphify orchestration runtime.
* No autonomous production modification.
* No weakening security tests.
* No deletion of historical evidence.
* No reset of working tree.
* Preserve all pre-existing user changes.

---

# 2. ABSOLUTE NO-CHANGE RULE

During this command:

### DO NOT MODIFY

* `app/api/routes.py`
* `app/core/gate_integration.py`
* `app/reasoning/*`
* `app/policy/*`
* `app/memory/*`
* `app/developer_core/*`
* `app/hermes/*`
* `app/knowledge/*`
* `app/models/*`
* `app/core/config.py`
* tests
* databases
* `.env`
* Docker configuration
* `/v2`
* any existing contract
* historical reports
* historical XML evidence
* existing checkpoints

Do not perform automated formatting that changes source files.

Do not run scripts that rewrite source files.

Do not install dependencies.

Do not start a production service.

Do not modify Docker state.

---

# 3. PRESERVE WORKING TREE

First inspect:

```powershell
git status --short
```

Record the current state.

The working tree may contain legitimate pre-existing user changes.

Do NOT:

```text
git reset
git checkout
git clean
git restore
```

Do not assume HEAD is a clean checkout.

---

# 4. SOURCE ANALYSIS

Inspect the actual `/v1/chat` implementation.

Primary target:

```text
app/api/routes.py
```

Identify precisely:

* route declaration;
* `ChatRequest`;
* HermesAgent construction;
* LanguageEngine usage;
* ProblemEngine usage;
* KnowledgeEngine/RAG usage;
* TrustEngine usage;
* GateIntegration usage;
* response construction;
* `gate_pipeline`;
* `trust`;
* `developer_core`;
* memory response data;
* grounding response data;
* error response branches;
* deterministic response branches;
* Ollama response branches;
* offline response branches.

Trace:

```text
app/api/routes.py
        ↓
app/core/gate_integration.py
        ↓
app/reasoning/*
        ↓
app/policy/*
        ↓
app/memory/*
        ↓
app/developer_core/*
```

Do not modify these files.

---

# 5. CC-01 PROOF

Confirm whether the following are externally exposed:

```text
gate_pipeline.reasoning
gate_pipeline.policy
gate_pipeline.memory
developer_core.observability.policy_decision
```

Determine the exact response structure.

Pay particular attention to:

```text
reasoning.facts
reasoning.inferences
reasoning.explanation
policy
memory
```

Do not print secret values.

Do not dump environment variables.

Do not read or expose `.env` contents.

Do not expose tokens, credentials or authentication material.

The objective is structural analysis only.

---

# 6. PUBLIC VS INTERNAL CLASSIFICATION

Create a proposed classification.

Use exactly these categories:

```text
PUBLIC
INTERNAL
ADMIN/DIAGNOSTIC
REMOVE_FROM_PUBLIC_RESPONSE
```

Analyze at minimum:

### Existing response fields

* answer
* response/content
* trust
* evidence
* evidence_count
* evidence_available
* confidence
* risk_level
* requires_human
* supports_claim
* gate_pipeline
* reasoning
* policy
* memory
* developer_core
* observability
* timing/latency
* request/session identifiers
* model/provider information
* error information

Do not assume a field is public merely because it currently exists.

Do not assume a field is safe merely because it contains no secret.

---

# 7. TRUST ALLOWLIST

Preserve the existing six-field trust contract:

```text
supports_claim
confidence
risk_level
requires_human
evidence_count
evidence_available
```

Verify that:

```text
trust.issues
trust.details
```

remain excluded.

Do not change the trust schema.

Do not add hidden reasoning to trust.

Do not convert reasoning into public trust data.

---

# 8. RESPONSE PROJECTION OPTIONS

Analyze at least these options:

## Option A — Strict Public Projection

Return only explicitly approved public fields.

Example conceptual structure:

```text
{
    answer: ...,
    trust: ...,
    evidence: ...,
    approved_public_metadata: ...
}
```

Internal gate context remains server-side.

## Option B — Public + Diagnostic Projection

Public clients receive safe fields.

Diagnostic fields are available only through a separately authorized diagnostic boundary.

Do NOT implement such an endpoint.

Only analyze the architecture and security requirements.

## Option C — Compatibility Projection

Preserve compatible fields where demonstrably safe, while removing or restricting internal fields.

Analyze API/UI compatibility impact.

Do not implement compatibility behavior.

---

# 9. SECURITY ANALYSIS

Analyze risks involving:

### Reasoning

Could the following become public?

```text
facts
inferences
explanation
```

### Policy

Could policy decisions or internal policy state become public?

### Memory

Could previous session content become public?

### Developer Core

Could internal policy observability become public?

### Gate Integration

Could future internal fields automatically become exposed if raw `gate_context` continues to be serialized?

The proposal should explicitly assess the danger of:

```text
raw internal object → public response
```

versus:

```text
explicit allowlist → public response
```

---

# 10. MEMORY PRIVACY

CC-05 is related to CC-01.

Analyze whether public response projection should prevent exposure of:

```text
raw memory
historical turns
session state
internal memory metadata
```

Do NOT redesign MemoryEngine.

Do NOT implement owner binding or TTL changes.

Only document how the response boundary should protect memory.

---

# 11. DEVELOPER CORE PRIVACY

Analyze:

```text
_developer_core.runtime_snapshot()
```

Determine which portions are:

```text
PUBLIC
INTERNAL
ADMIN/DIAGNOSTIC
```

Pay special attention to:

```text
observability.policy_decision
```

Do not modify DeveloperCore.

---

# 12. API COMPATIBILITY IMPACT

Determine:

* which existing `/v1/chat` consumers could depend on `gate_pipeline`;
* whether the UI currently consumes internal fields;
* whether removing internal fields could break clients;
* whether a versioned response projection is necessary;
* whether V1 can safely tighten the response without changing endpoint semantics;
* whether documentation must distinguish internal diagnostics from public API.

Do not invent clients.

If client usage cannot be proven, mark it:

```text
NOT_PROVEN
```

Do not claim compatibility.

---

# 13. PROPOSED TARGET

Produce a concrete proposed target:

```text
/v1/chat
   |
   +-- internal execution
   |      |
   |      +-- reasoning
   |      +-- policy
   |      +-- memory
   |      +-- gate_context
   |      +-- developer observability
   |
   +-- public projection
          |
          +-- answer
          +-- trust[6 fields]
          +-- approved evidence/public metadata
```

The exact final fields must be evidence-based.

Do not invent fields unnecessarily.

---

# 14. LEAKAGE TEST PLAN

Design tests WITHOUT IMPLEMENTING THEM.

Tests should verify that public `/v1/chat` responses do not expose:

```text
gate_pipeline.reasoning
gate_pipeline.policy
gate_pipeline.memory
developer_core.observability.policy_decision
reasoning.facts
reasoning.inferences
reasoning.explanation
```

Tests should also verify that legitimate public data remains available:

```text
answer
trust
approved evidence
```

Include tests for:

* deterministic/local-rule response;
* evidence fast path;
* Ollama generation;
* offline response;
* unsupported claim;
* missing evidence;
* `requires_human`;
* policy-sensitive request;
* empty/partial gate context;
* error response.

Do not run these tests during this command unless they are read-only static analysis.

---

# 15. AUTHORIZATION / DIAGNOSTIC BOUNDARY

If diagnostic visibility is proposed, define requirements:

* authenticated caller;
* explicit authorization;
* role/scope;
* audit trail;
* no client-provided role;
* no trust/confidence used as authorization;
* no session label used as authorization;
* no raw internal state exposed to ordinary `/v1/chat`.

Do not implement authentication or diagnostic endpoints.

---

# 16. IMPLEMENTATION SCOPE PROPOSAL

The final proposal must clearly state:

### Expected source change

Preferably limited to:

```text
app/api/routes.py
```

or another already-existing response projection location if evidence shows one exists.

### Expected test change

Only security/response projection tests that are directly required.

### Forbidden changes

* engine rewrite;
* Hermes replacement;
* ModelRouter introduction;
* MemoryEngine rewrite;
* TrustEngine rewrite;
* PolicyEngine merge;
* Agent runtime;
* LangGraph;
* Graphify runtime;
* database migration;
* configuration authority;
* `/v2`.

If more files are genuinely required, list them and explain why.

Do not modify them.

---

# 17. RISK ANALYSIS

Rate:

```text
security risk
API compatibility risk
privacy risk
architecture risk
regression risk
rollback risk
```

Use:

```text
LOW
MEDIUM
HIGH
BLOCKING
```

Explain each rating.

---

# 18. ROLLBACK PLAN

Define a safe rollback plan.

Rollback must:

* restore only approved changed files;
* preserve user pre-existing changes;
* preserve database;
* preserve historical evidence;
* preserve contracts;
* preserve configuration;
* not reset working tree globally.

No rollback is executed.

---

# 19. APPROVAL GATE

The proposal MUST end with:

```text
IMPLEMENTATION AUTHORIZATION = NOT GRANTED
```

and:

```text
NEXT STEP =
Owner review
→ Impact approval
→ Explicit implementation authorization
```

Do NOT interpret running this command as implementation approval.

Do NOT modify source even if the proposed fix appears obvious.

---

# 20. OUTPUT ARTIFACTS

Create ONLY these new documentation artifacts:

```text
reports/NUSANTARA-V1-CC01-RESPONSE-PROJECTION-PROPOSAL-2026-10-06.md
reports/V1_CC01_RESPONSE_PROJECTION_PROPOSAL.json
```

Do not overwrite existing reports.

Do not overwrite existing contracts.

Do not modify historical reports.

---

# 21. JSON REQUIREMENTS

The JSON must contain:

```text
{
  "date": "...",
  "scope": "V1",
  "finding": "CC-01",
  "status": "PROPOSAL_ONLY",
  "implementation_authorized": false,

  "source_evidence": [],
  "public_fields": [],
  "internal_fields": [],
  "diagnostic_fields": [],

  "projection_options": [],
  "recommended_option": "...",

  "security_risks": [],
  "privacy_risks": [],
  "compatibility_risks": [],
  "architecture_risks": [],

  "target_projection": {},
  "leakage_test_plan": [],
  "implementation_scope": [],
  "forbidden_changes": [],

  "rollback_plan": [],
  "approval_required": true,

  "runtime_changed": false,
  "database_changed": false,
  "contracts_changed": false,
  "v2_changed": false,
  "agent_runtime_changed": false,

  "next_step": "OWNER_REVIEW_AND_APPROVAL"
}
```

Do not claim tests passed unless actually executed.

Do not claim runtime compliance.

---

# 22. FINAL VALIDATION

Before finishing, verify:

```text
git status --short
```

Confirm:

* only the two new proposal artifacts were created by this command;
* no protected source file changed;
* no tests changed;
* no database changed;
* no contract changed;
* no `/v2` changed;
* no Agent/LangGraph/Graphify runtime changed.

If any protected file changes unexpectedly:

```text
STOP
```

Do not repair it automatically.

Report the unexpected change.

---

# 23. FINAL STATUS

Print:

```text
============================================================
NUSANTARA V1 — CC-01 RESPONSE PROJECTION
============================================================

MODE:
PROPOSAL ONLY

CC-01:
HIGH / BLOCKING

RUNTIME CHANGE:
NO

SOURCE CHANGE:
NO

DATABASE CHANGE:
NO

CONTRACT CHANGE:
NO

V2 CHANGE:
NO

AGENT RUNTIME:
NOT IMPLEMENTED

IMPLEMENTATION AUTHORIZATION:
NOT GRANTED

PROPOSAL:
CREATED

NEXT STEP:
OWNER REVIEW → IMPACT ANALYSIS → APPROVAL
============================================================
```

End the command immediately after producing the proposal.

**Do not implement CC-01.**
