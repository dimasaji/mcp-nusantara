# R2 CORE RUNTIME IDENTITY EXECUTION REPORT — R2-A5

Date: 8 October 2026 (Asia/Jakarta).
Result: **PASS for one controlled live provider harness request; overall Runtime Identity NOT_VERIFIED.**
Execution stopped after the single request and harness shutdown. No retry is authorized or scheduled.

## Authorization and scope
The human explicitly authorized one actual request to local Ollama using the proposed isolated harness, with no retry on failure, application source/configuration/DB/RAG/model/provider changes, service restart, rebuild, deployment or protected-file operations. Authorization is recorded here as engineering evidence only; no authorization/governance records were edited.

Harness script and evidence were created only under this report directory. No existing application source, configuration, model/provider implementation or protected files were modified. No full application, Hermes, RAG, knowledge worker, approval or governance owners were imported. No `/v2/chat`, model inventory probe, model installation, service health request or additional model invocation was performed in this authorized execution. No Graphify rebuild/update was run.

## Actual application/process/instance
Application identity: **Nusantara R2 engineering evidence harness**, not the full service on port 8000.
Harness PID: **6728**; parent PID from Windows CIM: **39468**.
Actual loopback listener: **127.0.0.1:50715**; Windows TCP ownership matched PID 6728 before dispatch.
Runtime instance: `51d58f3ca7ea49da89f09be2c45b87ea`.
Instance captured: `2026-10-08T02:47:00.841532+00:00`.
OS process start: `2026-10-08T02:46:59.5622940Z`.
Working directory: `C:\Users\dmaza\mcp-starter`.
Loaded build: `sha256:dcb61c742ce39f12458e08d4d0c9ce360bf453e0e9c5b7e08e2f37de0ae9f7cb`.

The interpreter reports `.venv\Scripts\python.exe`; Windows CIM reports the underlying `Python313\python.exe` process image. Both values are preserved separately, not claimed to be identical paths. Complete executable attestation is not asserted.

## Actual request and provider/model evidence
One real client HTTP POST traversed the existing HTTP middleware AST in the temporary harness and called the unchanged canonical OllamaProvider.generate over a real network transport. No provider response fixture or MockTransport was used. The transport had zero retries, redirects disabled and proxy routing disabled. Persistent exclusive execution and request-attempt records prevent reuse/retry of this harness execution.

HTTP request ID: `r2-a5-92c16fd22fa94bc2ab94d5758f8fe27a`.
Provider invocation ID: `c9af458a1cff40c0a1149ff35e2d6f93`.
Provider receipt timestamp: `2026-10-08T02:47:40.582860+00:00` (**09:47:40 WIB**).
Provider: **ollama**, port **11434**, Windows-owned PID **18296**.
Configured/effective/selected/payload/provider-reported model: **llama3.2:1b**.
Provider HTTP status: **200**. Harness HTTP status: **200**.
Provider completion: **done=true**, done_reason **length**; bounded output used **8** generated tokens and **33** prompt tokens.
Provider-reported completion timestamp: `2026-10-08T02:47:44.5906043Z`.
Internal provider identity: **RUNTIME_CONFIRMED**, confirmation source **PROVIDER_RESPONSE**. Console overall result deliberately remains **NOT_VERIFIED**.

Exactly **one** provider dispatch attempt and **one** harness client request were recorded. No retry, health/inventory fallback, provider substitution or additional generation.

## Verification result
All **14/14** scoped checks passed: one dispatch; successful HTTP; sent/echoed/provider request ID agreement; request-context origin; distinct invocation ID; runtime-instance binding; PID binding; working-directory binding; build binding; provider binding; all model identities matching; completed provider response; internal provider confirmation; provider HTTP success.

OS listener/provider ownership was proven before dispatch from Windows CIM and TCP ownership records. The evidence proves this harness process executed the local provider/model request. It does not prove Hermes or the full deployed service pipeline executed it. No extra positive/negative/mismatch/stale-process request was attempted beyond the one authorized request. Prior isolated test results remain separate and were not rerun or promoted to live evidence.

## Files, integrity and protected-state limits
Engineering artifacts: verify_live_identity.py, EXECUTION_STARTED.json, SOURCE_PREFLIGHT.json, READY.json, OWNERSHIP_GO.json, REQUEST_ATTEMPT.json, LIVE_RECEIPT.json, CONSOLE_EVIDENCE.json, EXECUTION.log, INTEGRITY.json and this report.

The three previously authorized R2-A3 source/test SHA256 values matched the preflight and after the request; source_unchanged=true. Receipt and console evidence hashes are stored in INTEGRITY.json. A separate final manifest covers this report and the remaining evidence artifacts.

Provider response and generated text are recorded by SHA256 plus bounded, selected metadata; full raw response/text are not retained and cannot be reconstructed from their hashes. No prompt/response text, credential or arbitrary upstream error body is copied into the receipt. The fixed harmless prompt appears in the harness script only.

No direct R3, DB, WAL/SHM, RAG, governance, human-decision or authorization-file access/mutation was performed. Their full after-hash integrity was not checked under the retained no-touch boundary; no complete protected-state integrity claim is made. No repair, cleanup, rollback, install, configuration change, model/provider change, service restart, rebuild, deployment, commit or push.

## Shutdown and final status
The harness recorded harness_stopped=true; its owned listener was closed and the execution process completed. Existing services were not stopped or restarted. No further runtime probes or requests were issued after completion.

**Scoped live harness test: PASS.**
**Full Nusantara Core + Hermes Runtime Identity: NOT_VERIFIED.**

The main service was not invoked for generation and still has no new live proof. Full acceptance conditions, protected-surface integrity verification, human review and R2 closure are not completed by this one-request authorization. Provider-reported model identity is not cryptographic model-weight attestation.

**STOP. No automatic next gate, retry or further execution.**
