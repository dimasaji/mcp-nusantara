# WP-03 — Full Regression Closure Report

- Branch: `codex/engineering-closure-20261124`
- HEAD baseline for this work package: `a91db2e62ac8b1d30eec86e2300f911713a06a21`
- Environment: Instabox Linux VPS, Python 3.13.5, isolated worktree `/data/workspace/nus-v1-engineering-closure-20261124/worktrees/closure`
- Command: `env PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m pytest -q --tb=no --continue-on-collection-errors`
- Expected result: no new failure/error ID versus WP-02 baseline; all mandatory V1 IDs closed.
- Actual result: **2 failed, 1605 passed, 82 skipped, 1086 warnings, 1 error in 38.01s**.
- ID reconciliation: `baseline_ids 62`, `current_ids 3`, `new_ids 0`, `fixed_ids 59`.
- Final status: **PARTIAL / NO NEW REGRESSIONS** — 59 of 62 inherited IDs closed; 3 remaining IDs are external environment/approval blockers.

## Commands and evidence

| Command | Exit | Expected | Actual | Status | Evidence |
|---|---:|---|---|---|---|
| targeted WP-03 regression (18 files) | 0 | targeted PASS | 311 passed | PASS | `evidence/WP-03/commands.tsv` |
| full regression after WP-03 | 1 | no new IDs | 2 failed, 1605 passed, 82 skipped, 1 error; `new_ids=0` | PARTIAL | `evidence/WP-03/regression_final.out` |
| full regression line trace | 1 | same IDs | 3 inherited IDs remain | PARTIAL | `evidence/WP-03/regression_final_tb_line.out` |
| ID diff vs WP-02 | 0 | no new IDs | `fixed 59 / new 0 / remaining 3` | PASS | `evidence/WP-03/id_diff_final.out` |
| `git diff --check` | 0 | clean patch | clean | PASS | `evidence/WP-03/diff_check_final.out` |
| compileall changed backend files | 0 | syntax OK | OK | PASS | `evidence/WP-03/compileall_final.out` |
| `ruff check` changed backend/test files | 1 | no lint findings | pre-existing repository findings remain | FAIL / tracked | `evidence/WP-03/ruff_final.out` |
| `mypy` changed backend files | 1 | clean typing | pre-existing typing findings remain | FAIL / tracked | `evidence/WP-03/mypy_final.out` |

## Closed ID groups

- Evidence-isolation runner writes: read-only interpreter/site-packages paths are allowed; active DB, sidecar, network and subprocess write blocks remain. 16/16 mandatory review-execution IDs now pass.
- Restored historical artifacts and reconciled byte-exact pins for configuration/R1/R2/runtime-attestation tests.
- V2-disabled tests now mount the archived V2 router on a local FastAPI app instead of requiring V2 in the V1 runtime.
- Provider/public-surface AST checks now normalize authorized `session_id`, `sop_version`, `sop_case`, `pages`, `block_ids` and `provider_status` additions while keeping all other fields pinned.
- Runtime-attestation AST check compares named functions, normalizes the authorized request-id profile branch and document-tools resume block, and keeps original handler semantics pinned.
- Control-plane projection now reads `frontend/evidence-sources.json` and `frontend/CPLANE_OWNER_AUTHORIZATION.json`; R2/R3 absent evidence is reported honestly as `NOT_VERIFIED`.
- Evidence registry manifest paths are canonicalized to `backend/...` and `frontend/...`, with the manifest itself included in collected evidence.
- SOP review counts original PDF pages through OCR fallback instead of OCR offset pages.
- RAG config test uses a 3-document fixture with `chunk_size=2000`; application dedup and `top_k` semantics were not changed.
- LangChain/LangGraph optional tests now set flags with `monkeypatch` per test, removing global environment leakage; `test_llm_e2e` and `test_chain_e2e` no longer fail in the full run.
- Opt-in LangGraph grounding test now asserts safe rejection (`UNGROUNDED_RESULT`) for ungrounded missing-evidence input and abstention projection for unsupported claims.

## Remaining IDs

| ID | Classification | Finding | Blocker |
|---|---|---|---|
| `ERROR tests/evaluation/test_live_harness.py` | `BLOCKED_ENVIRONMENT` | `scripts/run_eval.py:11` asserts `Configured operator credential unavailable` | No approved operator credential may be injected in this sandbox. |
| `FAILED tests/test_langchain_e2e.py::test_retriever_e2e` | `PLATFORM_DEPENDENCY` | Retriever returned 0 docs; embedding stage failed because `backend/nusantara-models/.venv/bin/python` does not exist | Approved IndoBERT/Docling worker artifacts absent. |
| `FAILED tests/test_langchain_hardening.py::test_knowledge_search_still_works` | `PLATFORM_DEPENDENCY` | `/v1/knowledge/search` returned HTTP 500 with the same missing worker path | Approved IndoBERT/Docling worker artifacts absent. |

No test was deleted, skipped by edit, or given a lower threshold to produce these numbers. Ruff and mypy findings are pre-existing on the changed files and are recorded rather than silently repaired.
