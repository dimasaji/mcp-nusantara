# R2-A13 — Runtime Identity Binding

Date: 2026-10-08. Outcome: **BLOCKED**. No application implementation was performed. The existing active process cannot be directly bound to the current application build using the available evidence. Passing diagnostic tests do not satisfy acceptance criterion A or establish a new build-binding mechanism.

## Repository and preservation

Repository: `C:\Users\dmaza\mcp-starter`; branch: `codex/fullroot-control-20261007`; HEAD: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. Staging remains empty. `GIT_BEFORE.txt`, `GIT_AFTER.txt` and `GIT_COMPARISON.json` preserve the actual observations. There are no observed changes outside this new report directory. All 381 monitored existing source, test, frontend and lifecycle files have equal before/after digests (`FILES_COMPARISON.json`). Existing inaccessible report directories produced Git warnings; no permissions were repaired. This inventory is not a digest of protected state.

## New observation, separate from historical evidence

One bounded GET to `http://127.0.0.1:8000/v1/runtime/attestation` ran at 09:18:59.146623–09:18:59.266760 UTC. HTTP 200, 4213 bytes; request ID `req_2553019f7c284e06`; raw response SHA-256 `49b688161738379439805dcd879a26698f6268ab2f357339ffa8880a50295b4a`. No retry, redirect, generation, health/model query or subsequent runtime request occurred. Source inspection established that the endpoint projects in-memory identity; ordinary request metrics/access logging remain possible. This is domain read-only observation, not a claim of zero process-memory activity.

OS listener metadata before and after binds loopback port 8000 to PID **33040**, parent 1268, with process start time **2026-10-08T06:30:22.561656Z**. The endpoint reports the same PID and start time. OS image: `C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe`. Command line invokes `C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1`. The endpoint distinguishes the venv interpreter from the base OS image.

The reported working directory is the startup-captured repository directory. A current OS working directory was not independently observable; it is not used as build proof. PID/start/image consistency establishes bounded PROCESS_IDENTITY, not full build identity or protection against a compromised process.

| Identity | New result | Evidence meaning |
| --- | --- | --- |
| REPOSITORY_IDENTITY | Root/branch/HEAD observed | Git identity, not executed-code proof |
| SOURCE_BUILD_ID | `sha256:fea32d2a822f9a23a5ae8de62b61a0fe7dfe1ba6d8cf2b8f4f072c53543ad25a` | Current disk snapshot, 211 inputs |
| PROCESS_IDENTITY | VERIFIED within bounded observation | OS listener/PID/start/image and response agree |
| RUNTIME_INSTANCE_ID | `e8e33cd84be14c7b85df4e003513fc10` | Fresh response from observed listener |
| Process-reported SOURCE_SNAPSHOT | `sha256:9789c2760ba7e78a4e6c5f6c7b1a5dec775c76f362cb40bb09d39e7d377a44df` | Import-time source snapshot only |
| SCOPED_LOADED_CODE | `sha256:de7d20b64ee306483de026bb7bbce24763bb64d180b42c24a961d8eac23fbf60` | Startup/current registered-code hashes match; non-transitive |
| Full RUNTIME_BUILD_ID | NOT_OBSERVABLE from existing projection | No complete loaded-build provenance exposed |
| ACTIVE_PROCESS_BUILD | NOT_DIRECTLY_VERIFIED | Source mismatch and incomplete coverage |
| Runtime Identity | NOT_VERIFIED | Complete correlation absent |
| PROVIDER_RUNTIME_IDENTITY | NOT_VERIFIED / NOT_OBSERVED | Invocation null; no provider operation performed |

`SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD` and `SCOPED_LOADED_CODE != FULL_APPLICATION_BUILD` remain explicit. A source hash and a registered-code hash are not interchangeable.

## Deterministic mismatch investigation

`BUILD_ID` is captured using disk `source_build_id()` at import time; it is not a record of the exact bytes used by every Python loader. `reconstruct_source.py` calculates the source fingerprint using the existing algorithm and the 211 input paths preserved in R2-A12. It then applies historical before-file bytes in memory only, without overwriting any source:

1. Current files reproduce `fea32d2a822f9a23a5ae8de62b61a0fe7dfe1ba6d8cf2b8f4f072c53543ad25a`.
2. Before-Phase-B bytes for `app/api/runtime_verification.py` and `app/core/runtime_correlation.py` reproduce historical C0 disk fingerprint `fdc9a1e219ce55ab5957a58a31aef67a7a9a12277dabb03a1bad9b62871821ad`.
3. Adding before-R2-A10 bytes for `app/api/control_plane.py` reproduces `9789c2760ba7e78a4e6c5f6c7b1a5dec775c76f362cb40bb09d39e7d377a44df`, equal to the newly observed process snapshot.

Thus the specific hash discrepancy is reproducible from the three retained source-version differences and the import-time capture mechanism. It does not require an assumed timestamp explanation or changed input set. Historical bytes are reconstruction inputs, not newly observed executed-code evidence. Aggregate equality does not prove that all those bytes were loaded into process memory, nor exclude source/load races or later runtime mutation.

## Proven coverage gap and implementation decision

Two new isolated counterexamples use the actual registered-code manifest algorithm. Changing a handler's global value changes its result without changing its registered-code hash. Replacing a transitively invoked helper's code also changes the result without changing the registered handler manifest. Additional tests distinguish a deterministic disk fingerprint from executed loader bytes and demonstrate retained import-time snapshots after source changes.

The endpoint explicitly excludes globals, closures, assets and provider dependencies; `full_application_build_verified` is false. Matching the existing two hashes therefore cannot satisfy the contract's full positive VERIFIED case. Adding a hash field, a client assertion or an unsubstantiated complete-coverage flag would not resolve this gap. No such implementation was made, and no existing assertion was weakened.

The current process cannot acquire a newly implemented provenance mechanism without a separately authorized load/restart. Restarting would be necessary for a future mechanism to take effect, but would not itself prove complete build coverage. No restart occurred.

The minimum next engineering prerequisite is an explicit, closed build definition and a trusted provenance path tying actual loader/artifact bytes to that build, PID/start and runtime instance. Missing or uncovered modules, dependencies, runtime-mutated globals and other relevant inputs must invalidate completeness. Expected source/artifact identity must remain distinct from observed loaded identity. This is a proposed requirement, not an implemented mechanism or an authorization record. Future activation requires a separate human decision.

## Tests and actual attempts

Project interpreter: `.venv\Scripts\python.exe` (Python 3.13.15); pytest 9.1.1. Selected test IDs are preserved in `SELECTED_IDS.json` and `SELECTED_IDS_FINAL.json`.

The focused selection contains 2 existing runtime-identity tests, 16 existing runtime-attestation tests and 5 new report-owned diagnostic tests. No full suite, browser/E2E, provider or authorization test entry point was run.

| Attempt | Passed | Failed | Error | Skipped | Deselected | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Initial guarded run | 7 | 16 | 0 | 0 | 0 | 5 |
| Final guarded run | 23 | 0 | 0 | 0 | 0 | 1 |

Initial failures came from a runner guard blocking Windows asyncio's stdlib fallback socketpair, before the application request path. Only the report-owned guard was corrected: it permits the exact `socket._fallback_socketpair` caller and its own bound loopback listener address, excluding application/provider ports. Other outbound connects and real HTTP transports remain blocked. The final warning is inherited Starlette/httpx deprecation; no dependency was changed. Initial logs/XML remain intact. Final run: 23 passed in 1.91 seconds.

The NORMAL health regression uses source-derived HealthResponse/health_check with isolated route owners rather than loading protected NORMAL composition. The actual-main subprocess regression executes existing assertions with protected-file/SQLite guards. Results establish the selected isolated regressions, not whole NORMAL production behavior.

### Contract acceptance accounting

| Requirement | Outcome |
| --- | --- |
| A: complete matching process/build VERIFIED | BLOCKED: complete loaded-build provenance unavailable; no synthetic full-build PASS manufactured |
| B: mismatch | New observation/reconstruction demonstrates mismatch; no new build assessor implemented |
| C/D/E: missing process/build or malformed metadata | New implementation acceptance tests NOT RUN because no new binding implementation exists |
| F: determinism | Passed for bounded disk fingerprint; does not prove active memory |
| G: protected-state safety | Guards prohibit protected opens/SQLite; protected files intentionally not inspected or digested |
| H/I: provider/authorization isolation | Import and transport guards; no provider, grant/reserve/dispatch/IPC operation |
| J: existing regression | All 18 selected existing identity/attestation tests passed within documented runner boundary |

These results are diagnostic evidence. Overall implementation acceptance remains BLOCKED.

## Commands and evidence

Executed from the repository, using PowerShell and the existing executables:

```powershell
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' rev-parse --show-toplevel
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' branch --show-current
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' rev-parse HEAD
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' status --porcelain=v1 --untracked-files=all
Get-NetTCPConnection -State Listen -LocalPort 8000
Get-CimInstance Win32_Process
& '.venv\Scripts\python.exe' -B docs/reports/r2-a13-runtime-identity-binding-20261008-841d2e7a/reconstruct_source.py
& '.venv\Scripts\python.exe' -B docs/reports/r2-a13-runtime-identity-binding-20261008-841d2e7a/observe_once.py
& '.venv\Scripts\python.exe' -B docs/reports/r2-a13-runtime-identity-binding-20261008-841d2e7a/isolated_runner.py
# The same isolated_runner.py command ran twice; both attempts are retained.
```

Source/contract reads and Graphify navigation were read-only. Process observations use bounded listener-selected CIM metadata; the two process JSON files preserve projected actual outputs. Source reconstruction logs, raw HTTP response, XML results and selected IDs preserve the task results. Git capture and monitored-file digest comparison were repeated before/after. Report-owned helper files contain the exact calculation, observation and pytest selection/guard code. No graph update was required because existing application/test code was unchanged.

## Diff, safety and final status

Existing application/test/configuration files changed: **none**. Files created: report-owned helpers, diagnostic test, captured JSON/log/XML evidence and this report; `FILE_MANIFEST.json` lists top-level artifact digests. Pytest temporary fixtures are confined to this new directory. Historical artifacts were read but not overwritten. The report-owned runner alone was corrected between attempts.

Protected state: UNCHANGED by task operations; no database/WAL/SHM/RAG access or hash was performed. This is scoped operation/guard evidence, not an independent full-machine protected-file forensic claim. No provider/model invocation, authority activation, restart, deployment, E2E or gate edit. Scope violations: NONE observed.

Implementation: **BLOCKED**. PROCESS_IDENTITY: VERIFIED within the observed PID/start/listener boundary. ACTIVE_PROCESS_BUILD: **NOT_DIRECTLY_VERIFIED**. Runtime Identity: **NOT_VERIFIED**. R2-A8 remains BLOCKED / NOT_VERIFIED; R2-A9 remains HOLD. Provider/model: NOT_INVOKED. Authorization: NOT_ACTIVATED. Git preservation: PASS. RUNTIME_RESTART_REQUIRED: YES for future mechanism loading; restart alone is insufficient and was not executed.

STOP. No next phase or live activation is authorized by this report.
