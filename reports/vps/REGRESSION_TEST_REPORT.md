# Regression Test Report — Nusantara V1 VPS

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Execution Phase: `Phase 3 — Regression Closure`
- Date: `2026-11-24`
- Worktree: `/data/workspace/nus-v1-vps-master-20261124/worktrees/engineering`
- Branch / commit: `codex/vps-master-engineering-20261124` @ `cfd46391`
- Method: reconcile existing regression evidence and run targeted portability/runtime tests. Full regression was **not rerun** on this branch because its base `545137e8` predates the open remediation PR #20; doing so would reproduce known stale failures rather than verify the latest remediation tree.

## 1. Targeted tests executed here

```bash
env PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m pytest -q \
  tests/test_runtime_portability.py \
  tests/test_backend_runtime_fixture.py \
  tests/test_runtime_readiness.py \
  tests/test_runtime_build_provenance.py
```

Result: **39 passed, 0 failed, 18 warnings**.

This covers the Linux/portability/runtime/build-provenance surface introduced or affected by the sync work. It does not claim full regression PASS.

## 2. Authoritative closure baseline

Source: `reports/engineering-closure/FULL_REGRESSION_CLOSURE_REPORT.md` on branch `codex/engineering-closure-20261124` @ `a91db2e6` baseline / final `3f517294`.

Command used there:

```bash
env PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python \
  -m pytest -q --tb=no --continue-on-collection-errors
```

Result: **2 failed, 1605 passed, 82 skipped, 1086 warnings, 1 error**.

ID reconciliation versus WP-02 baseline:

- `baseline_ids = 62`
- `fixed_ids = 59`
- `new_ids = 0`
- `remaining_ids = 3`

Conclusion from that report: **PARTIAL / NO NEW REGRESSIONS**.

## 3. Classification of remaining failures

| ID | Classification | Finding | Owner / gate |
|---|---|---|---|
| `ERROR tests/evaluation/test_live_harness.py` | `BLOCKED_ENVIRONMENT` | `Configured operator credential unavailable` | owner credential required |
| `FAILED tests/test_langchain_e2e.py::test_retriever_e2e` | `PLATFORM_DEPENDENCY` | embedding worker path `backend/nusantara-models/.venv/bin/python` absent | approved IndoBERT/Docling artifacts required |
| `FAILED tests/test_langchain_hardening.py::test_knowledge_search_still_works` | `PLATFORM_DEPENDENCY` | `/v1/knowledge/search` HTTP 500 from same missing worker path | approved IndoBERT/Docling artifacts required |

No test was deleted, edited to skip, or given a lower threshold to produce these results. Ruff and mypy findings on changed files are pre-existing and recorded, not silently repaired.

## 4. Frontend unit test on this branch

Command: `npm test` in `frontend/` via temporary `node_modules` symlink.

Result: `218 passed`, `3 failed`, `28 files passed`, `1 failed`, duration `7.83s`.

Failed cases in `src/__tests__/engineering-console.test.tsx`:

| Test | Missing path |
|---|---|
| `opens the evidence bundle for the new release gates` | `docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json` |
| `opens the full regression report from the evidence index` | `docs/reports/openrouter-workflow-20261009T184538/IMPLEMENTATION_REPORT.json` |
| `navigates using the human console recovery index` | `docs/reports/human-console-recovery-20261009T200537/README.md` |

Git history shows those generated report files were removed by `0b48db2a chore: clean up git tracking - remove generated reports, caches, temp, and backup files`. Classification: `BLOCKED_EVIDENCE_FIXTURE`, pre-existing on base `545137e8`, not introduced by Phase 0–3 work. Tests were not weakened, skipped, or edited. Owner decision is required: restore the fixtures or approve updating the tests to current evidence paths.

## 5. Other reconciliation evidence

- `reports/final-consolidation/VERIFICATION_SUMMARY.md` — targeted `133 passed`; full `89 failed, 1466 passed, 62 skipped, 49 errors`; 30 fixes retained, 0 new failure IDs.
- `reports/final-consolidation/V1_VPS_REGRESSION_DELTA.md` — targeted `133 passed, 119 warnings`.
- `reports/final-consolidation/RELEASE_GO_NO_GO.md` — regression verdict `PARTIAL`; production `NO-GO`.
- `reports/engineering-closure/V1_ENGINEERING_CLOSURE_REPORT.md` — overall `CONDITIONAL FOR REVIEW / NO-GO FOR PRODUCTION`.

## 6. Verdict

- New regressions introduced by Phase 0–3 work: **0**.
- Targeted backend tests on this feature branch: **PASS**.
- Frontend unit tests on this feature branch: **PARTIAL** — `218 passed`, `3 failed` on missing historical evidence fixtures.
- Full regression: **PARTIAL** based on authoritative closure evidence; 59/62 inherited IDs closed, 3 external blockers remain.
- Phase 3 status: **PASS for no-new-regression on this branch; PARTIAL for release readiness**.

## 7. Required before release

1. Supply an owner-approved operator credential and rerun `tests/evaluation/test_live_harness.py`.
2. Supply approved IndoBERT/Docling worker artifacts and rerun the two retrieval failures.
3. Re-run full regression on the exact release commit after PR #20/#21 reconciliation.
4. Complete Windows-native validation for the 37 skipped IPC cases.
5. Decide and implement restoration or approved test update for the 3 engineering-console fixture cases before relying on CI as a green gate.
