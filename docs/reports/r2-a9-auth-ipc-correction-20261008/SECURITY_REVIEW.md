# IPC security conclusion

PASS_SCOPED for native isolated account/session/process attribution. The adapter derives reviewer identity exclusively from OS peer impersonation and verifies the peer's actual primary process token, creation time and session. JSON identity claims are rejected; a reported worker PID is never authoritative. Server pinning uses native pipe server PID plus OS creation time, and a matching challenge tuple.

Nonce generated with secrets is process-memory-only, actor/start/session-bound, time-limited, consumed under a lock before handler, and erased terminally on any exchange result. Channel cannot be served/reopened twice. It does not arm, authorize decisions or issue generation permits.

Actual native pipe creation uses first-instance and reject-remote flags, with a restricted SID DACL. Test reads the real OS DACL and checks the actual native call flags. No connection to another host, Windows credential change, impersonated storage operation or live service occurred.

Scope limitations: no physical human-presence proof; same-account malicious processes remain within the OS account trust boundary. Policy provisioning is still explicit and unintegrated. No availability guarantee against an authenticated client stalling synchronous IPC. Native cleanup failure recovery, remote-machine negative testing, hostile OS/kernel/admin and full-process integrity are outside proven scope. No fallback weakens the identity model.

No production audit, protected state, provider/model, HTTP endpoint, Control Plane, runtime permit, NORMAL composition or authorization record is involved. This result is not authorization to deploy or enable the channel.
