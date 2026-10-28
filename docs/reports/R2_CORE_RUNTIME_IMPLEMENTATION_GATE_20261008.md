# R2-A2 DISCOVERY / IMPLEMENTATION GATE RECORD

Date: 8 October 2026 (Asia/Jakarta).
Latest human instruction: execute the R2 Core Runtime & Developer Execution Authorization Contract.
Runtime Identity: NOT_VERIFIED. Implementation: NOT_STARTED.

## Governing boundary
Contract: `docs/commands/R2CORERUNTIME&DEVELOPER-EXECUTION-AUTHORIZATION-CONTRACT.md`.
Section 15: discovery is read-only. Section 17: implementation requires complete discovery, R2-only scope, identified minimum change, affected files and protected files. Section 36 lists `runtime identity tidak terbukti` and `request correlation tidak terbukti` as mandatory STOP conditions. The latest request to run the contract is recorded; these contract gates still apply.

The earlier instruction not to run `/v2/chat` or touch R3, DB, WAL/SHM or governance remains a protected boundary. No such operation is proposed here. This record does not grant implementation authorization or claim that the incomplete prerequisites have passed.

## Discovery outcome
Repository, process/port ownership, loaded build, health identity and Ollama inventory were captured in the preserved baseline and discovery evidence. Current source build matches loaded application build. The current application is identified at port 8000, PID 32796, with Uvicorn parent PID 26952. Ollama owns port 11434, PID 18296; inventory has `llama3.2:1b`.

The observed HTTP health request IDs are echoed correctly. They do not prove an actual provider invocation. Health returns MODEL_INVENTORY_ONLY and NOT_VERIFIED. Current process working directory and runtime instance ID are not proven. No actual generation was run. Port 8001 is Docker-owned and has no established application identity.

Source topology: Settings configuration owner -> API provider construction -> Hermes language/problem/reasoning stages -> OllamaProvider generation -> provider response -> API projection. ModelRouter/ModelGateway have existing internal binding checks, but existence of that path does not prove it serves a given HTTP request.

Root cause of the evidence gap: capture_model_identity creates a separate UUID rather than binding to current_ids().request_id; it has no process-lifetime runtime_instance_id. Provider response receipts remain internal and are not linked to an externally recorded actual HTTP generation. V2 also writes persisted policy/request audit records, so it cannot be invoked within the retained governance boundary.

## Minimum-change candidate for a later gate
Reuse the existing request context, identity receipt and structured console logger. Preserve the public response contract and all current configured/effective/selected/actual identity distinctions.

Candidate files, not approved for mutation by this record:
1. `app/core/runtime_identity.py`: capture process-lifetime identity tied to PID; retain a unique provider invocation ID separately; bind an active HTTP request ID when present and distinguish standalone invocations honestly. Capture actual working-directory evidence internally without assuming repository root is process cwd. Treat capture time as capture time, not OS process start time.
2. `app/models/ollama.py`: emit an allowlisted, sanitized generation receipt through existing console observability after provider response, with HTTP request ID, invocation ID, runtime instance, provider/model, timestamp and truthful result. Do not log prompt, response text, credentials or private paths. Preserve failure behavior and structured-generation behavior.
3. `tests/test_provider_identity.py`: isolated transport and request-context tests for correlation, concurrency, process/instance separation, absent contexts, unavailable/missing/mismatched provider/model reports, privacy and unchanged public schemas.

Files to create for a later implementation: evidence/report artifacts only, declared before execution. No new runtime endpoint, provider registry, approval mechanism or governance record is proposed. External OpenAI-compatible runtime remains outside this Ollama-focused candidate and NOT_VERIFIED.

## Protected/read-only files
R3 evidence; knowledge DBs; every WAL/SHM sidecar; control-plane content; governance, approval, authorization and human-decision state; inherited source changes; historical checkpoints and receipts. Existing API handlers, observability owners and tests are discovery references only in this execution. No rollback, repair or cleanup is proposed.

## Required verification plan, not executed
Positive request-context/provider correlation; unique invocation IDs within one HTTP request; concurrent-request isolation; stable instance identity within a process and separation across processes; missing/wrong/stale instance rejection; configured/effective/live mismatch; historical-only and inventory-only NOT_VERIFIED; unavailable provider/model; incomplete provider responses; privacy checks; API schema regression and existing focused configuration/provider suites. Fixtures must not be promoted to live proof.

A later live gate must define a lawful actual application request path that does not write protected surfaces. Updating source does not update the already running process. No service restart, production deployment, full application import, `/v2/chat`, audit redirection, protected-state mutation or test bypass is authorized by this proposal. A separate isolated provider harness would prove only its own process, not PID 32796.

## Scope expansion and limitations
Changing governance behavior, suppressing persisted audit, mutating DB/WAL/SHM, restarting/deploying the existing service, or using fixtures as current runtime proof would require a separate decision and cannot be used as a workaround. Full protected-state after-verification remains uncompleted. No fresh protected-file reads were made for this gate record.

## Changes and final status
Only this new report was created. No source implementation, tests, chat, generation, restart, R3/DB/WAL/SHM/governance access or mutation was performed in preparing it. Earlier baseline, evidence and STOP reports remain preserved.

STOP at the discovery/implementation boundary. Runtime Identity remains NOT_VERIFIED. Token availability remains unspecified and is not asserted as the stop reason. The stop follows contract prerequisites and retained protected-surface boundaries.
