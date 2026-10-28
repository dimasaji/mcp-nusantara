# HDG-R2-A9-AUTH-002 — Isolated Windows IPC correction

**Result: PASS_SCOPED — isolated native Windows peer/process/session/server attribution.**
Date: 2026-10-08. Authority: the user's IPC FEASIBILITY CORRECTION ONLY decision. No AUTH implementation, decision binding, permit issuance or live integration is included.

**R2-A8 = BLOCKED / NOT_VERIFIED. Full Runtime Identity = NOT_VERIFIED.**

## Root cause proven

The previous test incorrectly equated subprocess.Popen.pid with the OS named-pipe client PID. On this machine, `.venv\Scripts\python.exe` is a launcher; the actual Python interpreter is a separate child process. The corrected test proves that distinction using Windows GetNamedPipeClientProcessId, GetProcessTimes, QueryFullProcessImageNameW and Toolhelp process metadata, independently of client identity claims.

| Isolated entity | OS PID | OS parent PID | Executable |
|---|---|---|---|
| Test server | 19516 | 33576 | C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe |
| Popen launcher | 41972 | 19516 | C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe |
| Actual interpreter / IPC peer | 39828 | 41972 | C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe |

Peer start FILETIME: 134359088543668605. Launcher start: 134359088543568841. Server start: 134359088536512626. Peer and server Windows session: 1; logon-session ID: 00000000:00072890. SID recorded as SHA-256 reference in ACTUAL_IPC_EVIDENCE.json rather than a credential. These are test processes, not live application PID 32796.

Worker self-report is corroborative only: the authoritative PID comes from the native pipe API, and native parent/image/start metadata establishes its relationship to the launcher. PID validation was strengthened rather than relaxed. The impersonated peer's SID/logon/session/PID/start tuple must also match the actual process primary token and explicit server policy. Client-provided reviewer/PID/session cannot establish authority.

## Minimum corrections

- `app/security/local_operator.py`: native process image/parent/start evidence; primary-token correlation; one-use IPC handshake nonce with bounded lifetime and actor/process binding; terminal invalidation on success/failure; reject client identity/credential claims; validate server challenge PID/start against native server identity.
- `tests/test_local_operator_identity.py`: corrected launcher/interpreter correlation and expanded native Windows security checks. No other application, test, UI, configuration, audit/queue, runtime permit or public route source was changed.

## Test result

IPC_FEASIBILITY.xml records **24 PASS, 0 failures, 0 errors, 0 skipped**, on Windows/Python 3.13.15. Positive attribution uses an actual child interpreter and actual OS named pipe. Native success/failure exchanges exercise policy checks, primary-token matching, server PID/start pinning, forged-claim rejection, wrong/expired nonce and terminal replay rejection. Cleanup is checked after successful exchange, policy rejection, forged claim, nonce failure and injected identity API failure.

Local-only restriction is evidenced by strict local pipe namespace validation, the native PIPE_REJECT_REMOTE_CLIENTS flag used in a real successful pipe creation, and the actual OS DACL read back from the pipe containing one allow ACE for the configured SID. Anti-squatting is tested by rejecting a second first-instance creation for the same live test pipe. No remote host or SMB-network test was performed; no broader network security claim is made.

## Security conclusion and limits

The required OS → local IPC peer → authenticated account/session → isolated server attribution is demonstrated within this scope. IPC nonce is an ephemeral handshake challenge, not an AUTH permit or human decision. Possession/control of the permitted Windows account/session does not prove physical human presence or protect against malicious code running under that same account, a hostile administrator or kernel. No shared-secret/browser-identity fallback was added.

The unintegrated adapter retains synchronous connection/read behavior; expiry rejects stale proofs but is not an I/O deadline. Do not interpret these tests as production availability, lifecycle readiness or complete service authentication approval. Failure to revert impersonation is fatal to the exchange and raises; recovery from a native RevertToSelf failure is not claimed. No live application code/build identity was observed.

See ACTUAL_IPC_EVIDENCE.json, TEST_RESULTS.md, SECURITY_REVIEW.md, DIFF_REVIEW.md, SOURCE_COMPARISON.json and owned file diffs. Repository graph was refreshed AST-only as required by AGENTS.md, with no model API. Git inherited worktree and HEAD retained.

**STOP.** No automatic continuation to AuditTrail/ApprovalQueue ownership, decision binding, DECISION → ARM → EXECUTE, UI, live arming or R2-A8. A separate human decision is required for any next phase. No authorization/gate record was promoted.
