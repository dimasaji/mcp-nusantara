# R2-A8 configuration/profile remediation — implementation report

Date: 2026-10-08. Repository: C:\Users\dmaza\mcp-starter.

**R2-A8 REMEDIATION = IMPLEMENTED / TESTED.**

**R2-A8 = BLOCKED / NOT_VERIFIED. FULL RUNTIME IDENTITY = NOT_VERIFIED.**

This is isolated engineering evidence. No PID 32796 restart, service loading, lifecycle script, live HTTP, provider health/model invocation or status promotion was performed.

## Authorization and pre-state

Authority: user-invoked attachment 04070cbe-1c69-49b5-94d0-a932386d58de/Pasted text.txt, R2-A8 REMEDIATION — CONFIGURATION/PROFILE IMPLEMENTATION AUTHORIZATION. Its digest and exact inspected preimages are recorded in PROFILE_BEFORE.json. The pre-modification inventory/rationale is PROFILE_IMPLEMENTATION_PLAN.md, also the current IMPLEMENTATION_PLAN.md. The prior design report/plan are preserved as DESIGN_PHASE_REPORT.md and DESIGN_IMPLEMENTATION_PLAN.md; remaining discovery documents are historical design evidence.

HEAD/branch: 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab, codex/fullroot-control-20261007. Inherited dirty changes were preserved. PROFILE_GIT_BEFORE.txt/PROFILE_HEAD_BEFORE.txt record pre-state. Baseline: 135 PASS in PROFILE_BASELINE.xml. No deployed configuration file/.env/environment value, registry, dependency or service script was changed; configuration schema code was expressly extended.

## Changed-file inventory and rationale

| File | Owned change |
| --- | --- |
| app/core/nusantara_config.py | Add immutable validated runtime.profile NORMAL/ATTESTATION, default NORMAL; alias through existing precedence/provenance loader |
| app/main.py | Select profile before protected API imports; diagnostics only in ATTESTATION; server-owned diagnostic request IDs |
| app/core/runtime_attestation.py | Stable canonical logical code-object fingerprint; include diagnostic/provider bindings; read-only receipt projection |
| app/models/ollama.py | Optional owned client injection; closed injected client cannot create a permissive replacement; existing default client behavior preserved |
| app/core/runtime_correlation.py | New frozen receipt/endpoint binding, expiring process-owned one-use permit, one-dispatch transport and final-send observer |
| app/api/runtime_verification.py | New conditional local diagnostic route using actual existing provider and execution_identity |
| tests/test_runtime_correlation.py | New configuration/profile, permit/concurrency, immutability and transport unit cases |
| tests/test_runtime_verification.py | New guarded boot-to-shutdown, real-provider/mock-transport integration, failure/cancellation, NORMAL composition and preservation cases |
| tests/test_runtime_attestation.py | Preserve original observer/handler tests; adapt authorized composition assertion while retaining NORMAL middleware semantics |

Five existing files modified; four created; none deleted. PROFILE_CHANGED_FILES.json contains hashes. The extra configuration-owner file is required by this newly authorized configuration architecture; the earlier eight-file proposal was not modified automatically.

app/api/routes.py, app/api/v2_routes.py, app/core/config.py, app/core/runtime_identity.py and Control Plane API/projection remain byte-identical to inspected preimages. Public /v1/chat projection and existing /v2/chat, /v2/dev, RAG/database/provider selection behavior were not edited.

## Configuration/profile evidence

settings.effective_configuration remains the single composition owner. runtime.profile follows existing file/dotenv/environment/explicit precedence and validation, with NORMAL default. Unknown profiles fail closed. No request-controlled profile/configuration/provider/model override is accepted. No parallel loader exists.

NORMAL retains full API router composition, shared snapshot, logging, public handlers, existing provider behavior and caller request-ID semantics. The new profile is additive snapshot metadata, so serialized configuration/fingerprints include it; model/provider values and selection semantics are preserved.

ATTESTATION excludes full API imports and therefore KnowledgeEngine/RAG/SQLite construction. Unsafe host/port/worker/provider/endpoint combinations fail closed. Legacy Control Plane evidence-only boot remains distinct and does not activate diagnostics. No deployed profile was activated or live process loading claimed.

## Correlation, authorization and provider transport

POST /v1/runtime/verification exists only in ATTESTATION. It accepts exactly the bounded public selector {"probe":"runtime-correlation"}, with no prompt/model/provider/options/fallback overrides. Local peer/host/port 8000 and local Origin restrictions reject remote/5173 access.

The permit starts DISARMED. Only a trusted same-process server-side grant method can issue one expiring in-memory capability, at most 120 seconds. No HTTP arm endpoint, startup auto-grant, secret configuration or persistent gate record was added. No live grant was issued. The actual operator arming integration remains a future decision.

Reservation is atomic before awaits/client creation; concurrent/duplicate/cancelled/failed attempts cannot re-arm or dispatch again. The genuine existing OllamaProvider produces its existing execution_identity. The diagnostic client disables redirects, environment proxies and retries. Its transport permits exactly one POST to the bound /api/generate origin.

Logical configured origin and actual loopback connection are recorded separately. Configured localhost HTTP is explicitly pinned to IPv4 127.0.0.1 while preserving Host/configuration identity; literal loopback is supported. Non-loopback hosts, HTTPS and base paths are rejected in this narrow profile. An IPv6-only localhost service would fail once without retry/configuration change.

The frozen receipt contains request/invocation/instance/PID, SOURCE_SNAPSHOT, SCOPED_LOADED_CODE, provider ID, endpoint identity, provider-reported actual model, start/completion timestamps, dispatch count and response observation. No prompt/generated content/capability/raw configuration/raw exception is retained. Completion/model/identity/code mismatches fail closed.

Provider-response observation differs from final successful ASGI send. The returned body cannot certify its own later delivery; a new immutable receipt records final-send success in memory afterward. Failed send does not assert delivery. external_client_observed remains false on the server.

## Build and runtime identity limits

SOURCE_SNAPSHOT remains import-time BUILD_ID. SCOPED_LOADED_CODE fingerprints actual registered Python handlers/dispatch, identity/diagnostic functions and selected provider methods. Canonical logical fields replace marshal encoding, whose string-intern representation drifted after nested ASGI execution. Code replacement is checked before/after generation.

Globals, closures, assets, included-router implementation internals, transitive/native dependencies and model weights remain outside coverage. Fingerprints remain interpreter/path-sensitive. full_application_build_verified is always false. SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD and SCOPED_LOADED_CODE != FULL_APPLICATION_BUILD. No full Hermes/RAG/normal V1 live proof is claimed.

## Tests and failure evidence

Final: **175 PASS; 0 failures/errors/skipped**, including 135 baseline and 40 new cases. PROFILE_TESTS_FINAL_PASS.xml is authoritative; PROFILE_ISOLATED_EVIDENCE.final.json and PROFILE_CONFIGURATION_CORRELATION_TRANSPORT_EVIDENCE.json contain labeled fixture evidence. One inherited Starlette/httpx deprecation warning remains; dependencies were not upgraded.

Initial 14 failures are retained in PROFILE_TESTS.xml: middleware-extraction fixture lacked a profile global, a fixture supplied an empty configuration group, and marshal fingerprints drifted on ASGI execution, denying requests before dispatch. Main middleware now reads app-owned profile with NORMAL fallback; the fixture omits the empty group; canonical logical code fields stabilize the manifest. The 170-case corrected run passed in PROFILE_TESTS_FIXED.xml.

Expanded tests had one fixture failure from FastAPI included-router wrappers (174 PASS, 1 FAIL in PROFILE_TESTS_FINAL.xml); schema-based route inspection fixed the fixture. The final 175-case suite passed. These were authorized isolated test reruns, not live retries.

Coverage verifies profile precedence/defaults; immutable receipt/endpoint; correct request/invocation/runtime/code/model joins; DISARMED/expiry/no-rearm; concurrent/cancelled/second request refusal; redirect/timeout/error/no-fallback behavior; no health/list-models; closed-client refusal; code drift; no sensitive retention; failed final-send handling; unchanged protected source; and real main ATTESTATION boot/request/provider/response/shutdown guarded against protected imports, SQLite connects, DB/WAL/SHM opens and file writes.

All HTTP/provider test calls use in-process ASGI/MockTransport. Real provider code is exercised; no real model runs. NORMAL composition tests use stub API owners to avoid DB initialization, combined with source/hash and baseline checks; they do not claim complete NORMAL end-to-end execution. Child PIDs/fixture-model are not live runtime/model evidence.

## Protected-state, diff review and post-state

No production DB/WAL/SHM was opened/hashed/repaired/migrated/deleted/copied; no RAG/model/provider state or configuration value was changed outside approved test fixtures. Guards establish the scoped application boundary, not global protected-file forensic integrity or zero internal filesystem activity in an external model daemon.

Owned diffs against exact preimages are *.owned.diff. HEAD-relative inherited changes are not attributed to remediation. Review found only declared source/test changes. Git reports the inherited terminal blank-line area in app/main.py after the new install block; no unrelated cleanup was performed. LF/CRLF and inaccessible inherited report warnings remain without ACL repair.

Required AST-only Graphify update completed: 8970 nodes, 15251 edges, 1639 communities. Derived graph outputs/backups only; no LLM/provider API. PROFILE_GRAPH_UPDATE.log records enumeration/label limits. HEAD remains 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab; post-state is PROFILE_GIT_AFTER.txt/PROFILE_HEAD_AFTER.txt. No staging/commit/reset/cleanup or gate/authorization-record promotion.

## Rollback and stop

Owned preimages/patches support separately authorized reversal only, preserving inherited work. No global restore, new-file deletion, service rollback or normal boot is implied; source restoration does not reload a process and normal initialization can touch DB.

**R2-A8 REMEDIATION = IMPLEMENTED / TESTED does not mean R2-A8 PASS or Runtime Identity VERIFIED.**

STOP. Service loading, a trusted live arming integration, protected-state/daemon/lifecycle acceptance and any live attestation/generation protocol require the next separate Human Decision Gate. PID 32796 was not restarted; no lifecycle script or live request follows this report.
