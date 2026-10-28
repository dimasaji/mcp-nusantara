# Evidence binding and server-owned permit bridge

## Immutable review binding

The server constructs a strict versioned object, canonical JSON with sorted keys and fixed field types, then SHA-256 hashes its bytes. Evidence version covers material content and limitations, not refresh/latency timestamps. Browser cannot submit replacement evidence, success status, runtime tuple or provider parameters.

| Binding field | Authoritative origin |
|---|---|
| schema, subject, action, exact scope | Server allowlist; each decision/arm/execute action distinct |
| evidence_id/type/source/digest and status | Bounded approved report/test artifacts, source inspection or in-process attestation; classify provenance |
| test_reference and result | Existing isolated evidence explicitly labeled historical; human result separately recorded |
| actor_ref, logon_session_ref | OS-authenticated operator channel, after human-approved policy |
| application entrypoint, target | app.main:app, 127.0.0.1:8000; 5173 is UI only |
| pid, process start time, runtime_instance_id | Current process/runtime owner and existing process metadata; no isolated PID substitution |
| source_snapshot | Existing BUILD_ID labeled IMPORT_TIME_SOURCE_SNAPSHOT_ONLY |
| scoped_loaded_code | Existing controller observer and registered scoped manifest, with declared exclusions |
| active_process_build | NOT_DIRECTLY_VERIFIED unless separately directly established |
| profile/worker policy | Existing immutable configuration owner; ATTESTATION, one worker |
| provider/endpoint/model constraints | Existing immutable configuration/controller, never client-selected; actual_model remains absent until provider receipt |
| expires_at, nonce, decision_id | Server clock and unpredictable IDs; deadline also enforced with monotonic time |

Full build remains unverified. Include new governance/actor/queue/audit helper code in scoped binding before manifest freezes; non-transitive code coverage still excludes OS libraries, globals, closures and full dependencies. Never relabel this FULL_APPLICATION_BUILD.

Proposal: each operator confirmation challenge lasts at most 60 seconds. Review approval lasts at most 120 seconds; effective expiry is the earliest of review, operator-session and permit deadlines. Server time determines expiry; UI countdown is display only. Revalidate source/evidence version, process/start time, runtime instance, scoped code, profile and endpoint/model constraints both before grant and before invocation. Missing process binding or changed code/evidence/session causes terminal rejection. No HTTP health or generation is used to validate these preconditions.

## Bridge sequence — future only

1. Browser requests review/decision intention. It cannot arm or execute. The server creates an immutable review in the existing approval queue with a service requester identity.
2. Trusted operator reads server-owned review, explicitly confirms APPROVE/REJECT/HOLD/ABORT plus reason and intended scope. Server derives actor/session independently; all claims from HTTP clients are ignored/rejected.
3. Under the governance lock validate binding, actor, nonce, expiry and queue state. Record decision using existing audit. APPROVE is not verification and does not implicitly authorize another scope.
4. A separately explicit approved arming action consumes the queue approval once, verifies audit semantics, then calls existing OneUseAuthorization.grant() exactly once. Store returned token only inside the same process owner, bound to frozen decision. No UI receipt, log or IPC response contains it. Grant failure is terminal for that review.
5. A fresh operator execution confirmation, under separately authorized live scope, is required before the server proceeds. Browser execute intent alone does nothing. Under the lock atomically claim ARMED → EXECUTION_CLAIMED, clear the token from the holder, and validate expiry/binding. Release the lock before await; call existing VerificationController.invoke(token) directly. No self-HTTP, provider health check, model override, fallback or retry.
6. Existing reserve() and transport enforce at most one invocation/dispatch. Failure before/after dispatch, cancellation or result mismatch produces terminal result; uncertainty never triggers a second generation. Audit invocation/response receipt identifiers, not prompt or generated content.

Need a future OneUseAuthorization.abort() operation: under its own lock drop digest and prevent use from DISARMED/ARMED/RESERVED states; ARMED revocation cannot rely on current finish(). An already dispatched invocation cannot be undone. Abort means no further dispatch; cancellation does not prove the provider did not receive a request. Respect lock ordering: governance owner then permit lock; no callback reversing order. No authority object may auto-grant on startup.

Execution response projection must preserve response_observed versus application_response_sent versus external_client_observed. Existing observation middleware currently watches only /v1/runtime/verification; a new Control Plane execution-response path requires explicit scoped observation integration. Direct controller invocation alone is not final delivery proof. Return receipt after generation, then mark completed ASGI send in memory; later read-only evidence may expose that fact. Never set external_client_observed from server-side send. Include request_id/invocation_id in audit joins only when actually observed.

No route, IPC channel, permit or decision was created or executed in this task. Until implementation, isolated validation and a separate live gate, all these capabilities remain proposed.
