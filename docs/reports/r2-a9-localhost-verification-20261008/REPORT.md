# R2-A9 LOCALHOST VERIFICATION RESULT

Date: 2026-10-08. Authority: attached NUSANTARA R2-A9 Localhost Control Plane Verification Contract. Read-only / non-generation / no implementation.

**Conclusion: BLOCKED. UI NOT RUNNING. The existing backend responds, but the implemented ATTESTATION integration is not established on that running process.** This is an unavailable-service/loaded-surface blocker, not a finding that the isolated implementation failed.

## Required result

```text
UI Reachability: NOT_RUNNING
Backend Reachability: PASS (existing service HTTP metadata only)
ATTESTATION Rendering: FAIL (blocked / not observed)
Evidence Version: FAIL (blocked / not observed)
Scoped Identity: FAIL (blocked / not observed)
NOT_VERIFIED Preservation: FAIL (UI verification blocked / not observed)
LOCKED State: FAIL (UI verification blocked / not observed)
SYSTEM: FAIL (not reached)
EVIDENCE: FAIL (not reached)
TEST: FAIL (not reached)
REVIEW: FAIL (not reached)
DECISION: FAIL (not reached)
Human/Test Separation: FAIL (UI verification blocked / not observed)
Browser Authorization Boundary: FAIL (UI verification blocked / not observed)
PENDING Intention: NOT_TESTED
ARM: NOT_TESTED
EXECUTE: NOT_TESTED
Live IPC: NOT_ACTIVE (none activated by this verification)
Runtime Identity: NOT_VERIFIED
ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED
R2-A8: BLOCKED / NOT_VERIFIED
Source Changes: NONE
Authorization Changes: NONE
Conclusion: BLOCKED
```

FAIL above means the required browser assertion could not be established under the unavailable/unsafe prerequisites. It does not mean a wrong status, fabricated PASS or an authorization bypass was observed. Backend reachability PASS does not prove the required snapshot adapter is loaded, callable or safe. No global IPC inventory was performed; NOT_ACTIVE describes actions in this verification, not unrelated host processes.

## Exact observations

| Check | Evidence |
|---|---|
| UI URL | http://127.0.0.1:5173/overview |
| Actual browser | Codex In-app Browser returned net::ERR_CONNECTION_REFUSED; error tab title “This site can't be reached”, text “127.0.0.1 refused to connect”. |
| UI listener | No listener on port 5173 in read-only OS inventory. |
| Existing application listener | 127.0.0.1:8000, PID 32796, parent 26952. |
| Process start | 2026-10-07T18:43:49.802242+07:00. |
| Interpreter | C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe. |
| Command line | .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1. |
| Browser backend attempt | http://127.0.0.1:8000/v1/runtime/attestation returned browser net::ERR_BLOCKED_BY_CLIENT. No security/network-policy bypass attempted. |
| Safe read-only backend GET | /v1/runtime/attestation returned HTTP 404. |
| Metadata GET | /openapi.json returned HTTP 200, title Nusantara Core + Hermes API, version 0.1.0. |
| Registered metadata paths | /v1/control-plane/snapshot present; /v1/runtime/attestation and /v1/control-plane/intention absent. See EXISTING_API_ROUTES.json. |
| Required snapshot endpoint | /v1/control-plane/snapshot was **NOT CALLED**. Metadata presence does not prove its active implementation or profile. |
| Intention endpoint | **NOT CALLED**, no PENDING submission or actor assertion sent. |
| Browser stage evidence | All five stages not reached; no application console or visible runtime status available. |

The safe GETs were performed using Invoke-WebRequest after the browser backend navigation failed. They retrieve route/response metadata only; they are not health probes, provider requests, model generation or R2-A8 execution. No second generation, fallback provider, retry or service lifecycle action occurred. HTTP evidence is retained in READ_ONLY_HTTP_EVIDENCE.json.

## Why execution stops

The new implementation is present in source, but the current registered API does not expose its attestation or intention surface. Process start predates the R2-A9 implementation. This combination does not prove a full historical build, but prevents claiming that the running process is correlated to the implemented source. ACTIVE_PROCESS_BUILD remains NOT_DIRECTLY_VERIFIED.

The existing NORMAL snapshot source invokes protected DB/WAL/SHM digest reads. Since the running profile and snapshot implementation are not proven safe, calling it would violate the contract's protected-state boundary. Starting the configured development UI would automatically request that snapshot through its existing proxy to port 8000. No UI service was started, no mocked fixture was substituted and no proxy/configuration was changed to manufacture a browser PASS.

Completing the real five-stage exercise requires a separately authorized, safe lifecycle/loading decision for the ATTESTATION backend and subsequent UI availability. This contract's limited development-UI start allowance does not authorize replacing/restarting PID 32796 or loading a new backend instance as a workaround. The contract explicitly requires STOP before live lifecycle/loading and prohibits modifying source/configuration to resolve this blocker.

## Evidence and unchanged boundaries

- PROCESS_EVIDENCE.json: read-only listener/process facts.
- BROWSER_EVIDENCE.json: exact attempted URLs and browser errors. Screenshot/console inspection unavailable because the error tab uses a data URL blocked by the browser policy; no screenshot was invented.
- READ_ONLY_HTTP_EVIDENCE.json and EXISTING_API_ROUTES.json: exact HTTP statuses and route metadata.
- SOURCE_STABILITY.json: 380 monitored source/test paths unchanged against the completed implementation baseline; documentation artifacts only were written. This is not a full build or database integrity proof.

No source/configuration edit, dependency install, service start/restart/loading, provider/model/RAG operation, SQLite/WAL/SHM access or protected-file digest, operator provisioning/IPC activation, ARM/EXECUTE, generation, authorization/gate-record mutation or R2-A8 execution was performed. Historical isolated 83-test PASS_SCOPED evidence was not reused as localhost success. Source discovery used the repository graph read-only; no graph update was necessary.

Full Runtime Identity remains NOT_VERIFIED. R2-A8 remains BLOCKED / NOT_VERIFIED. ACTIVE_PROCESS_BUILD remains NOT_DIRECTLY_VERIFIED.

**STOP. Human Decision required before lifecycle/loading or any further execution.**
