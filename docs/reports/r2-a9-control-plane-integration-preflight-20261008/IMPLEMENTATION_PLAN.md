# Proposed implementation plan — Human Decision required

No step below was executed. Approval must define whether the next phase includes a bounded PENDING-only HTTP adapter or only read-only UI rendering. Native operator activation and live capabilities are excluded from both options.

## Exact minimum candidate files

| File | Proposed purpose |
|---|---|
| control-plane/src/schemas.ts | Add strict ATTESTATION schema and variant without weakening NORMAL schema. |
| control-plane/src/api.ts | Parse snapshot variants; optional explicit bounded intention call, never decision/arm/execute or automatic POST retry. |
| control-plane/src/acceptance.ts | ATTESTATION review context and server-version invalidation; preserve NORMAL UI acceptance. |
| control-plane/src/human.tsx | Reuse five stages; distinguish observation/intention/server decision and unavailable operator confirmation. |
| control-plane/src/ui.tsx | Guard engineering views by variant; truthful scoped identity and unavailable legacy details. |
| app/api/control_plane.py | Versioned ATTESTATION read projection; optional strict PENDING-only intention adapter with request guards. NORMAL branch unchanged. |
| app/approval/runtime_authorization.py | Bounded detached review/decision projection and, if authorized, atomic expected-version intention validation/deduplication. Include added helpers in scoped code coverage. Preserve private owners and live lock. |
| control-plane/tests/api.test.ts | Variant parsing, malformed/unknown inputs, snapshot errors and explicit intention calls. |
| control-plane/tests/acceptance.test.ts | Review invalidation, expiry and historical/human/server-state separation. |
| control-plane/tests/human.test.tsx | Five-stage ATTESTATION rendering, intention semantics, unavailable native confirmation, no auto-action. |
| control-plane/tests/ui.test.tsx | Variant-safe engineering views and NORMAL preservation. |
| tests/test_runtime_authorization.py | Atomic stale-context rejection, replay/capacity/concurrency and redaction-safe detached projection. |
| tests/test_runtime_verification.py | Guarded in-process ATTESTATION composition and loaded-helper coverage; no live dispatch. |
| tests/test_control_plane_attestation_binding.py (proposed new) | Isolated adapter guards/PENDING-only contract; no real-root projection or network. |

Existing router.tsx, styles.css, graph.tsx, Vite/Playwright configuration and dependency manifests need no planned change. Avoid expanding scope unless a separately reviewed concrete dependency emerges. Existing e2e can be designed around fully intercepted synthetic responses later, but its current runner starts a frontend service: do not run it under a no-start/no-live-HTTP gate.

## Sequence if separately authorized

1. Capture attributable source baseline without inherited-worktree reset or protected file digests.
2. Implement strict variant/read presentation first. Supply synthetic fixtures, never invoke NORMAL project() against the repository root to generate them.
3. Implement intention-only adapter only if explicitly approved, with exact-version atomicity, bounded deduplication/capacity and strict request guards. No trusted actor from HTTP.
4. Add scoped helper coverage and detached decision summaries; fail closed on queue/audit integrity uncertainty. Do not manufacture missing historical receipts or timestamps.
5. Run frontend unit rendering/API mocks and guarded in-process backend tests, no socket listener, HTTP network or provider invocation. Trap filesystem/SQLite/protected digest/production owners/provider network; isolate NORMAL using existing stubs or synthetic roots.
6. Review attributable diff, unchanged public paths/configuration/lifecycle and security evidence. STOP and return PASS_SCOPED/IMPLEMENTED_PARTIAL/BLOCKED/FAIL for that authorized implementation scope only.

## Required isolated cases

Malformed/unknown variants; source vs scoped vs full-build labels; absent receipt/model; isolated evidence never relabeled live; separate human and automated results; stale version and process/runtime drift; expired/wrong-scope intentions; duplicate/concurrent submissions; actor/reviewer/token injection; hostile/null/wrong-port Origin and Host; invalid body; memory exhaustion and audit/queue failure; detached immutable projection; redaction including 16-digit runs; missing policy; disabled ARM/EXECUTE after any UI action; no automatic mutation/retry; final-send observation distinct from receipt; protected-state isolation; NORMAL preservation.

## Rollback and authority

Preserve exact owned-file before snapshots and review a file-specific reversal proposal if needed. No Git reset/cleanup or inherited-worktree revert. No deployment occurred, so there is no current service rollback action. Memory-only decisions intentionally do not survive restart; do not add persistence to fix that limitation.

Next gate: **AUTHORIZE MINIMUM R2-A9 CONTROL PLANE INTEGRATION**, explicitly naming read-only versus intention-adapter scope and isolated tests. No operator provisioning, service loading/restart, live HTTP, live arming, provider generation or R2-A8 authority follows from that gate.
