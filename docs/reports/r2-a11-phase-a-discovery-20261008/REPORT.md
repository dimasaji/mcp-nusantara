# R2-A11 Phase A discovery — 2026-10-08

**Phase A discovery completed. R2-A11 live verification: NOT_VERIFIED. Human decision: HOLD. Implementation/live operational authorization: NOT_GRANTED.** No implementation or activation occurred.

## Contract and repository

The requested `docs/AI R2-A10 CLOSURE & R2-A11 EXECUTION CONTRACT.md` does not exist. Filename discovery found the matching document at `docs/commands/R2-A10 CLOSURE & R2-A11 EXECUTION CONTRACT.md`, document ID NUSANTARA-MDE-R2-A10-CLOSURE-R2-A11-20261008. Its final directive authorizes read-only Phase A only and requires stopping before implementation or live operational actions. Contract hashes are recorded in CONTRACT_AND_BASELINE_HASHES.json.

Repository root independently observed: C:/Users/dmaza/mcp-starter. Branch: codex/fullroot-control-20261007. HEAD: 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab. All match the contract. GIT_BASELINE.json records staged/unstaged/untracked status; staged paths are empty. The 26 tracked modifications and pre-existing untracked work are inherited, not this phase's implementation. Git inventory has five inherited inaccessible report directories; their contents were not repaired or inspected. Status is not proof of absence of protected-file changes outside monitored paths.

## Independent R2-A10 evidence review

Reviewed `.dev/R2_A10_AUTHORIZATION_CONTRACT_20261008_134113.md` and predecessor `docs/reports/r2-a10-isolation-fix-20261008/REPORT.md`, IMPLEMENTATION.diff, before/control_plane.py, SOURCE_BEFORE.json, SOURCE_COMPARISON.json, GIT_FINAL.json, isolated_test_runner.py, BASELINE.xml and TARGETED_AND_REGRESSION.xml.

SOURCE review: current hashes of the 380 explicitly listed source/test/script/service paths match the predecessor comparison: only app/api/control_plane.py differs from the pre-R2-A10 snapshot; 379 are unchanged. The current file hash is ce0681617dd31a146b33198173dfee1d6ad61794117970f94f5e5b543aa14d44. This independently supports the existing lazy-import correction, not full build verification. No protected database or sidecar was read or hashed. The fix was not reapplied.

The exact implementation remains a move of AuthorizationError/SCOPE from module scope into the intention handler after ATTESTATION-only rejection. Evidence-only import no longer brings in app.approval via the shared router; NORMAL snapshot and ATTESTATION composition paths remain present. Existing assertions remain unchanged against their recorded source snapshots.

JUnit independently contains 89 tests, zero failures/errors/skips: attestation 16, identity 2, correlation 16, verification 24, Control Plane binding 31. BASELINE.xml contains one failure for the original integration test. The one deprecation warning is predecessor-reported; JUnit does not independently encode its warning count. These are **historical TEST_ISOLATED artifacts**, not a new test run or live observation. Test results were not regenerated or overwritten.

The runner blocks SQLite connections, protected-file opens and real HTTP transports, and rejects knowledge/RAG/language imports. The NORMAL health test uses the unchanged health handler AST with synthetic eager API owners and memory-only configuration. This supports isolated NORMAL composition/handler regression, not complete production NORMAL startup. Guard coverage is Python-level and not OS-level exhaustive monitoring.

## Current process evidence

PROCESS_OBSERVATION.json records OS observation at 2026-10-08T07:35:01.7560958Z: listener 127.0.0.1:8000, python.exe PID 33040, parent 1268, start 2026-10-08T13:30:22.561656+07:00. Image: Python313/python.exe. Command line names the repository venv launcher, `-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1`.

PID 32796 from older phases cannot be reused as current evidence. Neither the venv command line nor the start time proves loaded R2-A10 code. Working directory, effective profile, runtime instance and registered handler hash were not observed. Win32_Process does not expose working directory here. No runtime memory access, IPC, HTTP, provider probe or service action was used to fill these gaps.

## Evidence matrix and gaps

| Domain | Evidence class and finding | Remaining gap |
|---|---|---|
| Repository/source | SOURCE: branch/HEAD and scoped file hashes match | Source snapshot is not active build |
| Import isolation | SOURCE + historical TEST_ISOLATED: minimal fix, unchanged integration assertion, 89 passing artifacts | Current listener's loaded composition unknown |
| Listener/process | PROCESS_OBSERVED: PID/start/image/parent/entrypoint command line | No same-request process and runtime-instance attestation |
| SOURCE_SNAPSHOT | SOURCE: import-time source_build_id algorithm reviewed | Current process's captured BUILD_ID not obtained |
| SCOPED_LOADED_CODE | SOURCE: registered route/middleware/identity/controller code objects | Current process hashes unavailable; non-transitive globals/closures/native/assets excluded |
| ACTIVE_PROCESS_BUILD | NOT_DIRECTLY_VERIFIED | No complete loaded-build coverage or direct serving-process/full-build proof |
| Provider/model | SOURCE + historical TEST_ISOLATED mock receipts | No PROVIDER_CONFIRMED evidence; actual model unknown |
| Freshness | SOURCE: process/instance/code checks, monotonic permit expiry and review expiry/material checks | No bounded observation window joining live receipt to listener process |
| Governance | HUMAN_DECISION: contract HOLD; SOURCE: PENDING-only browser intention | No native authority/operational activation authorized |
| Live service | NOT_OBSERVED in this phase | No LIVE_SERVICE request performed |

SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD. SCOPED_LOADED_CODE != FULL_APPLICATION_BUILD. Historical fixtures, configured model labels and isolated PIDs do not close these gaps.

## Existing mechanisms, safety and freshness

app.main distinguishes evidence-only, ATTESTATION and NORMAL. ATTESTATION installs runtime_verification, a private authorization foundation and attestation; NORMAL imports existing API owners. runtime_attestation captures OS identity/instance and scoped code manifest, compares current registered code and explicitly declares full_application_build_verified=false and runtime_identity=NOT_VERIFIED.

runtime_verification VerificationController checks ATTESTATION, one worker, loopback port 8000 and Ollama; checks scoped code before and after invocation; reserves one-use authorization before awaiting; uses OneDispatchTransport with retries=0, no redirects/proxy environment, fixed generation input and bound endpoint. OllamaProvider.generate binds request/invocation/process/instance/source and derives actual_model from a completed provider response. Health checks are not invocation evidence. Failure/cancellation produces no successful model receipt and no retry.

ResponseObservationMiddleware records successful final ASGI send separately from provider response. application_response_sent does not prove external client receipt; external_client_observed remains false. A body cannot attest its own later delivery. CorrelationReceipt is immutable, content-free and contains scoped fields, but lacks a dedicated process-start field and explicit observation expiry. External comparison must join receipt PID/runtime_instance/source/scoped code to same-window attestation; a persisted receipt alone is not fresh evidence. No general externally supplied receipt acceptance mechanism was verified. No stale/conflicting artifact may be accepted merely because identifiers resemble configuration.

runtime_authorization binds scope, process start, PID, instance, source/scoped hash, endpoint/configuration digest and expiry; rejects changed material, expired/wrong actor, queue/audit inconsistency. Browser JSON is intention only. Existing owner reuses private memory AuditTrail/ApprovalQueue. No policy is auto-provisioned; live actions remain locked. Positive historical unit transitions use isolated mocks, not live authority.

Do not call NORMAL `/v1/control-plane/snapshot`: its project() branch may digest protected DB/WAL/SHM. ATTESTATION evidence projection has a separate bounded path, but the active profile has not been proved. `/v1/chat`, `/v2/chat`, `/v2/dev` and port 5173 provide no workaround.

Source lifecycle review: service/nusantara-service.ps1 includes process termination/PID/log handling; scripts/start_windows.ps1 includes environment creation, dependency installation, tests and reload. Neither was run. Command-line similarity does not prove which launcher started PID 33040. These scripts are inappropriate for an unapproved evidence-only refresh.

## Minimum next plan — proposed only

No source correction is justified solely by Phase A findings. Existing scoped attestation and correlation primitives already cover the proposed narrow evidence surface in source; missing live observations are not an import bug.

First human gate: authorize a specifically bounded read-only live-attestation observation, with no generation, provider health request, restart, snapshot projection or native activation. The existing GET /v1/runtime/attestation is the candidate; source shows loopback/port checks and scoped projection. Confirm observation permission and scope before dispatch, compare PID/start to OS observations before/after, preserve timestamped raw attestation, and reject missing/mismatched/stale bindings. Do not assume availability from source. A read-only observation would still not prove full ACTIVE_PROCESS_BUILD.

If implementation is later requested, exact candidate files are app/core/runtime_correlation.py (optional immutable process-start/receipt freshness metadata), app/api/runtime_verification.py (populate and validate only genuine receipt metadata), and tests/test_runtime_correlation.py / tests/test_runtime_verification.py (expiry, process reuse, conflicting identity and final-send regressions). These are proposals, not authorized changes. Avoid implementing a second authority or accepting client model/actor assertions. Any broader build-coverage requirement needs a separately specified threat model and contract; do not label scoped hashing a full build.

A later real provider invocation requires its own explicit decision and viable existing trusted authorization path. This Phase A does not provision that path, weaken live lock, create a bypass or authorize a fallback/retry. If the locked foundation cannot support the future scope, report the blocker for a separate design decision.

Security risks: PID reuse, race between listener and attestation observation, stale receipts after restart, unknown loaded profile, shallow code coverage, credential/receipt retention and confusing browser intention with authority. Minimum approach preserves redacted/content-free receipts and server-only permits. Regression plan: isolated freshness/binding/transport/final-send cases plus the unchanged 58 runtime and 31 Control Plane tests, using new report destinations and protected-state guards. Full NORMAL startup is still outside this safety boundary. No tests were rerun in Phase A.

Rollback boundary: no production rollback is needed for this documentation-only phase. Any future scoped implementation must preserve exact pre-change copies, review only approved file diffs, never use Git reset/cleanup or revert inherited work, and require a separate decision for service loading. No database repair, configuration/provider change or governance deletion may be part of rollback.

## Actions and reproducibility

Executed read-only inspection: Get-Content of the named contract, predecessor reports/diff/runner and listed source; rg --files for contract location and rg -n for source relationships. Filename discovery reported inaccessible historical test directories; no permissions were repaired. An attempted read of optional SOURCE_AFTER.json showed it is absent; this is not cited as evidence. SOURCE_BEFORE.json and SOURCE_COMPARISON.json suffice for the independent 380-path comparison. An initially narrow safe-path allowlist rejected script/service paths before completing the comparison; after inspecting those names, the allowlist was expanded to source/script/service paths. No protected data was accessed.

Git commands (existing local Git executable): rev-parse --show-toplevel, branch --show-current, rev-parse HEAD, status --short --untracked-files=no, status --porcelain=v1 --untracked-files=normal, diff --cached --name-only, diff --name-only. OS commands: Get-NetTCPConnection -State Listen -LocalPort 8000 and Get-CimInstance Win32_Process -Filter ProcessId=<listener PID>. Historical XML parsed with PowerShell [xml], grouped by classname. Source hashes obtained with Get-FileHash -Algorithm SHA256 only on the validated manifest paths. Exact findings are saved in GIT_BASELINE.json, PROCESS_OBSERVATION.json, SOURCE_REVIEW.json and TEST_EVIDENCE_REVIEW.json.

Existing graph queried (not rebuilt): `C:/Users/dmaza/AppData/Roaming/uv/tools/graphifyy/Scripts/python.exe -B -m graphify query "runtime attestation runtime correlation verification control plane authorization" --budget 1800`. Query returned 305 nodes, truncated to 49; direct source inspection supplied the detailed findings. No dependency installation, code import/boot or test execution was performed in this phase.

## Stop and human decision

R2-A10 remains PASS_SCOPED. R2-A9 remains PASS_SCOPED / HOLD. R2-A8 remains BLOCKED / NOT_VERIFIED. Full Runtime Identity and provider/model live correlation remain NOT_VERIFIED; ACTIVE_PROCESS_BUILD remains NOT_DIRECTLY_VERIFIED. ARM/EXECUTE remain LOCKED, IPC NOT_ACTIVE and production activation NOT_AUTHORIZED per governing contract; these are governance states, not newly probed service states.

Only new discovery documentation was written. Historical evidence, source, configuration, database/WAL/SHM, RAG, provider/model, policy and gate records were not modified. No HTTP, IPC, arming, generation, restart/reload, deployment, staging or commit occurred.

**STOP. Human decision required before Phase B implementation or Phase C live observation/operational verification.** Please decide HOLD, or explicitly authorize the next bounded phase and its actions. This request follows Sections 13, 20 and 24 of the governing contract; no next phase has begun.
