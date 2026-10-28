# DevCore Human Goal → Real Inspection Plan Integration

Date: 2026-10-08. **Final status: PASS_SCOPED — application-source integration and isolated DevCore validation.** No running service was loaded/restarted or observed. This is not a claim that the existing live process has loaded the change, or that Nusantara is complete.

## Objective and authority

Governing contract: `C:\Users\dmaza\.codex\attachments\3fddfbc0-0905-4ccd-8d73-473545866f76\Pasted text.txt`. It authorizes minimum DevCore integration/testing while prohibiting planning from becoming execution. The previous report-owned prototype was reviewed as design evidence only; production imports no report module and its historical tests are not counted as new results.

Repository: `C:\Users\dmaza\mcp-starter`; branch `codex/fullroot-control-20261007`; HEAD `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. Before/after branch and HEAD are unchanged, staging remains empty. Inherited dirty worktree preserved.

## Discovery and minimum integration point

Read-only graph query before edits:

```powershell
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify query 'DevCore router DevPlan handle inspection preview' --budget 1000
```

Graph returned DevPlan/router/core/workspace/test relationships, with explicit truncation. Actual source inspection established the change points: router accepts concrete file/find/list requests; DevCore then resolves source tools and optionally generates grounded analysis. General goals have no terminal preview branch. Generic `cari` can misinterpret `masalah` as a filename. Existing response contains handled/intent/original/normalized/request/session/tool/verification/answer fields; the new preview is additive.

Inspected existing tests and current rejected-model handling; compared the historical preview's fields, templates and boundaries. Only three application files are necessary, identified before editing: router for goal intake, core for terminal response/audit, and one pure helper for interpretation/planning/classification. No new architecture, authority owner, tool or subsystem is introduced.

## Before → after

Before: no real DevCore general-goal inspection-preview integration.

After: actual `DevCore.handle()` routes the five supported goals through deterministic interpretation, bounded plan and boundary classification, then returns a structured `inspection_preview` plus its readable JSON representation in the existing `answer`. The branch returns before source resolution, tool execution or model callbacks. Existing request/session identifiers and metadata-only `dev.request` audit are retained. Preview audit records target/status and `model=NOT_INVOKED`, not goal/source/plan content.

| Supported goal | Target | Plan |
| --- | --- | --- |
| Perbaiki RAG Nusantara | RAG | Configuration schema → retrieval/evidence → grounding boundaries |
| Periksa kenapa jawaban AI kurang akurat | Core | Answer branches → RAG/DevCore grounding → evidence needs |
| Buat Nusantara lebih cepat | Core | Timeout consumers → blocking dependencies → benchmark design prerequisites |
| Periksa konfigurasi provider | Configuration | Schema → effective owner → provider selection/binding |
| Cari masalah pada Developer Engine | Developer Engine | Goal routing → workspace boundaries → grounding/answer |

All required fields are present: goal, understanding, intent, target, discovery, likely_files, plan, expected_evidence, risk, write/runtime/provider/database requirements, human_decision, next_step. Additional status/root_cause/requirements-scope/boundary fields prevent misleading certainty. Root cause is UNKNOWN. Candidate files are marked CANDIDATES_NOT_INSPECTED: the preview does not claim file existence or root cause in an arbitrary workspace. The next step first confirms these candidates during a separately scoped inspection.

LOW and NO requirements refer only to the proposed next static inspection. Ultimate goal-resolution requirements remain UNKNOWN_PENDING_DISCOVERY. No model is required to plan. No inspection step runs automatically. `authorized_operations` is always empty.

Unrecognized engineering goals such as “Buat AI lebih pintar” return CLARIFICATION_REQUIRED, UNKNOWN target/risk, and no plan. Existing ordinary chat stays unhandled. Explicit source/find/list requests retain their existing route and safety controls. Finite reviewed templates are deliberately not a general natural-language interpreter.

Restart/reload/deploy/activate/delete/reset/authorize and recognized provider/database/external-operation wording return HUMAN_DECISION_REQUIRED, no authorized plan or tool call. Runtime/provider/database requirements become YES where the requested operation is explicit; unproved requirements remain UNKNOWN. Mixed operation plus file-reference requests remain blocked. Negated dangerous wording is conservatively stopped rather than interpreted as authorization.

Compatibility detail: the existing Indonesian “ubah/hapus <source file>” read-only review/refusal remains supported when no lifecycle/provider/authority/protected-state terms occur. It can read the explicit source through the existing tools but never writes; the existing refusal explains approval is required. Explicit English `delete` stops at HUMAN_DECISION_REQUIRED, including with a source reference. Database/index/RAG/WAL/SHM deletion wording does not use this compatibility exception. This is not a write capability.

## Exact changes

- `app/devcore/inspection.py` — new pure helper and five reviewed templates; UNKNOWN/clarification and restricted-operation classification. No I/O, provider/application composition or report dependency.
- `app/devcore/router.py` — additive optional preview field in DevPlan and narrow preview routing ahead of generic find matching; existing read/find/list code preserved.
- `app/devcore/core.py` — terminal preview response plus existing audit metadata; existing analysis, grounding rejection, modification refusal and fallback logic unchanged.
- `tests/v2/test_devcore_inspection.py` — new actual DevCore integration tests over temporary empty workspaces with no-operation sentinels for model/backend/tools/source resolution.
- Generated graph outputs/backups — authorized AST-only synchronization. Prior curated outputs backed up by graphify.
- Fresh report directory — runner, tests/evidence, before snapshots, task-relative diff and this report.

No provider/model implementation, RAG implementation/data, database/WAL/SHM, existing test, configuration, UI, public endpoint, policy, gate or authorization record was edited. `/v1/chat`, `/v2/chat`, `/v2/dev` remain unchanged. Existing `/v2/dev` statically returns DevCore's dictionary; no HTTP or endpoint test was performed, and endpoint behavior is not independently verified here.

## New tests and commands

Interpreter: project `.venv\Scripts\python.exe`, Python 3.13.15; pytest 9.1.1. Only existing dependencies used. Report-owned runner disables plugin autoload and selects existing pytest_asyncio explicitly; cache/bytecode disabled, temporary fixtures report-owned. Network, real HTTP, provider/knowledge/API/operator imports, subprocess, SQLite/protected-file opens and approval mutations are blocked. The only socket exception is Windows stdlib's exact local asyncio socketpair, not a service connection. All guard results have zero violations.

Commands from repository root:

```powershell
& '.\.venv\Scripts\python.exe' -B 'docs\reports\devcore-goal-integration-20261008-c83f7a21\isolated_runner.py' focused
& '.\.venv\Scripts\python.exe' -B 'docs\reports\devcore-goal-integration-20261008-c83f7a21\isolated_runner.py' regression
```

Each command's output was redirected to its corresponding `*_OUTPUT.txt`. Actual selected IDs are in `*_SELECTED_IDS.json`; results are in `*_RESULTS.xml`; guards in `*_GUARDS.json`.

| Source revision / run | Passed | Failed/errors | Skipped | Deselected | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial focused | 25 | 0 | 0 | 0 | 0 |
| Initial regression | 18 | 0 | 1 | 0 | 0 |
| Intermediate focused, added protected-mutation/file-ref case | 26 | 0 | 0 | 0 | 0 |
| Intermediate regression | 18 | 0 | 1 | 0 | 0 |
| **Final focused, explicit delete/file-ref boundary** | **27** | **0** | **0** | **0** | **0** |
| **Final regression** | **18** | **0** | **1** | **0** | **0** |

Final total: **45 passed, 1 skipped**. Earlier runs are preserved as `initial-*` and `intermediate-*`; counts are not added together. Reruns were justified by added mixed-operation cases and stricter boundary logic. No failed test or assertion was suppressed. One multi-file patch application was rejected because its expected context did not match; it made no edits, and was reapplied against the actual lines. No test failed in these runs.

Final focused tests cover all five goals through real DevCore, required fields and answer projection, terminal no-tool/model behavior, audit metadata/content exclusion, three unknown goals, fourteen restricted/mixed/negated goals, explicit runtime/provider/database requirements, normalization/independent response state, existing router modes and ordinary chat. Regression uses the actual unchanged `tests/v2/test_devcore.py` and `tests/v2/test_devcore_grounding_response.py`, including source inspection, find/list, path boundaries, modification refusal, unsupported-analysis exclusion and unavailable-model fallback. Their model callbacks are synthetic fixture functions, never provider calls.

The skipped test is the existing outside-workspace symlink test: Windows lacks symlink creation privilege. It is not counted as PASS. No browser, full suite, API/live service or human test was run.

## Graph and diff review

AST-only command (initial then final synchronization after boundary refinement):

```powershell
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify update . --no-cluster
```

Actual logs are `initial-GRAPH_UPDATE.txt` and `GRAPH_UPDATE.txt`. No clustering/semantic provider work was invoked; graph is navigation evidence, not runtime identity. Graphify backed up curated output. It warns that five inherited report directories cannot be enumerated and some unsupported extensions are skipped; no permission repair or workaround was performed.

`FILES_BEFORE.json` captures 386 preexisting non-protected files. `PRESERVATION.json` compares their actual before/after bytes; only the two authorized existing application files and generated graph JSON/report may differ. New helper/test are separately enumerated. This bounded inventory does not hash protected data or establish full build identity.

`TASK_DIFF.patch` compares source against exact task-start snapshots, preserving inherited changes. `INHERITED_HEAD_DIFF.txt` is explicitly a cumulative HEAD diff and must not be mistaken for this task's contribution. `GIT_BEFORE.txt`, `GIT_AFTER.txt`, `GIT_DELTA.json` record observable state; only scoped files/report artifacts and generated graph changes are attributable to this task. Git also warns about five inaccessible inherited report directories and LF/CRLF conversion on a future Git write; no Git mutation or permission change occurred.

## Risk, limitations and stop

Planning adds no execution authority or second authority source. The goal catalog and lexical risk detection are bounded to reviewed patterns; unrecognized paraphrases require clarification within the engineering vocabulary, and ordinary non-DevCore requests retain existing routing. This helper is not a replacement for governance or an exhaustive natural-language security parser. Candidate paths/diagnoses need future inspection. Live endpoint/service loading and behavior are NOT_VERIFIED.

No production HTTP, provider health/model-list/generation, database/protected-state access, embedding, index rebuild, service lifecycle, activation, permit, ARM/EXECUTE, IPC or external consequential operation occurred. No dependency was installed. No gate or assurance phase was created. Changes were not staged/committed/deployed.

Preserved statuses:

- R2-A14: BLOCKED / KNOWN LIMITATION.
- Runtime Identity: NOT_VERIFIED.
- ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED.
- R2-A8: BLOCKED / NOT_VERIFIED.
- R2-A9: HOLD.

**STOP after integration, focused validation and evidence review.** Preview is not authorization. No generated inspection plan or implementation phase begins automatically; further work requires its own appropriate scope/human decision.
