# R2-A14 — Build Provenance & Runtime Binding

Date: 2026-10-08. Final acceptance status: **BLOCKED**.

A minimum artifact-manifest/provenance foundation was implemented and 63 isolated tests passed. It does **not** implement or prove complete application execution provenance. Required positive complete-build acceptance case A remains unmet. Consequently this report does not claim PASS_SCOPED for R2-A14, ACTIVE_PROCESS_BUILD VERIFIED, or readiness to activate a complete identity mechanism.

## Contract and baseline

The requested `docs/BOUNDED-DEVELOPMENT-ENVELOPE.md` did not exist. The matching contract was found and read at `docs/commands/BOUNDED-DEVELOPMENT-ENVELOPE.md`; its R2-A14 contents are preserved as `CONTRACT.md`. No replacement contract, gate or authorization record was written.

Repository: `C:\Users\dmaza\mcp-starter`. Branch: `codex/fullroot-control-20261007`. HEAD: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. The worktree was already dirty; staging was empty and remains empty. No inherited change was removed. Git and source-state captures are retained in this directory.

R2-A12/R2-A13 were not repeated. No process observation, live HTTP request, provider query or service operation was performed. Their historical PID/instance/hash values are not counted as new R2-A14 results.

## Implementation and actual diff

| File | Change |
| --- | --- |
| `app/core/runtime_build_provenance.py` | New frozen build-input/manifest and PID/start/instance types; canonical declared build identity; bounded private in-memory artifact owner; fail-closed assessment |
| `app/core/runtime_identity.py` | Reuses/re-exports the new types through the existing identity module; corrects a misleading comment to state that BUILD_ID is an import-time disk snapshot |
| `app/core/runtime_attestation.py` | Adds the new helper code objects to the existing explicitly scoped/non-transitive manifest |
| `tests/test_runtime_build_provenance.py` | 24 new isolated test cases, including parameterized cases |

No changes to main/composition, Control Plane, public response schema, receipt verification, provider implementation, configuration, authorization, gate or protected data. No loader hook or global provenance owner was installed. NORMAL/ATTESTATION runtime selection remains unchanged.

`IMPLEMENTATION.diff` attributes these changes against the captured baseline, rather than presenting inherited Git changes as this task's work. The pre-edit inherited untracked attestation file was reconstructed by removing only this task's exact patch and verified against its captured pre-edit byte digest; this is disclosed in `review_diff.py` and `CHANGED_FILES.json`.

## Expected build definition and trust model

`BUILD_DEFINITION.md` defines the required complete build boundary: application code, assets, transitive Python/native dependencies and interpreter/stdlib/native runtime artifacts. These must be independently enumerated, not inferred from a source hash, installed package version or matching endpoint fields. Provider/model runtime identity and protected runtime data remain separate.

The new BuildDefinition canonicalizes input names, roles, inventory and content digests. Inventory membership and digests are distinct. Missing entries/roles, duplicates, malformed hashes, unsafe identifiers and protected database identifiers are rejected. Exact declared inventory consistency is **not** proof of complete executable application coverage.

BuildProvenanceOwner stores only content digests supplied by an internal artifact consumer and immutable context. It binds assessments to PID **and** UTC process start **and** runtime instance. A lock serializes record/assessment operations. Invalid or repeated artifact observations terminally invalidate the owner. There is no JSON/HTTP adapter and no client-controlled trust/completeness flag; serialized receipts return UNTRUSTED_PROVENANCE.

The owner is not an OS attribution adapter or a genuine Python loader witness. Its constructor context and consumer bytes must come from trusted server composition; the foundation cannot itself prove that source bytes were executed. Complete declared byte consumption can therefore set only `artifact_binding=VERIFIED`, while `status=NOT_VERIFIED`, `active_process_build=NOT_DIRECTLY_VERIFIED` and `runtime_identity=NOT_VERIFIED` remain unchanged. This is deliberate fail-closed behavior, not full build verification.

## New evidence and identities

| Identity | Result |
| --- | --- |
| Repository identity | Root/branch/HEAD observed; unchanged |
| Current disk SOURCE_BUILD_ID | `sha256:7a6477cc5b97f3640e35708f67cc365a5ef259c1397df376924b573bc2e0b6aa` |
| Complete Nusantara build definition | INCOMPLETE |
| Actual Nusantara EXPECTED_BUILD_ID | Unavailable; no complete independent application manifest |
| Actual OBSERVED_LOADED_BUILD_ID | NOT_OBSERVABLE in this phase |
| Actual PROCESS_IDENTITY | NOT_OBSERVABLE in this phase; no new process inspection |
| Actual RUNTIME_INSTANCE_ID | NOT_OBSERVABLE in this phase |
| ACTIVE_PROCESS_BUILD | NOT_DIRECTLY_VERIFIED |
| Runtime Identity | NOT_VERIFIED |
| Provider/model | NOT_INVOKED |
| Authorization | NOT_ACTIVATED |

`APPLICATION_BUILD_BOUNDARY.json` records missing coverage explicitly. The source hash was calculated using the exact existing source_build_id function extracted through AST, without importing app.main. It is a new current-disk result and is not promoted to EXPECTED_BUILD_ID or loaded provenance.

`SYNTHETIC_PROVENANCE.json` demonstrates the declared-artifact mechanism with four synthetic in-memory inputs. Its expected and observed artifact IDs match:

`sha256:c28f49b75c22ec0937a68101bf1d861d7b6806e7daa1f6b5b39a1a74e5bb33f2`

Its PID 1234 and instance `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` are explicit synthetic fixture values, not live process evidence. Even this matching fixture returns EXECUTION_CLOSURE_NOT_OBSERVED and does not verify ACTIVE_PROCESS_BUILD. Synthetic dependency/interpreter bytes are not real dependency/interpreter attestation. No fake provider or generation was used.

## Exact test execution and outputs

Interpreter: existing `.venv\Scripts\python.exe`, Python 3.13.15; pytest 9.1.1. Bytecode and pytest cache writing were disabled. No dependency/browser installation occurred.

Executed from the repository:

```powershell
& '.venv\Scripts\python.exe' -B docs/reports/r2-a14-build-provenance-20261008-61f072ac/isolated_runner.py focused *> docs/reports/r2-a14-build-provenance-20261008-61f072ac/TEST_RUN.log
& '.venv\Scripts\python.exe' -B docs/reports/r2-a14-build-provenance-20261008-61f072ac/isolated_runner.py regression *> docs/reports/r2-a14-build-provenance-20261008-61f072ac/REGRESSION_RUN.log
& '.venv\Scripts\python.exe' -B docs/reports/r2-a14-build-provenance-20261008-61f072ac/collect_evidence.py
& '.venv\Scripts\python.exe' -B docs/reports/r2-a14-build-provenance-20261008-61f072ac/review_diff.py
```

| Selection | Passed | Failed | Errors | Skipped | Deselected | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| New provenance tests | 24 | 0 | 0 | 0 | 0 | 0 |
| Existing bounded regression | 39 | 0 | 0 | 0 | 0 | 1 |
| Total | 63 | 0 | 0 | 0 | 0 | 1 |

Focused run took 0.17 s; regression 1.64 s. There were no failed attempts in this task. The inherited warning is Starlette/httpx deprecation; no dependency remediation was performed.

Exact node IDs are in `focused_SELECTED_IDS.json` and `regression_SELECTED_IDS.json`. Regression selection: 2 existing runtime-identity cases, 16 runtime-attestation cases, 19 B2 synthetic no-dispatch integration cases, and 2 existing observer-preservation cases. Other provider/generation/authorization/full-suite tests were excluded by explicit file selection, not silently counted as passing; pytest reports zero deselected within the selected paths.

## Required matrix accounting

| Requirement | Evidence and limitation |
| --- | --- |
| A: complete matching build provenance → VERIFIED | **Not satisfied.** Matching declared artifacts verify only artifact_binding; execution closure remains unobserved. No positive full-application test was manufactured. |
| B: mismatch | New mismatch test passes; returns BUILD_MISMATCH / NOT_VERIFIED |
| C: missing expected identity | New test passes; EXPECTED_BUILD_MISSING |
| D: missing observed identity | New test passes; OBSERVED_LOADED_IDENTITY_MISSING |
| E: malformed provenance | Six malformed-definition cases pass with bounded non-sensitive reasons |
| F: incomplete manifest | Missing inventory input and partial consumed inventory fail closed |
| G: untrusted provenance | None, empty JSON and forged trust/completeness JSON rejected |
| H: determinism | Reordered inventory has identical ID; 20 concurrent repeated assessments are identical |
| I: process mismatch | PID mismatch and PID reuse/start mismatch rejected; boolean PID and invalid time rejected |
| J: instance mismatch | Rejected separately from process mismatch |
| K: provider isolation | Provider generation/structured/health/list methods and real HTTP transports guarded; not invoked |
| L: authorization isolation | grant/reserve/dispatch guarded; synthetic B2 cases preserve real DISARMED owner |
| M: protected state | Protected-open and SQLite guards; new assessment test also prohibits file/network/SQLite I/O |
| N: R2-A11 regression | 19 B2 + 2 observer regression cases actually passed |
| O: runtime attestation | 16 cases actually passed; 2 identity cases also passed |

Tests were not weakened to force a full-build positive. Full R2-A14 acceptance is BLOCKED despite the passing bounded tests.

## Isolation, graph update and preservation

Runner guards prohibit protected `.db`, `.db-wal`, `.db-shm` and knowledge-path opens, SQLite connect, real HTTP transports, provider operations and grant/reserve/dispatch. Windows asyncio's exact stdlib fallback socketpair is allowed only for its own loopback listener and excludes application/provider ports. There is no live backend request or service listener.

Existing actual-main regression creates two isolated test subprocesses with read-only composition and ASGI TestClient, no TCP service bind and protected-file guards. These test boots are allowed fixtures, not replacement Nusantara instances. The NORMAL health test uses the existing source-derived health handlers with isolated route owners; it does not load protected NORMAL dependencies. Selected regressions do not prove complete NORMAL production behavior.

Source state: 381 previously monitored existing files compared; only runtime_identity.py and runtime_attestation.py changed. New application/test files are listed separately. All other monitored file digests match. Git before/after preserves branch/HEAD/staging and inherited entries. `GIT_COMPARISON.json` shows only the new provenance module/test as new Git entries outside the report. No reset, clean, checkout, restore, staging, commit or push was used.

Per AGENTS.md, graphify AST-only update ran after code changes:

```powershell
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify query 'runtime_identity runtime_attestation source_build_id loaded_code_manifest build provenance' --budget 1700
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify update . --no-cluster
```

Graph update completed with 10316 nodes / 18643 edges, no semantic LLM/provider/API calls. Generated graph files changed; curated graph outputs were automatically backed up by graphify. Graph before/after digests and log are preserved. Existing inaccessible historical report directories produced scan/Git warnings and were not repaired. Graph navigation/output is not runtime evidence.

Protected state: UNCHANGED by task operations; no database/RAG/WAL/SHM read, hash or mutation. This is bounded guard/operation evidence, not a full-machine forensic assertion. No live process observation/request, restart, reload, service launch, MCP, E2E, activation, provider/model operation or protected-state operation. Scope violations: NONE observed.

## Remaining blocker and stop

There is no complete independently trusted Nusantara manifest and no loader witness linking that inventory to exact executed Python/native artifacts and relevant execution closure. The new owner records consumer-supplied bytes only, so it cannot supply the missing trust by itself. It must not be wired to an endpoint and advertised as complete provenance. A genuine closed-build/loader integration is still required; service restart alone would not solve this boundary.

Source changes would require a separately authorized load/restart to become available in the existing service: **RUNTIME_RESTART_REQUIRED = YES**. No restart was performed. **IMPLEMENTATION_READY_FOR_ACTIVATION = NO** for the requested complete identity mechanism, because requirement A and the trust boundary are unresolved. The contract's ready-for-activation YES cannot truthfully be reported for this incomplete implementation.

R2-A8 remains BLOCKED / NOT_VERIFIED. R2-A9 remains HOLD. Full Runtime Identity remains NOT_VERIFIED. ACTIVE_PROCESS_BUILD remains NOT_DIRECTLY_VERIFIED. No gate or authorization record was changed.

STOP after evidence review. No runtime activation or next phase was initiated.
