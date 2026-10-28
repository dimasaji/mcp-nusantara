# R2-A8 pre-flight report — 2026-10-08

**Pre-flight decision: BLOCKED / NOT_VERIFIED.**

**Final R2-A8 outcome: NOT_VERIFIED.**

**Full Nusantara Core + Hermes Runtime Identity: NOT_VERIFIED.**

Execution stopped at pre-flight. No restart, load action, live attestation HTTP request, generation, retry, fallback, health probe, remediation or status promotion was performed.

## Authorization, discovery and plan

Authority is the user's current `R2-A8 EXECUTION AUTHORIZATION`, requiring DISCOVER → INSPECT → PLAN → PRE-FLIGHT and STOP when a critical prerequisite fails. The separately named full `NUSANTARA R2-A8 — LIVE RUNTIME IDENTITY VERIFICATION AUTHORIZATION CONTRACT` was not found in the inspected repository document locations (`docs`, `docs/commands`, `docs/contracts`, `.dev/commands`). References to R2-A8 in older contracts do not supply that missing contract. This is a discovery limitation, not a claim that no copy exists anywhere on the machine.

Plan: inspect Git and existing source evidence; read OS listener/process metadata; inspect the existing lifecycle scripts and observation/generation paths; distinguish disk source evidence from actual loaded process evidence; evaluate provider correlation and protected-state safety; permit progression only if all critical prerequisites pass. Source/configuration and protected-state operations are excluded. A request is not used to work around an already-established critical blocker.

Read-only Graphify query was used for source navigation; the graph was not rebuilt. OS metadata came from Get-NetTCPConnection and Win32_Process. Lifecycle scripts were read as text, never executed. No application module was imported to manufacture process evidence, and no isolated test PID was substituted for the live PID.

## Mandatory pre-flight findings

| # | Prerequisite | Evidence and result |
| --- | --- | --- |
| 1 | Current repository/Git state | `C:\Users\dmaza\mcp-starter`; branch `codex/fullroot-control-20261007`; HEAD `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. Extensive inherited modified/untracked files remain. No commit/reset/cleanup/staging performed. See `git-status.txt`. |
| 2 | Existing live listener/process | OS listener `127.0.0.1:8000`, PID **32796**, parent **26952**. Child start `2026-10-07T18:43:49.802242+07:00` (`2026-10-07T11:43:49.802242Z`). OS executable `C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe`. Command line: `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1`. This proves listener/process metadata, not the entire loaded application build. |
| 3 | R2-A7 present in source | YES. `app/main.py` installs `app/core/runtime_attestation.py`; the source files and `tests/test_runtime_attestation.py` match the final R2-A7 recorded SHA-256 values. |
| 4 | Active process loaded R2-A7 | **NOT_VERIFIED**. Current process start precedes R2-A7 implementation and its command line has no reload option. These observations do not directly inspect loaded Python code and are not treated as proof of absence or presence. No restart or hot loading performed. |
| 5 | Existing startup/lifecycle mechanism | `service/nusantara-service.ps1`, `service/nusantara-supervisor.ps1`, `service/install-nusantara-task.ps1`, `scripts/start-nusantara.bat` exist. Scripts specify Uvicorn and repo working directory; some also start Ollama, write logs/PID files, stop old processes or register/start a scheduled task. No matching Nusantara scheduled task was returned by the read-only task-name query. The actual launcher of PID 32796 was not fully traced. Script-defined cwd is not asserted as a direct observation of the current process cwd. |
| 6 | Live attestation availability | **NOT_VERIFIED / NOT_REQUESTED**. Source declares `GET /v1/runtime/attestation`, restricted to loopback port 8000. No HTTP request was sent because critical source-level build/receipt/safety prerequisites already fail. Source presence does not prove availability on the live process. |
| 7 | Runtime instance identity | **NOT_VERIFIED for the live process**. A runtime-owned instance mechanism exists in source, but no current live instance ID was observed. Historical/isolated IDs are not reused. |
| 8 | SOURCE_SNAPSHOT | The source mechanism uses import-time `BUILD_ID` labeled `IMPORT_TIME_SOURCE_SNAPSHOT_ONLY`. Current relevant disk file hashes are recorded in `SOURCE_EVIDENCE.json`. No aggregate live source snapshot was observed. Historical R2-A7 build values are not promoted to current live evidence. |
| 9 | SCOPED_LOADED_CODE | The mechanism hashes non-transitive registered Python handlers/HTTP dispatch/identity functions. No fingerprint from PID 32796 was obtained. Existing isolated hashes are not substituted. **NOT_VERIFIED live**. |
| 10 | ACTIVE_PROCESS_BUILD directly proven | **NO / NOT_VERIFIED**. The current observation implementation explicitly returns `full_application_build_verified = false`; its manifest excludes globals, closures, assets and transitive provider dependencies. No full build artifact → current process proof is available from inspected evidence. |
| 11 | Existing generation path | `/v1/chat` in `app/api/routes.py` constructs OllamaProvider, calls provider health, executes language/core/retrieval paths, chooses local/evidence/Ollama/offline branches and projects a public response. Source contains `provider.generate` but availability or branch selection was not tested live. `/v2/chat` was not selected as a workaround. |
| 12 | Actual provider receipt correlatable | **NO complete exposed correlation**. R2-A7 returns `provider_invocation = null`, `provider_observation = NOT_OBSERVED`, `provider_receipt_exposed = false`. Internal provider identity code is not a receipt observed from the current application. Public `/v1/chat` projection does not provide the complete runtime/build/invocation/provider/model/response join. |
| 13 | One live generation safe for protected state | **NOT_ESTABLISHED**. `/v1/chat` calls `_knowledge.search_knowledge`; existing `app/knowledge/store.py` opens a regular SQLite connection and sets `PRAGMA journal_mode=WAL`. The generation path also has pre-generation health probing and alternate branches. WAL/SHM and protected-state non-mutation cannot be guaranteed through this path. No request was attempted. |

## Source traceability and critical distinctions

Inspected direct source references include:

- `app/main.py`: attestation import/installation on the existing application.
- `app/core/runtime_attestation.py`: scoped code manifest, explicit false full-build flag, null provider receipt and local-port guard.
- `app/core/runtime_identity.py`: source snapshot and runtime instance state.
- `app/api/routes.py:919`: provider health before generation; `:955`: knowledge search; `:1214`: provider generation; subsequent public projection.
- `app/knowledge/store.py:35`: SQLite connection; `:37`: WAL pragma.
- `app/models/ollama.py`: generation and health paths were inspected as source only.

The required distinctions are maintained:

```text
SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD
SCOPED_LOADED_CODE != FULL_APPLICATION_BUILD
HEALTH CHECK != ACTUAL GENERATION
SOURCE ENDPOINT != OBSERVED LIVE ENDPOINT
ISOLATED TEST PID != LIVE LISTENER PID
```

No source hash, configuration, historical health result, checkpoint status or test result was used to infer current live build/provider identity. The historical R2-A7 implementation result is used only as a disk-source hash comparison reference.

## Evidence, diff review and limitations

`SOURCE_EVIDENCE.json` retains current relevant source hashes and their R2-A7 comparison. `git-status.txt`, `HEAD.txt`, `branch.txt` and `git-diff-summary.txt` record the inherited working state. Those HEAD-relative diffs include prior tasks and are not R2-A8 modifications. This task changes only its own report/evidence documents.

Existing inaccessible report directories limit Git/file enumeration. No permissions were repaired. The initial SQLite filename search used a nonexistent `sqlite_store.py`; subsequent inspection located the actual `store.py`. No database file was opened. No protected-file checksum workaround or global integrity claim was made.

R2-A7's 135 passing isolated tests are historical engineering evidence only; no tests were rerun for this pre-flight and they do not verify PID 32796. No tool rejection required a workaround. No runtime probe was performed beyond OS listener/process metadata. Port 5173 was not targeted and Control Plane was not modified.

## Blockers and stop

1. Separately named complete R2-A8 contract not located in the inspected locations.
2. R2-A7 loading, live endpoint availability and runtime instance identity not directly established for PID 32796.
3. Full active-process build identity is not proven by the available minimum observer.
4. Actual provider receipt is not exposed for the complete correlation.
5. The existing generation path cannot guarantee protected DB/WAL/SHM non-mutation.
6. Existing lifecycle scripts have additional provider/log/process/task side effects; no script is implicitly approved for execution by this pre-flight.

**Decision: BLOCKED / NOT_VERIFIED, not READY_FOR_LIVE_VERIFICATION.**

**R2-A8 final status: NOT_VERIFIED.**

**Full Nusantara Core + Hermes Runtime Identity remains NOT_VERIFIED.**

No further action is taken. Resolving blockers, choosing a restricted lifecycle action, or adding a full-build/provider mechanism requires a separate human decision and concrete scope; no implementation, restart or remediation is performed under this blocked pre-flight. STOP for the next Human Decision Gate.
