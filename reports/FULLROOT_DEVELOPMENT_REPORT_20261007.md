# FULL-ROOT Development Report — 2026-10-07

Task: FULLROOT-20261007. Objective: preserve and consolidate existing Nusantara V1 under the invoked FULL-ROOT contract. **Local engineering milestone PASS_SCOPED; full contract/V1 acceptance remains IN_PROGRESS / FAIL-HOLD.** No new V1, production activation or acceptance redefinition.

## Implementation

Created `developer.py` with inspect, inventory, status, health, test, architecture-check, cleanup --dry-run, validate and report. Uses existing pytest and runtime source identity. Source inspection does not import/start the application, inspect dotenv values, open databases, probe providers or launch workers. Atomic JSON writes reject root escape; invalid state is not silently replaced. Cleanup classifies and reports exact duplicates/UNKNOWN candidates, never deletes or moves.

Patched `app/models/router.py` in place: routing metadata now reports actual provider.model; coding/reasoning use a registered-provider fallback instead of dereferencing None when Ollama/OpenAI preferences are absent. Existing provider preference, public signatures and generation delegation remain. No model installed or permanently switched.

Created `app/models/gateway.py`, a thin ModelGateway over ModelRouter supporting existing sync/async provider response forms and the V2 generate(prompt) callback. Created `app/execution/{__init__,base,native}.py`: structural tool/agent interfaces and NativeExecutor delegating to existing GovernedToolRegistry. Trusted actor role/permissions are constructor dependencies; request tool payload cannot elevate permissions. HermesV2Adapter is retained, tested through the optional protocol with an injected fixture. API startup wiring and Trust/Policy enforcement are untouched. Provider capability discovery, cloud availability and remote MCP executor are not claimed.

Created tests: `test_developer_control.py`, `test_model_router_configuration.py`, `test_fullroot_boundaries.py`. Created required maps/state: `docs/NUSANTARA_REPO_MAP.md`, `docs/ARCHITECTURE_CURRENT.md`, `docs/ARCHITECTURE_TARGET_V1.md`, `docs/ARCHITECTURE_GAP.md`, `.dev/repo_inventory.json`, `.dev/PROJECT_STATE.json`, `.dev/TASKS.json`, `.dev/DECISIONS.jsonl`. Added `docs/COMPOSITION_ROOT_DESIGN.md` with precedence, impact, boundaries, tests and rollback design. No files moved/deleted; no dependency added.

## Actually executed verification

| Check | Result / evidence |
| --- | --- |
| Baseline | 145 passed; reports/FULLROOT_BASELINE_20261007.xml |
| Developer control | 8 passed; reports/FULLROOT_CONTROL_20261007.xml |
| Router compatibility | 32 passed; reports/FULLROOT_ROUTER_20261007.xml |
| First regression after router/control | 374 passed, 28 passing subtests, 1 skip; reports/FULLROOT_ROUTER_REGRESSION_20261007.xml |
| Gateway/executor compatibility | 87 passed; reports/FULLROOT_BOUNDARIES_20261007.xml |
| Final full regression after new adapters | **380 passed, 28 passing subtests, 1 skip, 0 failures/errors**; reports/FULLROOT_REGRESSION_FINAL_20261007.xml |
| Supplemental executor failure | PASS_SCOPED; reports/FULLROOT_EXECUTOR_FAILURE_20261007.json |
| All nine developer commands | Executed with exit 0, including test --suite full and cleanup --dry-run; .dev/commands plus .dev/test-full.json |
| Static validation | PASS_SCOPED_STATIC; .dev/commands/validate-final.json |
| Scoped source security scan | 0 findings using existing scanner; .dev/security-check.json; not whole-system security certification |
| Protected integrity | 296 baseline files plus prior approved changes compared; only router changed in baseline set, as authorized and backed up |
| Git diff | Router diff inspected; whitespace check passed; new source and tests reviewed |

Final XML aggregate is 409 tests with 381 testcase elements: 380 passed + 1 skipped + 28 passing subtests. Mandatory skipped case remains Windows symlink-outside-workspace privilege test. Existing datetime/TestClient deprecations remain known warnings. No test was modified to weaken acceptance.

## Required V1 scenarios and limits

| Scenario | Scoped evidence / remaining limit |
| --- | --- |
| FAST | Direct local generation callback tested; deployed selected-path decision NOT_PROVEN |
| KNOWLEDGE | Existing isolated RAG ingest/query and API fixtures pass; live persisted/model/index pipeline NOT_PROVEN |
| TOOL | Governed calculator adapter executes, unknown/invalid/permission denial checked; unified agent tool selection not activated |
| OFFLINE | Local MockProvider and empty-registry degraded response tested; actual offline model/worker health NOT_RUN |
| MODEL-FALLBACK | Existing V2 error/degraded fallback retained; real alternate-provider health/failover NOT_PROVEN |
| INVALID-TOOL | Unknown and invalid input preserved by NativeExecutor/registry |
| CONTEXT-LIMIT | Existing V2 bounded-context tests pass in full suite |
| MISSING-KNOWLEDGE | Existing no-evidence unverified/grounding contract tests pass |
| EXECUTOR-FAILURE | Isolated failing handler returns failed through governance; no exception/policy bypass |
| RESTART-STATE | Existing memory/persistence fixture tests pass; production process restart NOT_RUN |

Do not interpret these as ten production end-to-end passes. Static import/module maps do not prove dynamic/circular dependency behavior or runtime authority. Inventory excludes data/model assets, environment contents, generated/temp roots and environments; historical/experimental files stay UNKNOWN pending reference review. Exact duplicates alone do not prove obsolete code.

## Architecture impact and recovery

Changes are PATCH + additive compatibility adapters under FULL-ROOT Level A. Core Agent/public API/CC01/policy/schema and default startup behavior are preserved. Composition root implementation, provider capability architecture, RAG knobs/index preflight, runtime controls and default wiring remain work items, with design available rather than silently activated.

Recovery checkpoint `.dev/checkpoints/fullroot-20261007/BASELINE.json` records pre-existing branch/head/status/hashes. `existing-source.patch` preserves prior tracked source differences locally; router.py has exact pre-change backup. Pre-existing dirty work is preserved and excluded from the task's source commit. New local branch: `codex/fullroot-control-20261007`; commit ID is recorded in final checkpoint/project state after commit. No push/remote changes.

Current source build: `sha256:920ad1d01be7c574ea0e5198fd306d27383c9490bb9ef40c7a821ddbcb9be976`. Earlier configuration reports retain build `sha256:487ace8eb2a8ba4d8c979fdc7728cefe7802eb0b3f8f01d3f6462d9c83e9492a`; they are historical evidence, not substitutes for new final regression. Progress overlay records current approved hashes/build; prior progress backed up.

Graph updated with installed Graphify, AST-only/no-cluster, no LLM/API or visualization. Final graph has 6330 nodes and 10654 edges. Existing protected temporary report directories could not be scanned; warnings retained. Cluster/wiki/report metadata may remain older than the no-cluster graph. Graph/import names are navigation, not consumer execution proof.

## Open issues and next action

Configuration DoD NOT_COMPLETE, DeveloperCore PASS_SCOPED, V1 FAIL/HOLD. Official oracle snapshots `tangerang-ktp-pemula-snapshot` and `tangerang-sop-data-pribadi-snapshot` need authoritative review; `paspor-requirements-missing` remains MISSING. Mandatory symlink privilege gate, CC02–06 and production deployment/restart/workload/rollback evidence remain open. No Oracle/compliance artifacts or gates were edited.

Continue from `.dev/FULLROOT_CHECKPOINT.json`: implement the reviewed opt-in composition-root design incrementally; preserve existing API behavior; close RAG/runtime semantics with actual tests. Owner-controlled oracle evidence and an eligible privileged Windows test runner are needed for external acceptance gates. Production verification requires a concrete target and explicit authorization under FULL-ROOT section 27; routine local development remains independently actionable.

This is a verified local checkpoint, not a claim that every FULL-ROOT execution-order item or all V1 acceptance criteria are done.
