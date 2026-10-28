# HDG-R2-A9-AUTH-003 — Minimum authorization foundation

Date: 2026-10-08. **Outcome: PASS_SCOPED — implemented and isolated-tested ATTESTATION authorization foundation.** This outcome does not complete Control Plane integration or authorize live operation.

**R2-A8 remains BLOCKED / NOT_VERIFIED. Full Runtime Identity remains NOT_VERIFIED. ACTIVE_PROCESS_BUILD remains NOT_DIRECTLY_VERIFIED.** No authorization or gate record was promoted.

## Implementation

The ATTESTATION composition owns one private existing AuditTrail(path=None) and ApprovalQueue. NORMAL/v2 ownership and public routes are unchanged. The audit instance uses a projection adapter on record inputs; the existing class still supplies redaction, timestamps, locking and hash chain. No audit subsystem or persistence sink was created.

Windows IPC now passes an internal immutable VerifiedPeer capability to the backend after native account/session/process verification and a consumed IPC challenge. Client JSON cannot construct it or choose reviewer identity. The capability is revalidated against current OS process/session and server identity, expires after 30 seconds and cannot be reused for another operation. A synchronous explicit operator-channel integration method exists; composition does not create/listen on a pipe, provision an operator policy or call it automatically.

Server-generated frozen Binding and Review records retain exact scope, canonical evidence version, trusted actor/session reference after approval, server PID/start time/runtime instance, SOURCE_SNAPSHOT, SCOPED_LOADED_CODE and wall/monotonic expiry. Review creation is only a PENDING intention. Queue/audit objects remain private; projections are detached. Existing configuration is fingerprinted without exposing its values or accepting changes.

DECISION, ARM and EXECUTE are separate authenticated operations. Queue consumption and validated audit writes precede any grant. A server-only holder keeps the internal permit; no client/HTTP/log/audit response receives it. One governance lock serializes claims; dispatch remains single-use. Terminal revoke clears ARMED/RESERVED capabilities, and expiry is rechecked at actual dispatch. Any uncertain transition poisons the owner and prevents retry/rearm.

**ARM/EXECUTE are mechanically locked unless the trusted constructor receives an exact httpx.MockTransport for isolated tests.** The installed application owner receives no transport and no operator policy, so it cannot issue a live permit. There is no live-enable switch, environment alias, mutation endpoint or default grant in this implementation. A future live gate cannot be fulfilled by a browser click or this report.

The existing GET Control Plane snapshot uses a bounded in-memory foundation projection in ATTESTATION, bypassing its legacy protected database digest path. NORMAL retains the existing projection. No frontend schema/components were changed; the existing UI is not claimed compatible with this new ATTESTATION projection. Integration requires the next human gate.

New foundation, audit/queue projection, native IPC capability, validation, revoke, control-plane snapshot and operator integration functions participate in dynamic scoped loaded-code coverage. The manifest remains explicitly non-transitive and does not prove full application build, native libraries or mutable globals/instance state.

## Validation

**119 isolated tests PASS; 0 failures, 0 errors, 0 skipped.** Final evidence: FOUNDATION_FINAL_PASS.xml. Groups: 39 foundation tests, 24 native Windows IPC tests, 24 provider/mock/guarded composition tests, 16 correlation tests, 16 attestation tests. An inherited Starlette/httpx deprecation warning remains; no dependency installation occurred.

Coverage includes direct native IPC-to-backend decision, forged actor rejection, immutable/detached state, evidence/runtime/process/scoped-code drift, session/proof/review expiry, replay, wrong scope, queue/audit failure and tampering, post-grant audit failure, concurrency/dispatch uncertainty, revoke before/after dispatch, expiry immediately before dispatch, response/final-send distinction, sensitive retention, bounded memory and NORMAL preservation.

Guarded real app import/lifespan and in-process ASGI use a mock transport and synthetic inputs. They prohibit production owners, SQLite connections, protected files and file writes; the legacy projection is replaced by a trap. Only the four explicit approval package/modules are allowed. NORMAL composition uses stub API owners to avoid production storage initialization and verifies the new owner is absent. Public/configuration/provider source hashes are also retained; this is not a full live NORMAL runtime test.

Earlier test attempts are preserved: initial 58-test run had two failures (stale helper tuple and a fixture duplicate argument); dynamic coverage and fixture were corrected. Subsequent 114/118/119-test runs passed while new security checks and evidence assertions were added. The final result does not reinterpret earlier failures as PASS.

## Evidence / diff / limits

Eight owned source/test files: six existing files changed, two new. IMPLEMENTATION.diff is attributable to exact SHA-verified before snapshots; baseline reconstruction for two files was performed in reports only and verified against pre-task captured hashes. No inherited source was reset, reverted, cleaned, staged or committed. SOURCE_COMPARISON.json records all monitored source stability and unexpected-change count. Graph refresh is AST-only derived documentation, not runtime evidence.

COMPOSITION_EVIDENCE.json is explicitly ISOLATED_GUARDED_ASGI_WITH_MOCK_HTTP; its PID/model are fixtures. WINDOWS_IPC_EVIDENCE.json identifies isolated Windows test processes, never live PID 32796. No provider receipt in this phase establishes a live Ollama invocation. Memory-only audit has no durable recovery guarantee. Host-process compromise or code running as the same permitted Windows account is outside human-presence assurance. A dispatched request cannot be undone; concurrent failure/revoke terminates authority but preserves observed/uncertain receipt facts.

No live HTTP, service loading/restart/deploy, actual live arming/permit issuance, provider/model invocation, generation, RAG/database/WAL/SHM operation, configuration precedence change or public-route modification occurred.

**STOP after this phase.** No continuation to Control Plane UI, live arming or R2-A8. Separate human decisions must address UI integration, approved operator provisioning, lifecycle and any future live execution path. Human authority remains final.
