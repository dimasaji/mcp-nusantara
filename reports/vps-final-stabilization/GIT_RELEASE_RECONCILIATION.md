# Git Release Reconciliation — Nusantara V1

- Commit SHA (release candidate proposed here): `d2cfc60a0d88c93ce561f40c01d67e5f53910770` (short `d2cfc60a`)
- Base SHA: `b44b01e7d24efbd5ff7f4830cc71624b5aa4bf7f`
- Integration baseline: `ec76a9ed01f160a28d1cbe34e263b3bbe9ccb075` (PR #16 merge)
- Branch: `codex/vps-final-stabilization-20261123`
- Worktree: `/data/workspace/nus-v1-vps-final-20261123/worktrees/release`
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Collected: 2026-11-23T22:11:02Z–22:11:18Z

## Gate B verdict

**PASS** — one canonical release SHA selected, zero unexplained source conflicts, no unauthorized merge.

## Proposed release candidate

`d2cfc60a` is the proposed release candidate because it is the first commit that contains:

1. PR #16 final consolidation (`ec76a9ed`) with canonical `backend/`, `frontend/`, `deploy/docker/`, `reports/`, and `docs/reports/` layout.
2. PR #17 admin ingestion boundary fix (`db32ee40`) and V1 VPS verification reports (`b44b01e7`).
3. The isolated `/readyz` readiness-alias fix and its contract test (`d2cfc60a`), required by the Phase C acceptance contract.

The active runtime remains at `b44b01e7` on ports `18201`/`15274`. It was not restarted or updated.

## PR matrix

| PR | State | Base → head | Head SHA | Reconciliation | Evidence |
|---|---|---|---|---|---|
| #14 | OPEN | `codex/remediation-v1-20261122` → `codex/ollama-runtime-v1-20261123` | `87a58034` | Reports are present byte-identically in RC under `docs/reports/ollama-runtime-v1/`; not a direct ancestor of `ec76a9ed` because consolidation recreated the tree | `a_pr_14`, `b_ancestor_pr14`, `b_pr14_reports` |
| #15 | OPEN | `codex/ollama-runtime-v1-20261123` → `codex/vps-stabilization-20261123` | `3a361c03` | Cost-ledger race fix preserved as rename to `backend/app/models/cost_ledger.py`; report set superseded by consolidation; not direct ancestor | `a_pr_15`, `b_ancestor_pr15`, `b_pr15_cost` |
| #16 | MERGED 2026-11-23T16:57:40Z | `codex/restructure-20261123` ← final consolidation | `e7da7bcb` (tip), merge at `ec76a9ed` | Canonical restructure and all prior evidence consolidated; accepted integration baseline | `a_pr_16`, `a_git_log` |
| #17 | OPEN, MERGEABLE | `codex/restructure-20261123` → `codex/vps-eng-completion-20261123` | `b44b01e7` | Direct descendant of `ec76a9ed`; admin ingestion fix plus five V1 reports; no conflict | `a_pr_17`, `b_ancestor_pr17_base`, `b_range` |

No PR was merged, closed, rebased, force-pushed, or edited by this work.

## Commit delta from integration baseline

`git diff --name-status ec76a9ed..d2cfc60a` (`b_diff_names`, exit 0) contains only:

- `backend/app/api/routes.py` — admin ingest channel enforcement.
- `backend/app/knowledge/sop_review.py` — admin ingest exemption from pipeline review gate.
- `backend/app/main.py` — `/readyz` alias.
- Five V1 final-consolidation reports.
- `tests/test_approval_boundary.py`, `tests/test_audit_regressions.py`, `tests/test_readyz_contract.py`.

Diff stat: 11 files, 532 insertions, 10 deletions (`b_diff_stat`, exit 0).

## Worktree reconciliation

| Worktree | HEAD | State/action |
|---|---|---|
| `/data/home/mcp-nusantara` | `e218bd61` | Historical branch `codex/final-consolidation-20261123`, untouched |
| `/data/home/mcp-nusantara-integration` | `b268da1e` | Historical branch `codex/integration-v1-20261123`, untouched |
| `/data/workspace/nus-v1-postmerge-ec76a9ed/repo` | `b44b01e7` | Active runtime source, untouched |
| `/data/workspace/nus-v1-postmerge-ec76a9ed/base-head` | `dfa1c8f0` | Detached baseline, untouched |
| `/data/workspace/nus-v1-postmerge-ec76a9ed/independent-db32ee40` | `db32ee40` | Detached independent verification, untouched |
| `/data/workspace/nus-v1-staging-6f037ab4/repo` | `6f037ab4` | Detached staging, untouched |
| `/tmp/nus-restructure-check` | `b268da1e` | Stale prunable entry, not pruned |
| `/data/workspace/nus-v1-vps-final-20261123/worktrees/release` | `d2cfc60a` | New isolated release worktree used by this task |

## Canonical layout and entrypoints

- Present: `backend/`, `frontend/`, `deploy/docker/`, `reports/`, `docs/reports/` (`b_layout`, exit 0).
- Absent: root `app/` and root `control-plane/` directories (`b_no_root_app`, `b_no_root_control`, exit 0).
- Legacy path references exist only in `FINAL_CONSOLIDATION_MANIFEST.csv` as recorded deletions (`b_legacy_refs`), not in active runtime code.
- Backend entrypoint: `uvicorn --app-dir backend app.main:app` (README) and `uvicorn app.main:app` in the Docker image (`b_entrypoints`).
- Frontend scripts: `dev`, `build`, `test`, `e2e` in `frontend/package.json`.
- Env keys used by runtime: `NUSANTARA_DATA_DIR`, `NUSANTARA_KNOWLEDGE_DB`, `NUSANTARA_ADMIN_TOKEN`, `OLLAMA_BASE_URL`, `LLM_BASE_URL`, `LLM_MODEL`.

## Conflict assessment

| Potential conflict | Finding | Disposition |
|---|---|---|
| PR #14 vs #16 | Ollama evidence appears in both lineages | No conflict; identical report paths present in RC |
| PR #15 vs #16 | `app/models/cost_ledger.py` vs `backend/app/models/cost_ledger.py` | No conflict; Git detects rename and fix is retained |
| PR #17 vs #16 | Five commits on top of `ec76a9ed` | No conflict; direct descendant |
| `/readyz` alias vs existing readiness endpoints | Canonical `/v1/health/ready` and admin `/v1/runtime/readiness` already existed | New alias is additive and contract-tested; no route removed |
| Stale worktree | `/tmp/nus-restructure-check` prunable | Left untouched to avoid shared-state mutation |

## Command evidence index

Primary evidence files: `a_pr_14.*`, `a_pr_15.*`, `a_pr_16.*`, `a_pr_17.*`, `a_pr_list.*`, `b_ancestor_pr14.*`, `b_ancestor_pr15.*`, `b_ancestor_pr17_base.*`, `b_range.*`, `b_diff_stat.*`, `b_diff_names.*`, `b_top_level.*`, `b_layout.*`, `b_legacy_refs.*`, `b_entrypoints.*`, `b_pr14_vs_rc.*`, `b_pr15_vs_rc.*`, `b_pr15_cost.*`, `b_pr14_reports.*`, `b_no_root_app.*`, `b_no_root_control.*`, `b_rc_head.*`, `b_rc_status.*`, `d_readyz_red.*`, `d_readyz_green.*`, `d_readyz_diffcheck.*`. All exit codes and timestamps are in `evidence/commands.tsv`.
