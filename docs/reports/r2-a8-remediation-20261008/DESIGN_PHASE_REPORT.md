# R2-A8 minimum correlation remediation — discovery/design report

Date: 2026-10-08. Repository: `C:\Users\dmaza\mcp-starter`.

**Discovery/design output: COMPLETE. Implementation status: WAITING_HUMAN.**

**R2-A8 remains BLOCKED / NOT_VERIFIED. Full Runtime Identity remains NOT_VERIFIED.**

## 1. Current blockers

Live code/instance binding has not been established; full build provenance is unavailable; the internal provider receipt is not exposed in a complete application/response join; V1 generation and normal boot can access SQLite/WAL/SHM; lifecycle scripts have broader side effects. One provider generate call may follow redirects under the existing client. The full separately named R2-A8 contract was not located during pre-flight; this task does not invent one or retry pre-flight.

## 2. Root cause

Existing identifiers/context and provider receipt were implemented at different layers. Public V1 response discards receipt, while the observer fingerprints only registered code and has no provider observation. Retrieval is unconditional before generation selection and database construction happens during normal module import. Existing health, logging, session and lifecycle behavior cannot be assumed protected-state-free. HermesAgent.run does not itself generate, so a superficial Hermes invocation cannot repair the chain.

## 3. Minimum remediation

Propose a request-local immutable receipt joined to actual process/instance/scoped-code bindings, one bounded memory observation slot, final ASGI response-send evidence and one-use transport/permit. A conditional new diagnostic route on the existing application would use the genuine existing provider and unchanged selected model/snapshot without health/RAG/fallback. A protected initialization profile is necessary; a route alone is insufficient. No fake receipt or model/provider replacement is proposed.

This proposal can at most support PASS_SCOPED for the diagnostic application/provider chain. It cannot establish a full build or normal `/v1/chat`/Hermes/RAG behavior. The human must accept that scope; otherwise original R2-A8 remains blocked.

## 4. Exact proposed files

Eight files, all **proposal only**: modify `app/main.py`, `app/core/runtime_attestation.py`, `app/models/ollama.py`, `tests/test_runtime_attestation.py`; add `app/core/runtime_correlation.py`, `app/api/runtime_verification.py`, `tests/test_runtime_correlation.py`, `tests/test_runtime_verification.py`. Roles, risk and changes are itemized in IMPLEMENTATION_PLAN.md. No source/test file was edited or created here.

## 5. Architecture impact

Current V1 source/architecture is unchanged. Proposed work reuses the existing app, context, runtime-instance owner and real provider abstraction, without a new Core/Hermes or knowledge implementation. The diagnostic route/profile is an additional engineering surface and an acceptance boundary requiring review; it is not production V1 equivalence or a bypass advertised as full verification.

## 6. Security impact

New generation exposure would be disabled without an approved process-bound expiring one-use permit. It requires local host/port/origin checks, server-owned request correlation, bounded public diagnostic input, no overrides/secrets/content retention, redirect/proxy/retry restrictions and verified transport target. Loopback and freshness nonce do not authenticate human authority. The existing source has no established safe permit-arming channel; that is a human design decision before MODIFY. No security/policy change was performed.

## 7. Protected-state impact

No DB/WAL/SHM/RAG operation occurred. `/v1/chat` is unsafe for this constraint because both request retrieval and normal boot can reach SQLite schema/WAL operations. A future capability must protect import, initialization, request, response and shutdown boundaries. The diagnostic profile and actual model-daemon activity boundary require explicit acceptance. Control Plane implementation/state remains untouched.

## 8. Test strategy and design validation

Only static/source validation was performed: request-context IDs, real generate identity return, V1 projection, SQLite paths, startup effects and proposed file/requirement boundaries were traced. No pytest, ASGI call, live HTTP, health probe, model generation, service/lifecycle script or application import was executed. Historical 135 PASS is a baseline reference, not a new result.

Future isolated tests cover process/code/context joins, actual receipt validation, one-dispatch/concurrency/cancellation, redirect/proxy refusal, sensitive data exclusion, response delivery and the full protected import/init/dispatch/shutdown boundary. Requirements A–F map to CORRELATION_DESIGN.md, PROTECTED_STATE_ANALYSIS.md and LIFECYCLE_ANALYSIS.md. Static design consistency does not prove runtime safety; unresolved decisions are retained, not marked PASS.

## 9. Rollback strategy

No source rollback needed for discovery/design. A future implementation must retain owned preimages/hashes and reverse only its patch after authorization, preserving inherited changes. No Git reset/cleanup, data recovery, sidecar repair or runtime rollback is implicit. Normal runtime restoration can touch DB and needs its own authorization.

## 10. Human Decision Gate required

**WAITING_HUMAN — AUTHORIZE MINIMUM REMEDIATION IMPLEMENTATION.**

The review must accept scoped diagnostic proof, select a trusted arming channel, approve the exact inventory/provider transport extension/new route, and resolve diagnostic initialization and protected-state/daemon scope. Implementation approval does not automatically permit service loading or live verification. Refer to the explicit decisions in IMPLEMENTATION_PLAN.md.

## Evidence and stop

Required outputs are DISCOVERY.md, CORRELATION_DESIGN.md, PROTECTED_STATE_ANALYSIS.md, LIFECYCLE_ANALYSIS.md, IMPLEMENTATION_PLAN.md and this REPORT.md. Supporting source hashes/Git state/design-validation records are retained in this directory. The source/script hashes compared before/after inspection demonstrate no changes to those inspected inputs; this is not a global protected-file integrity claim.

STOP before MODIFY. No restart of PID 32796, no live request, no provider health/generation/model operation, no source/config/RAG/DB/WAL/SHM modification, no dependency installation, no Control Plane modification, no Git commit/reset/cleanup, no authorization/gate mutation and no Runtime Identity promotion.
