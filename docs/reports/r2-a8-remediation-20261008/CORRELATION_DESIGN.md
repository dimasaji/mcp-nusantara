# Minimum correlation design — proposal only

No mechanism below is implemented, armed, loaded or executed by this task.

## A. Live process binding

Keep attestation on `app.main:app`, target `127.0.0.1:8000`; do not introduce a second Core or a standalone harness as application proof. For a future authorized run, an external operator first identifies the OS listener PID/start/executable. An HTTP attestation must report the same PID and OS creation time, a valid current-process binding, application entrypoint and process-owned runtime instance. Bind the receipt to that same tuple and to the actual app/route/provider objects used in the request. Re-attestation can detect an intervening replacement only if explicitly allowed by that future request budget.

Add a random process-owned observation nonce and challenge echo as freshness evidence; neither is an authorization credential. The future protocol must enumerate all allowed non-generation HTTP observations separately from the exactly-one generation budget. Any missing/mismatched PID/start/instance/challenge fails closed. Same-machine malicious code/process injection and proxy impersonation are outside this limited attestation threat model; this is correlation, not a hardware/root-of-trust signature.

## B. Loaded code binding

Retain three independent fields:

| Evidence class | Mechanism | Permitted claim |
| --- | --- | --- |
| SOURCE_SNAPSHOT | Existing import-time BUILD_ID | Disk source/assets snapshot at import; never all actual loaded code |
| SCOPED_LOADED_CODE | Existing in-memory code-object manifest extended with the actual diagnostic handler/collector and bound provider methods | Only the explicitly listed current objects in this process |
| ACTIVE_PROCESS_BUILD | No complete artifact/loader provenance exists in the inspected implementation | NOT_VERIFIED; full_application_build_verified stays false |

Include actual `generate`, identity capture/confirmation, `_get_client`, `_options`, receipt emission, and selected transport/response functions where Python code objects are available. Record interpreter identity and manifest coverage/exclusions. Associate the manifest with actual function/class objects selected for the diagnostic call, not labels copied from disk. Detect registration/rebinding/code drift before reservation and after execution. Drift after dispatch yields failure evidence, never a second attempt. Non-Python implementation, globals, closure values, assets, transitive dependencies and model weights remain outside coverage. Interpreter/path-sensitive marshal hashes are not portable release build identities.

Full loaded-build provenance would require a separate artifact/import-loader design and authorization. It is not smuggled into this minimum remediation.

## C. Receipt fields and lifecycle

Use an immutable request-local receipt, then a bounded process-memory completed observation slot. Never a global mutable `last_identity` shared across concurrent requests.

| Field | Origin and validation |
| --- | --- |
| request_id | Server-owned diagnostic request context; equals provider receipt request_id and response X-Request-ID. A caller label is separate and optional, not authoritative. |
| invocation_id | Existing provider capture_model_identity, obtained from actual generate result; not invented in advance as generation proof |
| runtime_instance_id | Existing current_runtime_instance, equal in pre-attestation, provider receipt and response |
| pid / process_start_time | Current application OS metadata, correlated externally with live listener |
| source_snapshot | BUILD_ID with explicit SOURCE_SNAPSHOT evidence class; equality is necessary, not full-build proof |
| scoped_loaded_code | Frozen manifest/hash and coverage of actual bound request/provider objects, checked before/after dispatch |
| provider_id | Existing provider response identity, validated against the selected existing provider |
| actual_model | Provider-reported model only; null/mismatch cannot pass. A response label does not prove model weights. |
| timestamp | Separate request-received, dispatch/identity-capture, provider-response-received and response-sent UTC timestamps; optional monotonic ordering for elapsed time |
| response_observed | Separate provider_response_received, application_response_sent and external client_response_received evidence; never one ambiguous boolean |
| operation / completion | ACTUAL_GENERATION and existing completion identity status; health/inventory never qualifies |
| dispatch_count / outcome | Transport-confirmed 0 or 1; reservation exhaustion retained on failure/cancellation; terminal status and sanitized error category |

Do not retain prompt, generated content, request authorization values, raw configuration, secrets or user session data. A fixed reviewed public diagnostic prompt may be transient input only. The app may return a receipt-only diagnostic HTTP response; do not pretend that it is the production user response. Validate that the provider result carried a correctly typed response and derive response_observed without persisting its text.

ASGI instrumentation records application_response_sent only after successful final `http.response.body` send; construction of JSON or return from generate is insufficient. The already-returned body cannot truthfully contain proof of its own later delivery. Keep that final send observation in memory; the external verifier separately records receipt reception. Reading the final observation would require a separately budgeted read-only GET, not another generation. Disconnect/cancellation remains unconfirmed with no retry.

## D. Actual provider receipt and one-dispatch transport

Proposed conditional route: `POST /v1/runtime/verification`, installed on the same app only for an explicitly approved diagnostic capability. This new route is a human decision, not an existing safe endpoint or an authorized workaround.

Use the existing OllamaProvider and the same immutable effective configuration owner, provider/model selection and options. No direct Ollama call outside the provider. No health, tags/list-models, fallback, model override, RAG, Hermes reimplementation or audit execution. The route joins the provider's existing execution_identity with captured process/loaded-code identity, then validates every join field. The provider model must match the selected snapshot and receipt actual_model; configuration is not proof of actual invocation.

The narrow proposed provider change is optional client injection through a documented constructor argument, preserving default behavior for all existing callers. The diagnostic client is a real httpx transport, not a fake provider: redirects disabled, explicit retries zero, allowed local origin/path/method, one transport dispatch maximum, no environment proxy (`trust_env=False`), no client model/base-URL overrides. Permit localhost only if its actual connection can be proved loopback; otherwise stop rather than rewrite configuration. Reject redirects without following them. Reuse and close the injected client with clear ownership; no global provider/client mutation.

Use an atomic process-local permit: DISARMED → ARMED → RESERVED → DISPATCHED → TERMINAL. Reservation precedes any await/provider call; a concurrent/duplicate POST loses before I/O. Any timeout, error, cancellation, redirect, invalid completion, or model mismatch consumes the attempt; never automatically re-arm, retry or fall back. Restart invalidates permit/receipt state and does not authorize a new attempt.

Arming must be bound to a separately approved operator action, PID/start/instance, expiration and maximum one dispatch; network input, challenge nonce or an arbitrary X-Request-ID must not grant it. **A trusted permit injection/arming channel has not been established in the existing source.** Before implementation, the human must select and authorize that channel. No arm endpoint, credential, persistent authorization record or secret file is introduced by this design task.

## Acceptance boundary

At most PASS_SCOPED is possible for the declared application → process → scoped code → instance → diagnostic request → actual provider/model → observed response chain. Full Runtime Identity and ACTIVE_PROCESS_BUILD remain NOT_VERIFIED. An application/provider diagnostic call cannot be advertised as full Hermes/RAG or `/v1/chat` verification. If that narrower claim is unacceptable, reject this plan and keep R2-A8 blocked.
