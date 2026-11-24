# Nusantara V1 Engineering Closure Report

- Branch: `codex/engineering-closure-20261124`
- Worktree: `/data/workspace/nus-v1-engineering-closure-20261124/worktrees/closure`
- WP baseline HEAD: `a91db2e62ac8b1d30eec86e2300f911713a06a21`
- Engineering objective: close inherited V1 regression IDs without V2 activation, rewrite, threshold weakening, authorization bypass, or production changes.
- Overall engineering status: **CONDITIONAL FOR REVIEW / NO-GO FOR PRODUCTION**.

## Summary

| Work package | Status | Evidence |
|---|---|---|
| WP-01 Release consolidation | PASS | `RELEASE_CONSOLIDATION_REPORT.md` |
| WP-02 Cross-platform portability | PARTIAL | `CROSS_PLATFORM_ACCEPTANCE_REPORT.md` |
| WP-03 Regression remediation | PARTIAL, no new IDs | `FULL_REGRESSION_CLOSURE_REPORT.md` |

- Full regression: `2 failed, 1605 passed, 82 skipped, 1086 warnings, 1 error`.
- ID diff versus WP-02 baseline: `baseline_ids 62`, `current_ids 3`, `new_ids 0`, `fixed_ids 59`.
- Remaining three IDs are all external blockers: missing configured operator credential and missing approved IndoBERT/Docling worker.
- No mandatory V1 test was deleted, skipped by edit, or weakened to achieve this result.

## Security and runtime invariants

- No V2/V3/V4 endpoint was activated; V1 runtime still has no `/v2` routes.
- No authorization, Human Approval, Fullroot Control or audit control was disabled.
- No relevance threshold, acceptance threshold or retrieval behavior was weakened.
- No real secret, PII, SOP upload, DB dump or operator credential was introduced.
- No active service, database, volume, model or production port was changed.
- PR #19 remains OPEN/MERGEABLE; merge and deploy were not performed.

## Remaining blockers

1. Approved IndoBERT/Docling worker is absent at `backend/nusantara-models/.venv/bin/python`; two retrieval IDs remain blocked.
2. Live evaluation harness needs an owner-configured operator credential; one collection error remains.
3. Windows-native IPC cases, R2 owner artifact hash authenticity, R3 Windows evidence path, PIAK-03 official SOP, Ollama topology decision and PR merge/deploy approvals require owner/PC/CI action.

See `PC_VPS_ACCEPTANCE_CHECKLIST.md` for the full environment split.

## Decision

- **Code review**: CONDITIONAL — the engineering tree has no new regression IDs and all VPS-closeable defects were remediated.
- **Production release**: NO-GO — approved worker, knowledge artifacts, operator credential, PC/Windows evidence and owner approvals are still required.
- Do not merge, deploy, restart active services, force push, or mark production-ready until every blocker in `PC_VPS_ACCEPTANCE_CHECKLIST.md` is resolved or formally accepted by the owner.

## Required next actions

1. Supply approved IndoBERT/Docling artifacts and re-run the two blocked retrieval tests.
2. Supply or authorize the evaluation-harness operator credential and re-run `tests/evaluation/test_live_harness.py`.
3. Complete Windows PC/CI validation for the 37 skipped native IPC cases.
4. Resolve R2 owner-hash and R3 Windows evidence provenance; provide official PIAK-03 SOP.
5. Decide Ollama production topology and re-run Docker staging against the exact final commit.
6. Obtain approval for PR #19 merge and any production deployment.
