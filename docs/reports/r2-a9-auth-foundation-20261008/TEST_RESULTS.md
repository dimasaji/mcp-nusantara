# Isolated test results

Final run: FOUNDATION_FINAL_PASS.xml, **119 PASS / 0 FAIL / 0 ERROR / 0 SKIP**. Windows/Python 3.13.15. Native local IPC plus mocked provider transport and in-process ASGI only; no live HTTP service was contacted.

| Required area | Evidence |
|---|---|
| Actor/session | Native VerifiedPeer, direct IPC-to-decision, fake Actor rejected, policy/session/proof expiry checks |
| Evidence binding | Frozen Binding, detached projection, exact digest/scope/reference checks |
| Stale process/session/code | PID/start/runtime/source/config material drift and actual helper method code drift rejected |
| Expiry | Wall/monotonic review deadlines; IPC proof expiry; grant expiry at final dispatch |
| Replay/concurrency | Proof, approval, grant and execution replay rejection; overlapping execution never dispatches twice |
| Audit/queue failures | Submit/decide/consume exceptions and false result, corrupt ledger/queue, audit failure after grant/before invocation revoke |
| Abort/revoke/uncertainty | Before/after dispatch terminal state, no second invocation, late observed receipt not promoted to completed authorization |
| Final send | Successful and failed final ASGI send separated from provider observation; external-client flag stays false |
| Sensitive retention | Permit/prompt/response/error absent; bounded reason enum and redaction-safe audit round-trip |
| Protected boundary | Real guarded app boot-to-shutdown, explicit approval module allowlist, forbidden protected files/SQLite/storage owners/legacy projection |
| NORMAL | No foundation installed; existing API/router/header behavior via stub owner composition; protected source bytes retained |

Groups: foundation 39, Windows IPC 24, runtime verification 24, correlation 16, attestation 16. Historical R2-A8 175 PASS is not added to this count and is not live evidence.

Initial FOUNDATION_TESTS.xml: 56 PASS / 2 FAIL; corrected dynamic code coverage and test fixture duplicate argument. FOUNDATION_COMPOSITION_TESTS.xml: 114 PASS. FOUNDATION_FINAL_TESTS.xml: 118 PASS. FOUNDATION_ACCEPTANCE_TESTS.xml: 119 PASS. Final guard/evidence assertions verified in FOUNDATION_FINAL_PASS.xml. One inherited Starlette/httpx deprecation warning; no packages installed.
