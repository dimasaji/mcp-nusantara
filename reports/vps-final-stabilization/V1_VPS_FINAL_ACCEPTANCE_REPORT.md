# V1 VPS Final Acceptance Report — Nusantara V1

- Final verdict: **GO FOR REVIEW**
- Code under review: `d2cfc60a0d88c93ce561f40c01d67e5f53910770`
- Branch: `codex/vps-final-stabilization-20261123`
- Base/active commit: `b44b01e7d24efbd5ff7f4830cc71624b5aa4bf7f`
- Evidence bundle commit: `aed48220cc8e0088a2a5aa66191cc4d9a6886f6c`
- Pull request: #18 — https://github.com/dimasaji/mcp-nusantara/pull/18 (MERGED)
- Post-review actions: `VPS_DEPLOYMENT_RECORD.md`
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Generated: 2026-11-23T22:24:30Z

## Verdict rationale

The RC was ready for code review: all must-pass stabilization gates were complete or explicitly bounded, no new regression was introduced, the `/readyz` fix was red→green, admin authorization was intact, and a reviewable branch/PR was produced. At review time deployment was not authorized; after explicit owner confirmation, PR #18 and #17 were merged and an in-place deploy was executed and recorded in `VPS_DEPLOYMENT_RECORD.md`. The final verdict remains GO FOR REVIEW.

## Gate summary

| Gate | Result | Evidence |
|---|---|---|
| A — forensic baseline | COMPLETE | `VPS_FORENSIC_BASELINE.md` |
| B — git/PR reconciliation | PASS | `GIT_RELEASE_RECONCILIATION.md` |
| C — isolated runtime recovery | PASS | `VPS_RUNTIME_RECOVERY_REPORT.md` |
| D — regression/root cause | PASS for no-new-regression; full-suite green blocked by known IDs | `REGRESSION_ROOT_CAUSE_AND_FIX_REPORT.md` |
| E — security/data integrity | PASS | `VPS_SECURITY_AND_DATA_INTEGRITY_REPORT.md` |
| F — knowledge/PC boundary | Boundary verified; official acceptance PC-bound | `KNOWLEDGE_VPS_BOUNDARY_REPORT.md`, `PC_PIAK03_ACCEPTANCE_HANDOFF.md` |
| G — release/rollback | Plan complete; deploy not authorized | `VPS_RELEASE_AND_ROLLBACK_PLAN.md` |
| H — final acceptance | GO FOR REVIEW | This report, `TEST_RESULTS.json` |

## Source changes under review

- `backend/app/main.py`: additive `GET /readyz` alias to `readiness_check` (+1 line).
- `tests/test_readyz_contract.py`: contract test (+34 lines).
- Ten evidence reports under `reports/vps-final-stabilization/` (ignored by `.gitignore:76`, to be added explicitly).
- No dependency, framework, service, DB schema, migration, threshold, or production configuration change.

`g_release_diff`: `2 files changed, 35 insertions(+)` from active `b44b01e7`.

## Verification highlights

- Red/green readiness: `d_readyz_red` exit `1` (`assert 404 == 200`); `d_readyz_green` exit `0` (`6 passed in 0.36s`).
- Isolated runtime: backend `18211`, frontend `15284`; `/health` and `/v1/health` 200; `/readyz` 200 degraded with `documents=0`; canonical model status 200 `INFERENCE_VERIFIED`; synthetic chat `PONG` 200; frontend proxy and build pass.
- Full regression: `85 failed, 1482 passed, 62 skipped, 1076 warnings, 48 errors in 22.72s`; `134` failing/error IDs in both current and independent baseline; `new_ids=0`, `fixed_ids=0`.
- Targeted: `5 failed, 238 passed` (same known V2/fixture residuals); synthetic LangChain env `3 passed`.
- Frontend: `3 failed, 218 passed` (archived fixture residuals); build `built in 2.19s`.
- Static: current vs baseline Ruff `2097 = 2097` (only 3 line shifts in `backend/app/main.py`); Mypy `1370 = 1370` with `new=0`, `fixed=0`.
- Security: missing/invalid admin token → HTTP 403; valid token cost summary → 200 `UNAVAILABLE` as designed; targeted security/audit `4 failed, 65 passed` with only known V2 IDs.
- Data: active DB mtime/hash unchanged from forensic snapshot; `quick_check=ok`, `9` tables; no DB write, migration, deletion, or overwrite.
- Cleanup: isolated PIDs stopped; ports `18211`/`15284` free; active `18201`/`15274`/Ollama `11434` untouched.

## Accepted risks / review findings

1. Full suite is not green: 134 baseline failures/errors remain; no new IDs. Do not merge as a claim of clean suite.
2. Official SOP acceptance is not available on VPS: `knowledge=NOT_VERIFIED`, `official_oracle=REVIEW_REQUIRED`, `approval=REVIEW_REQUIRED`, `documents=0`.
3. Docker image has review defects: empty `scripts/healthcheck.py`, missing IndoBERT worker copy/mount, mostly unpinned pip install, compose port `8000` vs active `18201`/`15274`, and unused Postgres/Redis services.
4. `scripts/verify_sop_conversation.py` expects legacy `/v1/frontend/model-status` (404 on RC); PC harness must use the canonical `/v1/control-plane/model-status` or an approved proxy route.
5. Reports are ignored by `.gitignore:76 reports/*`; they must be force-added to the PR.

## Actions at acceptance time (before explicit later authorization)

- No PR merged, closed, rebased, or force-pushed at that time.
- No shared history rewritten; no hard reset.
- No active service restarted; no port changed.
- No deploy performed; no image built or pushed.
- No DB deleted, overwritten, migrated, or restored.
- No real secret, `.env`, personal data, SOP PDF, manifest, model artifact, or DB dump printed or uploaded.
- No test disabled, skipped by edit, or weakened; no threshold lowered.
- No new framework, service, or runtime dependency added.

## Post-review actions (explicitly authorized)

- PR #18 and PR #17 were merged with merge commits; integration branch reached `b77c9c6e3d547b1d5a34c633abd0fb01e5aef046`.
- Active repo was fast-forwarded to that commit; backend was restarted in place on the same port `18201` with the same env and DB path; new PID `19130`.
- Frontend PID `7740`, ports `15274`/`11434`, DB hash/mtime, and secrets were unchanged.
- Docker compose was not used; official PIAK-03 acceptance remains PC-bound. Full detail: `VPS_DEPLOYMENT_RECORD.md`.

## Review handoff

Reviewers should focus on the readiness alias, the contract test, the evidence bundle completeness, and the Docker deployment findings. Owner approval for an in-place deploy was obtained after review and is recorded in `VPS_DEPLOYMENT_RECORD.md`; PC PIAK-03 `GO` and resolution of the Docker preconditions in `VPS_RELEASE_AND_ROLLBACK_PLAN.md` remain necessary for container/production rollout.

## Evidence index

The full evidence bundle is included at `reports/vps-final-stabilization/evidence/` (308 files, including `commands.tsv` and all `a_*`, `b_*`, `c_*`, `d2_*`, `e_*`, `f_*`, `g_*`, `h_*` outputs). Deployment evidence is bundled separately at `reports/vps-final-stabilization/deployment-evidence/`. Original collection path: `/data/workspace/nus-v1-vps-final-20261123/evidence/`. Structured summary: `reports/vps-final-stabilization/TEST_RESULTS.json`.
