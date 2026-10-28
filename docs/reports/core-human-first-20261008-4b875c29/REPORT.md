# Human-first Nusantara Core — discovery and bounded improvement

Date: 2026-10-08. **Selected improvement: PASS_SCOPED. Overall Core completeness: PARTIAL / NOT_VERIFIED where untested.** No new phase/gate or R2 assurance work was created.

## Objective

Apply the human-first contract: discover Core, Configuration, Provider/Model, Knowledge/RAG, Tool Governance, Developer Engine, Control Plane and Existing Tests; choose one useful, safe blocker and fix it with proportional tests. `DISCOVERY.md` contains current state, top five blockers, dependencies, safe next changes and human decisions. Its source findings are distinct from new tests and historical reports.

Repository `C:\Users\dmaza\mcp-starter`; branch `codex/fullroot-control-20261007`; HEAD `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. The inherited dirty worktree and empty staging were preserved. `CONTRACT.md` is a report-owned copy of the human attachment, not a modified authorization/gate record.

## Changed: one concrete answer-quality blocker

Before this change, DevCore._analyze detected unsupported model claims but kept the rejected model text as the primary answer and appended warnings/static facts. A human could therefore receive “retry with timeout 10 seconds” even though the source used timeout=3 and contained no retry.

`app/devcore/core.py:153` now replaces a rejected model analysis with a clear warning and existing static source facts. The structured verification remains `failed`, and violations are retained for review. Supported model analysis and the model-unavailable fallback remain unchanged. No policy, grounding-rule, permission or authority boundary was altered.

Application change: **one existing file, one answer-selection branch**. New test file: `tests/v2/test_devcore_grounding_response.py`, four cases. `IMPLEMENTATION.diff` compares the actual pre-edit source to the final source, not the entire inherited Git diff.

## Not changed

No Core composition, route, API schema, UI, configuration precedence/default, provider/model selection, RAG/knowledge, SQLite/WAL/SHM, authorization/gate record, approval policy, runtime identity or provenance change. Existing DevCore write/execute refusal remains in place. The broader goal-to-engineering-plan gap is documented, not implemented. R2-A14 stays BLOCKED / KNOWN LIMITATION and is not treated as a general Core development blocker.

## Tested: actual attempts

Project interpreter `.venv\Scripts\python.exe`: Python 3.13.15; pytest 9.1.1. Only new changed-path cases and relevant DevCore regression ran. No full-suite run or dependency installation.

| Attempt | Passed | Failed | Errors | Skipped | Deselected | Meaning |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Initial runner setup | NOT RUN | NOT RUN | Setup failure | NOT RUN | NOT RUN | Guard replaced subprocess.Popen with a function; Windows asyncio could not subclass it. No test ran. |
| Pre-fix reproduction | 2 | 2 | 0 | 0 | 0 | Two acceptance cases reproduced rejected claims in the answer. |
| Post-fix focused | 4 | 0 | 0 | 0 | 0 | All new cases passed. |
| Existing DevCore regression | 14 | 0 | 0 | 1 | 0 | Symlink test skipped because Windows privilege is unavailable. |

**Final validation: 18 passed, 0 failed, 0 errors, 1 skipped, 0 warnings.** The pre-fix failures are preserved, not added to the final pass total. The skipped symlink test is not counted as passing.

The runner-only setup correction guards `subprocess.Popen.__init__` while retaining the class, preventing process creation without breaking stdlib class declarations. Initial failed setup log `BEFORE_TEST_RUN.log`, reproduced source failures `BEFORE_REPRODUCTION.log`, after results and regression logs/XML are retained. No source test assertion was weakened.

New cases prove: rejected output is absent from the human answer; failure diagnostics remain; source facts show timeout=3; supported output is preserved; absent model uses static facts; modification requests remain read-only; source bytes remain unchanged; memory audit verifies and does not contain the rejected full model text.

Existing regression covers generic file extraction, routing, blocked paths, verbatim reads, original grounding checks, missing/ambiguous files, directory listing, modification refusal, prompt-injection-as-data, unavailable model fallback, audit metadata and static facts. The Windows symlink privilege test remains a limitation.

Exact test IDs: `before_SELECTED_IDS.json`, `after_SELECTED_IDS.json`, `regression_SELECTED_IDS.json`. Test outputs: `before_RESULTS.xml`, `after_RESULTS.xml`, `regression_RESULTS.xml`.

Commands from the repository:

```powershell
& '.venv\Scripts\python.exe' -B docs/reports/core-human-first-20261008-4b875c29/isolated_runner.py before
# First setup failed; the same command was rerun after the runner-only correction.
& '.venv\Scripts\python.exe' -B docs/reports/core-human-first-20261008-4b875c29/isolated_runner.py after
& '.venv\Scripts\python.exe' -B docs/reports/core-human-first-20261008-4b875c29/isolated_runner.py regression
& '.venv\Scripts\python.exe' -B docs/reports/core-human-first-20261008-4b875c29/review_evidence.py
```

The pure routing probe in `ROUTING_DISCOVERY.json` confirms a broad RAG repair goal has no DevCore actions, whereas an explicit source-file request produces a read plan. It does not invoke the planned tool or provider and does not test the general ASK pipeline.

## Not tested and evidence limits

No active-service HTTP, provider generation/health/model listing, production RAG/retrieval/database access, worker, full Core startup, API route integration, Control Plane UI/browser, human acceptance or deployment validation. Historical UI/R2 reports were read as context only and are not new execution results.

The existing grounding checker is lexical/heuristic; a model answer that triggers no listed rule is not a proof that every statement is supported. This change suppresses detected rejected analysis only. Static facts describe inspected source, not executed live behavior. Structured violation snippets remain diagnostic evidence in the existing response, so this is not a sensitive-data-retention redesign.

## Risk and protected state

Risk is low and reversible: detected-invalid model commentary is discarded as a whole, so even supported portions of a mixed rejected response are replaced by source facts. That tradeoff favors a clear answer over retaining uncertain analysis. Reviewer diagnostics remain available; existing accepted-output behavior is preserved by tests.

The report-owned runner blocks real model/API/knowledge-owner imports, real HTTP transports, SQLite/protected database opens, service subprocesses and approval mutation methods. Only the exact stdlib Windows fallback socketpair is allowed, excluding known application/provider ports. `before_GUARDS.json`, `after_GUARDS.json` and `regression_GUARDS.json` record **zero guard violations**.

Tests use temporary source files and synthetic model-text callbacks. Source strings containing HTTP examples are read/parsed as data, never executed. Dummy .env/data fixtures in the existing test are isolated; sensitive paths are rejected by the engine and no production configuration or protected state is read. Protected database/WAL/SHM/RAG/model/index data was neither accessed nor digested.

Protected state: **UNCHANGED by this task's operations**. No restart, reload, deployment, provider/model operation, permit/arming/execution, authorization activation, external consequential operation or gate promotion occurred. Scope violations: **NONE observed**. Guards are bounded Python instrumentation, not exhaustive full-machine forensic monitoring.

## Preservation and diff review

383 previously monitored existing source/test/frontend/lifecycle files were compared; only `app/devcore/core.py` changed. New test file is listed separately. R2-A14 source and all other monitored inherited files remain unchanged. `FILES_COMPARISON.json`, Git before/after and `GIT_COMPARISON.json` preserve actual results. Branch/HEAD and empty staging remain unchanged; no inherited Git entry was removed. No reset, clean, checkout, restore, staging, commit or push.

Per AGENTS.md, graphify query preceded architecture inspection and AST-only update followed source changes:

```powershell
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify query 'Nusantara Core Developer Engine DevCore configuration effective provider tool governance review workflow' --budget 2600
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify update . --no-cluster
```

The graph update completed: 10395 nodes / 18763 edges, no model/API cost. Generated graph outputs changed and graphify preserved automatic curated backups. Graph before/after digests and log are retained. Existing inaccessible historical report directories caused Git/scan warnings; their permissions were not altered. Graph is navigation evidence, not live operational proof.

Rollback, if requested, is limited to reversing this task's small answer-selection diff and added test; the captured `core.py.before` preserves the inherited pre-edit source. No rollback was executed and no inherited changes should be reset.

## Decision required and final status

The bounded fix is complete with evidence: **PASS_SCOPED for rejected-analysis answer selection**, not a claim that Nusantara Core is complete or live-verified. Overall discovery remains PARTIAL with the four remaining top blockers documented.

No additional human decision was necessary for this fix under the supplied contract. A future restart/reload/deployment or protected-resource/provider operation requires an explicit human decision. No such action is prepared or executed here. The next useful bounded Core objective is a no-write inspection-plan preview for broad human engineering goals; it is a recommendation, not an automatic next phase.

Runtime Identity NOT_VERIFIED; ACTIVE_PROCESS_BUILD NOT_DIRECTLY_VERIFIED; Complete Build Provenance NOT_VERIFIED; Provider Runtime Identity NOT_VERIFIED. Existing R2-A8 BLOCKED / NOT_VERIFIED and R2-A9 HOLD remain unchanged. These known limitations do not block unrelated safe development.

STOP. No further phase, live operation or assurance gate was initiated.
