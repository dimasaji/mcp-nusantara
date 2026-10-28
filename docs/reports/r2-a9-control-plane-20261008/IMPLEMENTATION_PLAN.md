# Conditional implementation plan — not executed

## Work panel

Objective: extend existing Control Plane with evidence-bound human decisions and backend enforcement. Baseline: R2-A8 remediation IMPLEMENTED / TESTED; live R2-A8 and Full Runtime Identity NOT_VERIFIED. Existing UI: reusable five-stage console. Existing backend: read-only projection, shared admin check, reusable audit/queue primitives, disarmed runtime permit. Risk: LEVEL C. Human Decision: YES. Live action: NOT AUTHORIZED.

First prerequisite: approve a server-established human actor/session mechanism and the ownership/lifetime of the existing AuditTrail reused in ATTESTATION, without importing NORMAL v2 owners or creating parallel audit infrastructure. Specify memory-only versus durable decision evidence, existing permitted destination if durable, and failure behavior. No credential creation or deployment is included here.

After that prerequisite and explicit implementation approval:

1. Extend source-only evidence projection with provenance-bearing R2-A8 report/test evidence and explicitly unavailable live fields. Do not call protected database digest paths for this workflow.
2. Validate server actor/session, exact subject/scope, immutable evidence digest, current runtime binding, expiry and replay for every decision. Store audit using approved existing owner. HOLD/REJECT/ABORT never arm.
3. Keep any permit in a server-only process/runtime-bound holder; never return it to the UI. Integrate arming only after audited decision succeeds. Fail closed on audit failure and stale identity/evidence. Existing permit must stay single-use without auto-rearm/retry.
4. Extend existing Review/Decision components to display separate automated test, human test, evidence, authorization and live verification states. Preserve existing UI acceptance scope separately.
5. Run isolated UI and backend tests with synthetic evidence, approved audit fixtures and mocked provider transport. Review owned diff. Stop before restart or live execution.

Exact existing candidate paths (conditional):

- `control-plane/src/human.tsx`, `acceptance.ts`, `api.ts`, `schemas.ts`
- `app/api/control_plane.py`, `app/core/control_plane_projection.py`
- `app/security/auth.py` only if human-approved identity integration requires extending its existing owner
- `app/api/runtime_verification.py` for server-only bounded bridge after prerequisites
- `app/main.py` only for approved audit/policy composition; no lifecycle operation
- `control-plane/tests/api.test.ts`, `acceptance.test.ts`, `human.test.tsx`, `ui.test.tsx`
- `tests/test_control_plane_readonly.py`, `tests/test_runtime_verification.py`

No new source file is selected until audit/session ownership is decided. Existing `app/approval/audit_trail.py` and `queue.py` are reuse targets, not a mandate to modify them. No CSS/router changes presently required. Protected/excluded: /v1/chat, /v2/chat, /v2/dev, provider/model selection and implementations, RAG/database/sidecars, configuration values, deployment/lifecycle, protected authorization/gate records, dependency manifests. No commit/reset/cleanup.

Rollback: no R2-A9 source changes exist to roll back. Future approved changes must use owned pre-change file snapshots and isolated diffs; never reset inherited worktree or touch protected state. Loading a future revision requires a separate lifecycle decision.
