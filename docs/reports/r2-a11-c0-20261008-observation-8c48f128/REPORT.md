# R2-A11 Phase C0 — bounded read-only observation

**Outcome: NOT_VERIFIED. The single authorized observation is complete. No gate promotion. STOP.**

## Authorization and pre-dispatch review

Human authorized at most one GET to existing http://127.0.0.1:8000/v1/runtime/attestation, with OS listener observations before/after and evidence only. Governing contract docs/commands/R2-A10 CLOSURE & R2-A11 EXECUTION CONTRACT.md and Phase A REPORT.md were re-read; references/hashes are preserved here. This authorization supersedes Phase A's prohibition only for this bounded observation, not implementation, generation or activation.

Repository root C:/Users/dmaza/mcp-starter, branch codex/fullroot-control-20261007, HEAD 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab were independently checked before dispatch. Inherited working tree preserved; staged paths empty. GIT_BEFORE.json records tracked/untracked state and inherited inaccessible historical report directory warnings. GIT_AFTER.json records unchanged HEAD/staging/tracked status. All 380 monitored source/test/script/service files remained unchanged during collection (SOURCE_STABILITY.json).

Source inspected: runtime_attestation, runtime_identity, app.main middleware/composition, runtime_verification receipt accessor/code_functions, runtime_correlation response middleware and runtime_authorization code_functions. The GET reads captured process/instance/build metadata, hashes registered in-memory code objects, and projects only an existing receipt. No provider invocation, grant, configuration load, database/sidecar digest or knowledge retrieval occurs on this handler path. Code-functions registration returns function references; it does not invoke grant/native IPC/provider functions. Receipt accessor reads memory under a lock. Response middleware only marks verification POST responses, not attestation GET.

The existing request middleware updates bounded in-memory HTTP metrics/context; HTTP server access logging may occur normally. Read-only here means no protected/domain/authorization mutation, not absence of normal observability effects. Projection is scoped to registered code symbols/hashes and metadata; it is not a full build. Collector imposed a 262144-byte response cap and ten-second socket timeout. No application import/boot was performed by the collector.

## Exact dispatch and evidence

Executed once from repository root:

```powershell
& 'C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe' -B 'docs/reports/r2-a11-c0-20261008-observation-8c48f128/observe_once.py'
```

The report-owned collector uses standard-library HTTPConnection, exactly one GET call, no automatic retry, no redirect follow, no proxy/authentication credentials. Exclusive REQUEST_ATTEMPT.json prevents rerunning it to dispatch again. OS metadata comes from Get-NetTCPConnection and Win32_Process through read-only PowerShell. Git inspection and source hashes are local; no database or sidecar was read/hashed. Report-owned collector is evidence tooling, not application implementation.

Request interval: 2026-10-08T07:41:36.340159+00:00 to 07:41:36.444768+00:00. **HTTP 200**, 4213 bytes, not truncated, application/json. X-Request-ID req_9c59310c3e504783 identifies this observation only; it is not a provider invocation ID. Exactly one request attempt; zero retries and zero additional HTTP requests. RESPONSE_RAW.txt preserves the full response text; no credential/secret fields were present requiring redaction. Its SHA-256 is 49b688161738379439805dcd879a26698f6268ab2f357339ffa8880a50295b4a. HTTP_RESULT.json preserves timing, selected non-secret headers, size and redaction metadata.

## Correlation findings

| Evidence | Result | Class / limit |
|---|---|---|
| Listener before/after | 127.0.0.1:8000, PID 33040, parent 1268 | PROCESS_OBSERVED; no process change observed |
| Start time | OS and response agree: 2026-10-08T06:30:22.561656Z | PROCESS_OBSERVED + LIVE_SERVICE; timezone/precision normalized |
| Serving-process assertion | response process_id and observed_process_id 33040, valid_for_current_process true | Correlated within this observation window |
| Runtime instance | e8e33cd84be14c7b85df4e003513fc10 | LIVE_SERVICE; same ID in correlation_readiness; only one sample, no claim of cross-request persistence |
| Working directory | C:\Users\dmaza\mcp-starter | LIVE_SERVICE-reported, not independently provided by Win32_Process |
| Executable | Python313/python.exe | OS and response agree |
| Interpreter | repository .venv/Scripts/python.exe | LIVE_SERVICE and OS launcher command line; interpreter may redirect to base executable |
| Application | Nusantara Core + Hermes API 0.1.0, app.main:app | LIVE_SERVICE assertion plus OS entrypoint command line |
| Scoped code | startup and current registered code hashes equal, loaded_code_binding MATCH | Internal scoped binding; not current-source/full-build proof |
| Source snapshot | process snapshot differs from current disk snapshot | NOT_VERIFIED for current-source association |
| Provider | provider_invocation null; NOT_OBSERVED; provider_receipt_exposed false | No provider-confirmed evidence |
| Full runtime/build | runtime_identity NOT_VERIFIED, full_application_build_verified false | No promotion |

Scoped loaded-code hash reported by the live response:

`sha256:de7d20b64ee306483de026bb7bbce24763bb64d180b42c24a961d8eac23fbf60`

Process import-time SOURCE_SNAPSHOT:

`sha256:9789c2760ba7e78a4e6c5f6c7b1a5dec775c76f362cb40bb09d39e7d377a44df`

Current disk SOURCE snapshot, computed independently using the inspected source_build_id algorithm without importing application code:

`sha256:fdc9a1e219ce55ab5957a58a31aef67a7a9a12277dabb03a1bad9b62871821ad`

These snapshots do not match. The current process cannot be presented as serving the current disk build. No restart/reload or remediation was attempted. Matching scoped code hashes show equality of this process's captured and registered code objects only; they do not close this mismatch. The 15-symbol live manifest contains no /v1/control-plane handlers or diagnostic controller functions. Current source includes such composition paths, so current R2-A9/ATTESTATION availability cannot be inferred from this response. Effective runtime profile was not explicitly exposed; do not invent it from manifest shape.

Instance capture time 2026-10-08T06:30:23.240892+00:00 follows the observed process start and precedes the request. Before/after observations occurred at 07:41:36.339133 and 07:41:37.369066 UTC. This bounds the observation window, not perpetual evidence validity. No second sample was taken. The response is an application assertion correlated to OS identity, not a cryptographically independent measurement of all loaded memory/native code. A listener transition between samples cannot be exhaustively ruled out. Raw receipt data must not be reused as fresh evidence in a future phase without that phase's authorized validation.

SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD. SCOPED_LOADED_CODE != FULL_APPLICATION_BUILD. No configured or actual model identity was observed, and no historical mock receipt fills the gap.

## Preservation and stop

New artifacts exist only in this uniquely named report directory: observe_once.py, reference hashes, Git/source observations, request ledger, raw response, HTTP metadata, process before/after, COMPARISON.json and this report. No historical evidence was overwritten. Source/test/configuration/database/WAL/SHM/policy/gate records were not modified; no protected data was read or hashed. This source-file manifest is not OS-level proof of every process side effect, and protected files were deliberately not opened for verification.

No health, snapshot, chat/generation, provider/model probe, retry, redirect follow, ARM, EXECUTE, IPC, permit creation, restart/reload/deploy, dependency installation, Git staging/commit/reset/cleanup or authorization activation occurred. No tests were rerun. Operational governance statuses were not queried or changed.

**Full Runtime Identity: NOT_VERIFIED. ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED. Provider/model correlation: NOT_VERIFIED. R2-A11 C0 result: NOT_VERIFIED due to source mismatch and absent provider/controller bindings.** The PID/start/runtime-instance observation is useful scoped evidence, not authorization or full verification. Prior R2-A9 HOLD, R2-A10 PASS_SCOPED and R2-A8 BLOCKED / NOT_VERIFIED remain unchanged.

**STOP after this report. No implementation, additional request or further phase without another explicit human decision.**
