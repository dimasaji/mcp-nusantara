# R2-A9 IMPLEMENTATION RESULT

Date: 2026-10-08. Authority: attached **NUSANTARA R2-A9 — Minimum Control Plane Implementation Contract**, WRITE-ALLOWED, ISOLATED, NON-LIVE. Result applies only to minimum UI/read-adapter/PENDING-intention integration and isolated tests.

```text
Scope: PASS (PASS_SCOPED — isolated implementation only)
ATTESTATION Adapter: PASS
NORMAL Schema Preservation: PASS
UI Presentation: PASS
NOT_VERIFIED Preservation: PASS
Human/Test Separation: PASS
Bounded Browser Intention: PASS
Stale Evidence Rejection: PASS
ARM Boundary: PASS
EXECUTE Boundary: PASS
Live IPC: NOT_IMPLEMENTED
R2-A8: BLOCKED / NOT_VERIFIED
Runtime Identity: NOT_VERIFIED
ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED
Human Decision Required: YES — before any next phase
```

## Resulting behavior

The existing snapshot API can expose ATTESTATION_FOUNDATION_V1 separately from NORMAL SystemHealth. The frontend chooses the matching parser, rejects unknown/mixed contracts and shows scoped process/source/loaded-code/evidence identity with NOT_VERIFIED and live LOCKED status. The existing five stages and routing are reused; no dashboard rebuild or historical R3 evidence is fabricated for ATTESTATION.

The browser submits only exact scope and reviewed evidence_version to the new ATTESTATION-only POST /v1/control-plane/intention. It creates PENDING, never approves authority. Strict transport/body guards reject untrusted fields. Owner locking and a second exact-version check prevent stale mutation; duplicate requests reuse one bounded review without extending expiry or adding audit. Expired/terminal contexts cannot be renewed automatically.

Human observations, historical automated results and authenticated server decisions remain distinct. Browser APPROVE/REJECT/HOLD receipts retain their old session-only NORMAL meaning. No native confirmation, operator policy activation, permit issuance, live IPC, ARM/EXECUTE route or transport activation was introduced. Existing private AuditTrail/ApprovalQueue and native decision machinery are reused unchanged. Added functions participate in scoped loaded-code coverage.

## Changed files

Existing source:

- app/api/control_plane.py
- app/approval/runtime_authorization.py
- control-plane/src/schemas.ts
- control-plane/src/api.ts
- control-plane/src/acceptance.ts
- control-plane/src/human.tsx
- control-plane/src/ui.tsx

New tests:

- tests/test_control_plane_attestation_binding.py
- control-plane/tests/attestation.test.tsx

Documentation/evidence under this report directory includes before snapshots, synthetic NORMAL fixture and helpers, source manifests/comparison, attributable IMPLEMENTATION.diff, JUnit attempts/final results, COMPOSITION_EVIDENCE.json and Git metadata. AST graph outputs/cache/backup were refreshed as required by AGENTS.md. No other monitored application source changed.

## Validation

**83 isolated tests PASS: backend 31 + frontend 52; no final failures/errors/skips. TypeScript --noEmit exit 0.** [TEST_RESULTS.md](TEST_RESULTS.md) records exact commands, contract T1–T12 coverage, retained failed attempts and warnings.

COMPOSITION_EVIDENCE.json comes from guarded app.main lifespan and in-process ASGI, not a deployed service. PID 19244 is an isolated test process, not evidence about historical/live PID 32796. Provider dispatch_count=0, provider_receipt=null, live_http=false, operator_policy=NOT_PROVISIONED, live_actions=LOCKED; no permit or IPC activation. Its scoped hash covers test guards and must not be used as a production loaded-code proof.

Source comparison: 378 existing monitored paths, 7 expected modifications, 371 unchanged, zero unexpected monitored modifications, plus 2 new tests. Exact source snapshots are not ACTIVE_PROCESS_BUILD. Git remains codex/fullroot-control-20261007 at 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab, with inherited dirty work and no staged paths.

## Protected boundaries and remaining gaps

No live HTTP, production service restart/loading/deploy, provider health probe or invocation, model generation, operator provisioning, live arming, R2-A8 execution, configuration behavior/dependency change, RAG/SQLite/WAL/SHM access or protected-file digest operation was performed. No authorization/gate record was edited or promoted. Only isolated memory PENDING test intentions were created. Public /v1/chat, /v2/chat and /v2/dev, NORMAL projection and audit ownership remain unchanged.

This phase does not provide operator provisioning, native confirmation workflow, durable decisions, runtime activation, live arming or complete runtime correlation. Browser Windows FILETIME display has a disclosed numeric precision limit; exact authority remains server-side. Same-account actor presence and broader multi-operator availability are not established. Real browser scrolling and deployed proxy/origin behavior were not tested. Details: [SECURITY_REVIEW.md](SECURITY_REVIEW.md), [DIFF_REVIEW.md](DIFF_REVIEW.md).

HDG-R2-A9-AUTH-003 remains accepted PASS_SCOPED. R2-A8 remains BLOCKED / NOT_VERIFIED; Full Runtime Identity remains NOT_VERIFIED; ACTIVE_PROCESS_BUILD remains NOT_DIRECTLY_VERIFIED. Implementation success does not promote these states.

**STOP.** Human authority remains final. Separate human decisions are required for any operator/native activation, lifecycle/loading or eventual live verification work.
