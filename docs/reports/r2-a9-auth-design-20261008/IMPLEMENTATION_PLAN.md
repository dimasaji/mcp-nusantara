# Minimum R2-A9-AUTH implementation plan — approval required

Status: DESIGN_COMPLETE / IMPLEMENTATION_NOT_AUTHORIZED. This plan is not executable authorization. OS attribution, process-memory audit and server-only confirmations need explicit approval as a package or a human-selected alternative.

## Exact candidate source files

| File | Proposed bounded responsibility |
|---|---|
| NEW app/security/local_operator.py | Windows local IPC peer/session adapter, narrow commands, nonce handling; no general login/auth service |
| NEW scripts/r2_a9_operator.py | Trusted local review/confirmation client; no shell/restart/provider calls; no internal permit output |
| NEW app/approval/runtime_authorization.py | Single private owner reusing AuditTrail/ApprovalQueue, immutable reviews, policy/bridge, audit projections |
| app/main.py | ATTESTATION-only composition and adapter cleanup; preserve NORMAL and legacy composition |
| app/api/control_plane.py | Scoped evidence/intent/state surfaces, no HTTP-authoritative actor or bearer permit |
| app/core/control_plane_projection.py | Separate bounded R2-A8/AUTH projection without protected file access; preserve existing NORMAL projection |
| app/core/runtime_correlation.py | Terminal abort primitive and scoped final-send observation extension |
| app/api/runtime_verification.py | Include owner/adapter functions in scoped code coverage and reuse existing controller directly; no provider/path behavior replacement |

Existing audit_trail.py, queue.py, auth.py, runtime_identity.py and runtime_attestation.py should be reused unchanged if scoped composition works. Any necessary change outside this exact candidate set requires a revised plan before editing. NORMAL v2 owner is deliberately excluded.

Optional later UI presentation integration, separately approved: existing control-plane/src/{human.tsx,acceptance.ts,api.ts,schemas.ts}. No UI change is part of the proposed initial AUTH-only backend/IPC stage. If browser-only approval is required, this plan cannot satisfy it without a different identity/session decision. No new dashboard/router/CSS framework is proposed.

## Work order after explicit approval

1. Isolated OS-channel feasibility tests: actual Windows peer identity, deny rules, server identity, session matching, impersonation cleanup. No production IPC/service connection. If any cannot be proven, STOP; no shared-secret fallback.
2. Implement memory owner with existing audit/queue; canonical frozen binding, safe redacted projections, capacities, strict transitions, no production persistence.
3. Add terminal abort and controller bridge; include all new helper code in scoped manifest; retain source/full-build distinctions.
4. Add ATTESTATION-only composition and safe evidence/intent surfaces. HTTP intention is not approval. Keep existing NORMAL owners/source/configuration/public routes unchanged.
5. Validate isolated concurrency, expiry, stale evidence, process/session changes, audit failures, revoked grant and one provider dispatch through mocked transport. Do not load production app or run live generation.
6. Review owned diff and report IMPLEMENTED_PARTIAL or PASS_SCOPED only for demonstrated isolated scope. STOP for separate UI, lifecycle and live decisions.

## Tests proposed

NEW tests/test_local_operator_identity.py; NEW tests/test_runtime_authorization.py; extend tests/test_runtime_correlation.py, tests/test_runtime_verification.py, tests/test_runtime_attestation.py and tests/test_control_plane_readonly.py with synthetic roots/evidence. No real project() or production snapshot fixture generation. No dependencies installed.

Test matrix: forged reviewer/session; wrong SID/logon/server; remote IPC; nonce replay/expiry; duplicate/concurrent operations; stale material evidence/scoped code/runtime/profile; canonical binding tampering; mutable queue/audit aliasing; redaction of 16-digit runs and sensitive/deep fields; audit exceptions at every transition; HOLD/ABORT before and after grant; TTL clamp; failure before first dispatch versus uncertainty after dispatch; no automatic retry/rearm; permit absent from every response/log; ASGI final send failure; guarded imports and no filesystem/SQLite/RAG/provider health access; NORMAL baseline preservation.

Rollback: owned pre-change snapshots and patches only. No reset/cleanup/staging/commit. Restoring source does not revoke a capability in an already loaded process; future runtime abort must handle that, and lifecycle rollback needs its own human gate. In this design-only task there are no source changes to roll back.
