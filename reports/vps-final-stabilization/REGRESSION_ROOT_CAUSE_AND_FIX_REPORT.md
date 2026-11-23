# Regression Root Cause and Fix Report — Nusantara V1

- Commit SHA: `d2cfc60a0d88c93ce561f40c01d67e5f53910770`
- Branch: `codex/vps-final-stabilization-20261123`
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Collected: 2026-11-23T22:15:57Z–22:19:20Z

## Gate D verdict

**PASS (no new regression; fix verified) / BLOCKED (full-suite green)** — the release candidate has zero new failing/error IDs versus the independent baseline, the `/readyz` fix is red→green, and the admin-ingest channel fix remains intact. Full suite remains blocked by 134 known IDs and by environment/fixture dependencies that require owner decision.

## Fix applied in this phase

| Item | Before | After | Evidence |
|---|---|---|---|
| Canonical readiness alias | `GET /readyz` 404 in active runtime | Additive alias to `readiness_check`; red `assert 404 == 200`, green contract suite `6 passed` | `d_readyz_red`, `d_readyz_green`, commit `d2cfc60a` |
| Live isolated alias | Not available in active runtime (no deploy performed) | Isolated RC `/readyz` HTTP 200, same body as `/v1/health/ready` | `c_readyz_alias`, `c_v1_ready` |
| Admin ingest boundary | PR #17 fix retained | `admin_api` forced after caller metadata merge; auth/approval tests unchanged | `b_diff_names`, `d2_targeted` |

No test was deleted, skipped, weakened, or downgraded. No new dependency was installed.

## Test matrix

| Suite | Command key | Result | Exit |
|---|---|---|---|
| Full regression (first attempt) | `d2_full_regression` | Interrupted: `collected 1675 items / 2 errors` because `--continue-on-collection-errors` was omitted | 2 |
| Full regression (comparable rerun) | `d2_full_regression_continue` | `85 failed, 1482 passed, 62 skipped, 1076 warnings, 48 errors in 22.72s` | 1 |
| Targeted P0/P1 | `d2_targeted` | `5 failed, 238 passed, 459 warnings in 6.75s` | 1 |
| Synthetic RAG optional env | `d2_synthetic_langchain` | `3 passed, 24 warnings in 0.13s` | 0 |
| Frontend unit | `d2_frontend_test` | `3 failed, 218 passed (221)` | 1 |
| Frontend build | `d2_frontend_build` | `built in 2.19s`, 451 modules | 0 |
| Ruff scoped current | `d2_ruff_scoped` | `Found 2097 errors.` | 1 |
| Ruff scoped baseline | `d2_ruff_scoped_baseline` | `Found 2097 errors.` | 1 |
| Mypy app current | `d2_mypy_app` | `Found 1370 errors in 179 files` | 1 |
| Mypy app baseline | `d2_mypy_app_baseline` | `Found 1370 errors in 179 files` | 1 |
| HTTP synthetic ingest | `d2_synthetic_ingest` | HTTP 400, missing IndoBERT worker python | 0 |
| HTTP synthetic search | `d2_synthetic_search` | HTTP 500, same worker error in backend log | 0 |
| HTTP grounded chat | `d2_synthetic_chat` | HTTP 422 `DOCUMENT_NOT_INDEXED` | 0 |

Counts use the same tool versions on both sides. The earlier independent report quoted different static-analysis totals because it used a different invocation/version; the apples-to-apples comparison here is current-vs-baseline with the same `ruff 0.17.6` and `mypy 2.4.1`.

## Regression delta

- Current failing/error IDs: `134`.
- Independent baseline failing/error IDs: `134`.
- New IDs vs baseline: `0`.
- Fixed IDs vs baseline: `0`.
- Full-suite gate: still **BLOCKED** by the same 134 IDs; no claim of green suite is made.

The two collection errors are also present in the baseline:
1. `tests/evaluation/test_live_harness.py` — `scripts/run_eval.py` requires a `.env` with `NUSANTARA_ADMIN_TOKEN`; no real credential was created.
2. `tests/test_developer_control.py` — expects deleted root `developer.py`.

## Root causes and disposition

| Residual | Root cause | Disposition |
|---|---|---|
| 3 × `test_privileged_api_denies_before_access[/v2/dev...]` | Test expects V2 route to exist and return 403; V1-only runtime intentionally does not register `/v2/dev`, so 404 is returned | No source fix: re-enabling V2 would violate V1-only scope. Test expectation change requires owner decision |
| `test_authorized_developer_lists_workspace` | Test posts to `/v2/dev`, absent in canonical V1-only tree | No source fix; same owner decision as above |
| `test_synthetic_retriever_exposes_evidence_to_langchain` (main env) | Optional LangChain dependency absent from main env; same test passes in `env-langchain` | No dependency added per constraint; environment-scoped PASS recorded |
| Frontend 3 failures | Archived fixture files are absent from canonical tree: `REMAINING_GATES.json`, `IMPLEMENTATION_REPORT.json`, `OWNER_DECISION.json` | No fixture reintroduced; owner must decide whether to restore/archive-align |
| HTTP synthetic ingest 400 / search 500 / chat 422 | No `nusantara-models/.venv/bin/python` or `indobert_worker.py` in any workspace; log shows `FileNotFoundError` at `indobert_client.start()` | Environment artifact blocker, not code regression; PC/owner must supply approved IndoBERT model artifacts |
| Ruff 2097 / Mypy 1370 | Legacy debt with identical counts and message sets on baseline and RC; Ruff diff is only 3 line-number shifts in `backend/app/main.py` from the added decorator | No new static-analysis debt; no mass reformat, no threshold change |
| `d2_full_regression` first attempt | Missing pytest flag | Rerun correctly as `d2_full_regression_continue`; first attempt retained as evidence |

## Command evidence index

Primary evidence: `d_readyz_red.*`, `d_readyz_green.*`, `d2_copy_test_db.*`, `d2_full_regression.*`, `d2_full_regression_continue.*`, `d2_targeted.*`, `d2_synthetic_langchain.*`, `d2_frontend_test.*`, `d2_frontend_build.*`, `d2_ruff.*`, `d2_ruff_scoped.*`, `d2_ruff_scoped_baseline.*`, `d2_mypy.*`, `d2_mypy_scoped.*`, `d2_mypy_scoped_baseline.*`, `d2_mypy_app.*`, `d2_mypy_app_baseline.*`, `d2_synthetic_ingest.*`, `d2_synthetic_search.*`, `d2_synthetic_chat.*`, `runtime/isolated/logs/backend.log`. All timestamps, exit codes, and full commands are in `evidence/commands.tsv`.
