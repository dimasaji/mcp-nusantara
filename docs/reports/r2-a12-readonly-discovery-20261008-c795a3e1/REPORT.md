# R2-A12 — Read-only Runtime Identity discovery

Date: 2026-10-08. Discovery authorized by the latest human decision. **Runtime Identity: NOT_VERIFIED. ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED. STOP.** These are evidence conclusions, not changes to gate or authorization records.

## Repository and preservation

Observed root `C:/Users/dmaza/mcp-starter`; branch `codex/fullroot-control-20261007`; HEAD `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`; staging empty. Git before/after has zero accessible inherited-status differences outside this new report directory. All 381 monitored existing source/test/configuration paths remain unchanged. Five inherited inaccessible historical report directories produce Git warnings and were not opened/repaired.

Only report-owned collector, pure comparison script, evidence and this report were created. No source/test/configuration/database/RAG/index/provider/model/gate/authorization record was modified, no dependencies installed, no service action or Git mutation performed. No tests, browser, authorization, grant/reserve/dispatch, generation, health/list-model or /v2/chat operation was executed.

Historical R2-A11 Phase A/C0 and Level C reports were inspected for context. Their PIDs, hashes and test totals were **not used as new results**. All observations below come from this task's metadata capture, single HTTP response and current disk comparison.

## Safe existing evidence surface and actual request

Source review covered `app/main.py`, `app/core/runtime_attestation.py`, `app/core/runtime_identity.py`, receipt/code-function accessors, ResponseObservationMiddleware and in-memory metrics. Existing GET `/v1/runtime/attestation` projects captured process metadata, actual registered code-object hashes and an already-stored receipt, if any. It does not invoke a provider, inspect knowledge/database files, grant authorization or call the verification handler. Code-function listing accesses references only. The response-observation middleware marks only `/v1/runtime/verification`, not this GET. NORMAL Control Plane snapshot was not called.

Read-only means no protected/domain/authorization mutation. The ordinary request middleware increments in-memory HTTP metrics/context and Uvicorn may produce access logs. These normal observability effects are disclosed; no claim of zero process-memory change or exhaustive OS-level write monitoring is made. No protected file/DB inspection was used to check safety.

Exactly **one GET** to `http://127.0.0.1:8000/v1/runtime/attestation`:

- Interval: `2026-10-08T09:04:02.014702+00:00` to `2026-10-08T09:04:02.111734+00:00`.
- Actual output: HTTP **200**, **4213 bytes**, application/json, not truncated.
- X-Request-ID: `req_fc0338f02b3d4fa1`; this is the observation request identifier, not a provider invocation.
- Body SHA-256: `49b688161738379439805dcd879a26698f6268ab2f357339ffa8880a50295b4a`.
- Response cap 262144 bytes, socket timeout 10 seconds; no proxy, credentials, redirect follow or retry.
- Exclusive `REQUEST_ATTEMPT.json` prevents sending a second request by rerunning the collector. No second HTTP request occurred.
- `RESPONSE.json` preserves the actual response; no secret fields required redaction. `HTTP_RESULT.json` / `OBSERVATION.log` preserve timing, headers, byte count and wire/preserved digest.

The body happens to match a historical response's digest. It is still a separately acquired response with new request/timing/header evidence; repeated captured metadata is not inferred to be newly captured process startup data or proof of freshness for every field.

## Identity evidence and statuses

| Required identity | Actual evidence | Status and precise limit |
| --- | --- | --- |
| Repository root/branch/HEAD | Independent Git inspection in this workspace | VERIFIED for inspected repository; does not prove all active modules came from current HEAD |
| Listener/process PID | 127.0.0.1:8000 owned by PID **33040**, parent **1268**, before and after GET; response process_id/observed_process_id agree and valid_for_current_process=true | VERIFIED for this observation window; not continuous PID monitoring |
| Process start | Win32_Process `2026-10-08T06:30:22.5616560Z`; response `2026-10-08T06:30:22.561656+00:00` | VERIFIED after timezone/precision normalization; PID reuse not inferred from PID alone |
| OS executable | `C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe` in OS metadata before/after and response | VERIFIED path/image identity; loaded executable bytes/version were not attested |
| Interpreter | Response captured interpreter `C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe`; same launcher in OS command line | VERIFIED as reported interpreter/launch binding; base OS image differs legitimately from launcher path; no package/environment content identity claim |
| Command line | `"C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1` | VERIFIED from current Win32_Process metadata |
| Application entrypoint | OS `app.main:app` command plus live service name Nusantara Core + Hermes API, version 0.1.0, entrypoint app.main:app | VERIFIED bounded serving-application attribution; not full build verification |
| Working directory captured by application | `C:\Users\dmaza\mcp-starter` in response, equal to inspected repository path | VERIFIED as the captured startup/setup value exposed by the endpoint; it is not independently refreshed current cwd evidence |
| Independently current working directory | Win32_Process does not expose cwd; endpoint captures `_process_identity()` during installation rather than each request | NOT_OBSERVABLE through inspected read-only surfaces; no remote-memory debugger/injection added |
| Runtime instance value | `e8e33cd84be14c7b85df4e003513fc10`, same in attestation/readiness, bound to observed PID | VERIFIED as this process's exposed scoped instance value; not full Runtime Identity or cross-request persistence proof |
| Current disk SOURCE_SNAPSHOT | Reproduced deterministic inspected source hash below, without application import | VERIFIED for bounded disk-source calculation only |
| Active process source association | Process snapshot differs from current disk snapshot | NOT_VERIFIED |
| Active process full build | Response explicitly full_application_build_verified=false; incomplete/non-transitive coverage and source mismatch | **ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED** as mandated; no full-build assertion |
| Provider/model invocation | provider_invocation=null, provider_observation=NOT_OBSERVED, provider_receipt_exposed=false, actual model absent | NOT_OBSERVABLE through this endpoint; provider/model correlation NOT_VERIFIED |
| Full Runtime Identity | Complete current application/process/current build/runtime/provider/model/response correlation is absent | NOT_VERIFIED |

PID, start, image, command line and startup cwd are actual observations, not assumptions from filenames/timestamps. Source/instance/cwd labels have their stated limited meanings. No configured model name was substituted for genuine provider evidence. No claim is made that R2-A11's corrected receipt helper has been loaded into this process.

## Source and scoped loaded-code comparison

Fresh process-import SOURCE_SNAPSHOT reported by the endpoint:

`sha256:9789c2760ba7e78a4e6c5f6c7b1a5dec775c76f362cb40bb09d39e7d377a44df`

Current disk SOURCE_SNAPSHOT, reproducibly calculated twice with the inspected `source_build_id` function extracted as AST, never importing application modules:

`sha256:fea32d2a822f9a23a5ae8de62b61a0fe7dfe1ba6d8cf2b8f4f072c53543ad25a`

The two differ. No restart/loading was used to resolve or hide this mismatch. `SOURCE_SNAPSHOT_INPUTS.json` records source-only input paths/digests; inspected selection has 211 candidate paths. JSON inputs are existing evaluation datasets/baselines, not protected knowledge/index files. The collector checks for unsafe knowledge/RAG/data/index JSON inputs before calling the algorithm. App code/assets and the algorithm's explicit project/worker source files are read only; no DB/WAL/SHM or knowledge-store content was read/hashed.

Live startup/current registered-code hashes both:

`sha256:de7d20b64ee306483de026bb7bbce24763bb64d180b42c24a961d8eac23fbf60`

The endpoint reports MATCH, with 15 manifest entries and explicitly non-transitive coverage. A pure compile-only comparison (no module execution/import) of current disk app.main/runtime_identity/runtime_attestation code matched **11 manifest entries**. **4 FastAPI dependency entries were not independently compared: NOT_OBSERVABLE** within the bounded comparison. These are 15 entries, including duplicate route references, not 15 unique application functions. `IDENTITY_COMPARISON.json` preserves per-symbol hashes/results.

Matching scoped code does not reconcile the different whole source snapshot. No reconstructed complete application composition or active memory/build inventory was collected. Global values, closure contents, native libraries, assets, dependency code, dynamically loaded/unregistered helpers and provider state remain outside loaded-code coverage. Therefore:

`SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD`

`SCOPED_LOADED_CODE != FULL_APPLICATION_BUILD`

No test PID, historical hash, configuration or health response was treated as active full-build or provider proof.

## Exact executed discovery commands and output evidence

From `C:\Users\dmaza\mcp-starter`:

```powershell
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' rev-parse --show-toplevel
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' branch --show-current
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' rev-parse HEAD
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' status --porcelain=v1 --untracked-files=all
& 'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe' diff --cached --name-only
Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter 'ProcessId=33040'
& .venv/Scripts/python.exe -B docs/reports/r2-a12-readonly-discovery-20261008-c795a3e1/observe_once.py
& .venv/Scripts/python.exe -B docs/reports/r2-a12-readonly-discovery-20261008-c795a3e1/compare_identity.py
```

Listener/process metadata commands ran before and after the single GET; selected properties and UTC conversion are recorded in `PROCESS_BEFORE.json` / `PROCESS_AFTER.json`. The metadata expression selects LocalAddress/LocalPort/OwningProcess and ProcessId/ParentProcessId/Name/ExecutablePath/CommandLine/CreationDate converted with `.ToUniversalTime().ToString('o')`.

The pure comparison command ran twice: first to compare, second to preserve the additional source-input manifest and demonstrate identical disk snapshot reproduction. It reads the saved HTTP response; it cannot send requests. Outputs are `COMPARISON.log` and `COMPARISON_WITH_INPUT_MANIFEST.log`.

Read-only graph query:

```powershell
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify query 'runtime_attestation endpoint process identity source_snapshot scoped loaded code' --budget 300
```

Static source/evidence reads used Get-Content, `rg -n`, and `rg --files app -g '*.json' -g '*.js' -g '*.css' -g '*.html'`; source hashes used Get-FileHash -Algorithm SHA256 over the explicit safe inventory. No protected-file search/read/hash was needed. Fresh report creation used New-Item once; subsequent writes are report-only scripts/logs/JSON. Original collector/comparison scripts preserve exact executable logic for reproduction. Do not rerun the network collector expecting another observation: exclusive request marker prevents it.

Git/source preservation outputs: `GIT_BEFORE.txt`, `GIT_AFTER.txt`, warnings, `GIT_COMPARISON.json`, `FILES_BEFORE.json`, `FILES_COMPARISON.json`. Actual HTTP result/body and comparison outputs are included, not substituted by historical artifacts. `ARTIFACT_MANIFEST.json` supplies report artifact digests.

## Scope violations and final status

**Scope violations: none observed.** One read-only metadata GET, zero retries, zero additional endpoint/health/provider/model requests. Normal in-memory request metrics/access logging are disclosed above. No invasive process memory probe, application import/boot, service mutation, protected-state operation, source/test/config change, authorization action, graph update or gate modification occurred. Preservation evidence is scoped to monitored files/accessible Git metadata, not a claim of OS-wide surveillance.

**ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED. Runtime Identity: NOT_VERIFIED. Provider/model correlation: NOT_VERIFIED.** Existing R2-A8/R2-A9/gate/HOLD records remain unchanged. Discovery cannot establish the full current-source/full-build/provider correlation with available evidence.

**STOP. No implementation, R2-A8/R2-A9 action, authorization or runtime activation follows this report.**
