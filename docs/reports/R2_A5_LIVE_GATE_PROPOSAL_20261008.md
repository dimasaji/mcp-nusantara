# R2-A5 LIVE VERIFICATION GATE PROPOSAL

Date: 8 October 2026, Asia/Jakarta.
State: READINESS_INSPECTED; LIVE_GENERATION_NOT_RUN.
Overall Runtime Identity: NOT_VERIFIED.

## New read-only observation
At 2026-10-08T02:36:53.2478832Z, GET `http://127.0.0.1:8000/health` returned HTTP 200. Request ID sent and echoed: `r2-a5-readiness-9bc37abf2b5844cfbea547237acf524b`. Port 8000 owner: PID 32796.

Loaded build: `sha256:2cfc98c71f65027c56646ec8958c5c6a0fa658b9311167e2c1b4a27e714593f2`.
Current source build: `sha256:dcb61c742ce39f12458e08d4d0c9ce360bf453e0e9c5b7e08e2f37de0ae9f7cb`.

This difference is expected after the authorized source implementation without a service restart. It proves that the active service cannot be assumed to contain R2-A3 instrumentation. It is not a provider/model mismatch, a failed test, or permission to restart the service.

## Concrete proposed verification
Start one short-lived, isolated engineering harness using the current source and repository interpreter. The harness imports configuration/identity/provider owners only; it must not import `app.main`, full API modules, knowledge, workers, approval or governance owners. If required imports unexpectedly reach protected owners, STOP without issuing a model request.

Extract and execute the existing HTTP correlation middleware from its source AST in a minimal FastAPI harness. A temporary loopback listener on an OS-assigned free port exposes one harness-only verification route. It is not installed in the application or control plane. A unique client HTTP request invokes the existing `OllamaProvider.generate` against the already running local Ollama, configured model `llama3.2:1b`, with a fixed innocuous prompt and a small output limit. No MockTransport or simulated provider response may be used for this live request.

Record actual harness PID/executable/working directory, instance ID and capture time, actual listener address/port, explicitly labeled harness application identity, HTTP request ID, provider invocation ID, configured/effective/selected/payload/actual model, provider completion and truthful receipt result. Record OS process start evidence if available; never label capture time as process start time. Correlate returned receipt with the client request and listener owner. Preserve raw controlled evidence and SHA256 without secrets. Shut down only the harness-owned listener/process on completion or failure.

## Declared potential files
No application source edits.
New engineering artifacts only, under `docs/reports/r2-a5-live-20261008/`: a verification harness script, preflight/source-hash record, live receipt, console evidence, integrity record and execution report. Earlier R2-A3 and discovery artifacts remain unchanged. These are proposed; none have been created or executed by this readiness inspection.

## Limits and acceptance
- Do not invoke `/v2/chat`, restart/stop the existing service, download models, alter configuration, or access/mutate R3, DB, WAL/SHM, governance, human decisions or authorization records.
- A real model invocation is beyond the previous isolated-fixture test execution; this proposal requires a clear R2-A5 decision before dispatch.
- Harness evidence must be labeled CONTROLLED_LIVE_PROVIDER_HARNESS, never production/deployed-service verification.
- Hermes and the full application pipeline are not executed in this provider-focused harness. No claim of full Nusantara Core + Hermes verification.
- Overall Runtime Identity remains NOT_VERIFIED. A successful live receipt can support a scoped finding for the harness only; it cannot attest PID 32796 or complete R2 closure.
- Provider/model mismatch, unavailable model, missing correlation, ambiguous process ownership or any protected-surface dependency: STOP and preserve failure evidence. No repair, workaround, governance redirection or forced PASS.

## State after this continuation
Only read-only source/report inspection, fresh health GET and port ownership inspection were performed. Only this gate proposal was written. No live generation, source edit, test repetition, service restart or protected-surface operation was performed. Await a decision on the proposed harness scope.
