# R2-A9 Control Plane Integration — Preflight / Discovery

Date: 2026-10-08. Authority: human acceptance of HDG-R2-A9-AUTH-003 PASS_SCOPED and authorization for **Preflight/Discovery Only**.

**Preflight: COMPLETE. Existing UI integration: BLOCKED by schema, presentation and intention-transport gaps. Implementation requires a separate Human Decision.** This is an integration-readiness finding, not a change to an authorization record or engineering gate.

HDG-R2-A9-AUTH-003 remains the accepted **PASS_SCOPED** foundation. R2-A8 remains **BLOCKED / NOT_VERIFIED**. Full Runtime Identity remains **NOT_VERIFIED**. ACTIVE_PROCESS_BUILD remains **NOT_DIRECTLY_VERIFIED**.

## Findings

1. The existing ATTESTATION GET snapshot returns foundation evidence, while the frontend parser requires the historical SystemHealth schema. Required fields such as schema_version, phases, gates and governance are absent. Source inspection establishes an incompatible contract; no HTTP request or browser demonstration was performed.
2. Existing System → Evidence → Test → Review → Decision stages can be reused. Their current content reviews fourteen R3 gates and eight UI acceptance checks. Their APPROVE/REJECT/HOLD receipt is browser-session state and explicitly does not authorize R2. It must not be reinterpreted as a trusted R2 decision.
3. The foundation has a server-only PENDING intention method and a verified Windows IPC decision method. It has no HTTP intention adapter, provisioned operator policy or automatically running IPC listener. Browser JSON must never become a VerifiedPeer or authoritative reviewer.
4. The installed foundation mechanically rejects ARM/EXECUTE: its policy and isolated transport are absent. Isolated MockTransport support is test capability, not a live bridge. UI integration cannot unlock live operation.
5. ATTESTATION snapshot avoids legacy database hashing. NORMAL projection still reads protected DB/WAL/SHM bytes. Neither that projection nor its existing real-root test may be executed for this integration preflight.

## Minimum future scope

Reuse existing routes/components with a separately typed ATTESTATION evidence view. Preserve NORMAL schema and presentation. Present server evidence version and scoped identity explicitly; do not synthesize historical R3 success to satisfy UI gates. Keep human observations distinct from automated test evidence and authenticated server decisions.

A separately authorized backend adapter could accept a bounded, explicit browser intention tied to the evidence version actually reviewed. It would create PENDING only, reject stale context before mutation, and never approve, arm, execute, issue a permit or accept actor assertions. Return detached summaries only. Actual operator activation and native confirmation workflow are unresolved lifecycle requirements for a later gate, not implicit work in this proposal.

Exact proposed paths and validation sequence are in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md); security and transport conditions are in [INTEGRATION_DESIGN.md](INTEGRATION_DESIGN.md). The required twenty-point assessment is in [PREFLIGHT.md](PREFLIGHT.md).

## Evidence and limits

377 monitored files match the accepted foundation SOURCE_AFTER baseline; no changes were found before report writing. Post-report comparison is documented in SOURCE_STABILITY.json. Git remains dirty with inherited work; GIT_STATE.json includes access-warning limitations. This monitored-file check is not a complete repository or runtime build attestation.

The accepted FOUNDATION_FINAL_PASS.xml records 119 tests, zero failures/errors/skips. It was read as historical isolated evidence; **no tests were executed in this preflight**. Prior isolated PIDs and mocked provider receipts are not current live application evidence. Historical PID 32796 is not asserted to be current: no listener/process probe or runtime request was made here. Source presence does not establish that a live process loaded it.

Only discovery report artifacts were written. No source/configuration/UI modification, ARM, live HTTP, provider health check, generation, service restart/loading, dependency installation, RAG/SQLite/WAL/SHM operation, protected-file digest, Git staging/reset/cleanup/commit or R2-A8 execution was performed. No application imports or lifecycle scripts were executed. No gate/authorization record was changed.

**STOP.** Human authority remains final. Next decision may authorize minimum Control Plane implementation and isolated tests; operator provisioning, service loading, live arming and R2-A8 each remain outside this phase.
