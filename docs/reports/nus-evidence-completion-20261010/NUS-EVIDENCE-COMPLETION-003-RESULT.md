# NUS-EVIDENCE-COMPLETION-003 — Completion Report

- Repository: `C:\Users\dmaza\mcp-starter`
- Date: 2026-10-10 (UTC)
- Starting revision: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab` on `codex/fullroot-control-20261007`
- Scope: Level B evidence registry, human decision UI/API, isolated tests, and report
- Outcome: **implementation and offline acceptance evidence complete; no human decision recorded; live runtime remains NOT_VERIFIED**

## Result summary

The Control Plane now builds a server-side evidence package from the declared offline manifest, keeps source classification separate from validation status, links all 15 criteria to sources and tests, exposes blockers, and binds decisions to a server-computed package ID. The human form offers only `PASS`, `FAIL`, and `HOLD`, with optional notes. Decisions require the existing admin token and are stored in a server-side hash-chained log with a separate head checkpoint.

The final offline package `evp_sha256_788db2800ff15f2077b78a75939e92ff8532d7be1dd1e377dd51e3c9c7db1bb4` validates all **15/15 criteria** and permits a reviewer to choose PASS. That is eligibility only: no decision was submitted or inferred. The package explicitly keeps runtime identity `NOT_VERIFIED`; this report does not claim the running product, provider, or knowledge store is healthy or accepted.

## Acceptance matrix

| ID | Result | Current evidence |
|---|---|---|
| AC1 | PASS | All 15 criteria are enumerated and covered by source/test links; `test_registry_covers_all_acceptance_criteria` |
| AC2 | PASS | Collector emits declared paths, classifications, validation states, and hashes; `test_collector_records_real_artifact_references` |
| AC3 | PASS | Validator distinguishes `VALID`, `INVALID`, `MISSING`, `BLOCKED`, and `NOT_VERIFIED`; `test_validator_distinguishes_all_statuses` |
| AC4 | PASS | Every criterion links evidence and tests; `test_each_criterion_links_sources_and_tests` |
| AC5 | PASS | Final runs used network, active-data, filesystem-output, subprocess, and cache guards; commands and boundaries are recorded below |
| AC6 | PASS | Run manifest and result bundle hashes validate against 11 Python and 17 Vitest results; `test_test_run_manifest_is_bound_to_result_hashes` |
| AC7 | PASS | UI has only PASS/FAIL/HOLD, optional notes, blocker visibility, and a disabled PASS when prerequisites fail; 17 UI tests passed |
| AC8 | PASS | Server recomputes the evidence package and rejects stale/client-forged IDs; `test_decision_rejects_stale_or_client_forged_package` |
| AC9 | PASS* | Missing/invalid admin tokens are denied; authorized writes record `admin-token-holder` from the existing shared admin-token mechanism |
| AC10 | PASS | PASS is blocked while criteria are unresolved; no evidence collection sets a decision automatically |
| AC11 | PASS | Material artifact changes change the package ID; UI clears an old receipt when a new package ID arrives; `test_package_id_changes_when_evidence_changes` |
| AC12 | PASS* | Decision ID, server timestamp, package/test/blocker references, hash chain, and separate head checkpoint are verified; edits and single-file truncation/deletion are detected |
| AC13 | PASS | Runtime remains `NOT_VERIFIED` independently of package/test success; UI test checks this state |
| AC14 | PASS | Snapshot route remains registered and unchanged by this work; `test_legacy_snapshot_route_is_unchanged` |
| AC15 | PASS | Blockers have explicit reasons and are rendered in Evidence and Decision; package blocker test and UI interaction test passed |

`*` Scope limitation: the existing admin token authenticates a shared token-holder principal, not a uniquely named person. A filesystem administrator who rewrites both the decision log and its checkpoint can replace local history; the files are not externally anchored. The UI states this limit and does not call the log immutable or append-only. If policy requires individual identity or protection from a privileged filesystem administrator, those are not established by this local implementation.

## Verification actually run

1. `python -B tests/run_evidence_tests_isolated.py docs/reports/nus-evidence-completion-20261010/runs/003-python-final-07` — **exit 0; 11 passed, 0 failed, 0 errors, 0 skipped**. Pytest cache plugin and bytecode were disabled; pytest temporary files and logs were confined to this new run directory. External network connections, subprocess execution, database/active-data paths, and writes outside the run directory were blocked. The guard permits an internal Windows loopback socketpair, but these endpoint tests call handlers directly and do not use it or start a service.
2. `.\node_modules\.bin\vitest.cmd run tests/human.test.tsx --config vitest.config.ts --configLoader native --reporter=json --outputFile=C:\Users\dmaza\mcp-starter\docs\reports\nus-evidence-completion-20261010\runs\003-vitest-final-05\vitest-results.json` — **exit 0; 17 passed, 0 failed**. Vitest used `cache:false`, a cache path under the new run directory, the network/data/filesystem guard, and the exact isolated Vitest worker/esbuild exceptions. A test-only local snapshot was used as a fixture; it is not evidence of current runtime state.
3. `.\node_modules\.bin\tsc.cmd --noEmit --pretty false` — **exit 0**.
4. Offline package validation via `collect_review_package()` — **15 criteria valid; `pass_allowed=true`; `runtime_status=NOT_VERIFIED`; no blockers**. No service, database, WAL/SHM, active index, provider, ingestion, or migration was accessed.

Vitest baseline E043 remained unchanged: SHA-256 `033a462d06bc94941574c6152b3e7b5b07f1216ac77e22e948ed5b4aca310453` before and after the final run (last write remains 2026-10-09 14:20:10 UTC). Earlier test-harness attempts failed before completing the scoped final suite; those attempts are not included in the current 11/17 pass counts. The successful final reports are the only results linked by the current run manifest.

## Evidence files and hashes

| Artifact | Classification | SHA-256 / detail |
|---|---|---|
| `current-test-run.json` | CURRENT_OFFLINE | `6b601996c5320c91b2e5287a1c682264c19fb6a44877284207efa52663e7de77` |
| `runs/003-python-final-07/results-bundle.json` | TEMPORARY run output | `f28257d560bf5cd48d882f46b73f1ac250c7bf0af285740dcec954793b523a48` |
| `runs/003-python-final-07/python-results.xml` | TEMPORARY run output | `34304a6c5a222afdd3b861051f98752474f5d0ea8f6640611786fc92f12ee006` |
| `runs/003-vitest-final-05/vitest-results.json` | TEMPORARY run output | `3dbb670b9d3e9ad6f39e723bd34f12f15f282dc78d228fa7d39d0e20cc743c36` |
| `control-plane/.cplane-snapshot.local.json` | FIXTURE used only by the UI test | `d01906e4e178aa2967620aaba26ef52a1e4b19f71a81b0b825fb1c23a0aede1e`; last write 2026-10-09 14:19:44 UTC |
| E043 Vitest cache baseline | CURRENT_OFFLINE baseline, preserved | `033a462d06bc94941574c6152b3e7b5b07f1216ac77e22e948ed5b4aca310453` |
| MDA-E1 / MDA-E2 reports | HISTORICAL | Referenced and hashed by `current-test-run.json`; not promoted to current runtime proof |

The run manifest hashes 16 source files. The result bundle records hashes of both machine-readable test outputs. Hash agreement establishes byte identity only; it does not establish a live runtime condition.

## Implementation files

- `app/core/evidence_registry.py` — offline evidence validation, package identity, linked test-result validation, blocker reasons, and decision audit/checkpoint.
- `app/api/control_plane.py` — package and authenticated decision routes; legacy unauthenticated decision routes now return 410.
- `control-plane/evidence-requirements.json` — all 15 criterion/source/test mappings and historical classifications.
- `control-plane/src/api.ts`, `auth.tsx`, `acceptance.ts`, `human.tsx`, `assistant.tsx`, and `ui.tsx` — package display, shared in-memory existing token, PASS/FAIL/HOLD form, server recording, and stale-package review invalidation.
- `control-plane/tests/human.test.tsx` and `tests/test_evidence_registry.py`, `tests/test_evidence_decision_api.py` — UI, validator, package, authorization, and audit coverage.
- `control-plane/tests/inspection-preview-network-guard.cjs`, `control-plane/vitest.config.ts`, `tests/run_evidence_tests_isolated.py`, and `tests/pytest-evidence.ini` — scoped test guards and isolated run configuration.

## Limitations and preserved state

- Current live service/build/provider/model/RAG/knowledge state remains `NOT_VERIFIED`. No live calls were made.
- E043's earlier writer and HCU-CACHE-01 history remain unknown; the baseline was preserved and final runs wrote only to new run paths.
- Shared-token authentication cannot name a specific person. The token value is neither changed nor logged.
- The local audit checkpoint detects one-file edits/truncation but is not protected against a privileged actor replacing both local files.
- `graphify query` and the required post-change `graphify update .` both failed with `uv trampoline failed to canonicalize script path`; the project graph was not refreshed.
- Existing working-tree changes were preserved. Initial HEAD was `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`; unrelated staged, modified, untracked, and inaccessible report paths were not reverted or cleaned. No commit or push was made.

No human PASS/FAIL/HOLD was submitted. The decision remains with an authenticated human reviewer in the Control Plane.
