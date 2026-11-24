# WP-01 — Release Consolidation Report

- Commit SHA: `b5214ce21c5a8f2dabebe6d190e47c18147ff4ec`
- Release candidate SHA: `f4f8b7f5b99f6fbd034d21149675fb625881a788`
- Previous approved integration SHA: `545137e8cfbec737488246492d59837df303cc4d`
- Environment: Instabox Linux VPS, isolated worktree `/data/workspace/nus-v1-engineering-closure-20261124/worktrees/closure`
- Engineering branch: `codex/engineering-closure-20261124`
- Expected result: satu baseline konsisten, tidak ada konflik/git drift yang hilang, rollback reference tersedia, branch dapat dibangun dan diuji.
- Actual result: baseline terverifikasi, tidak ada konflik, tidak ada dependency drift, patch lokal dipindahkan ke worktree closure, rollback refs tersedia.
- Final status: **PASS**.

## Commands and evidence

| Command | Exit | Expected | Actual | Status | Evidence |
|---|---:|---|---|---|---|
| `git fetch --all --prune --tags` | 0 | remote refresh | done | PASS | `evidence/WP-01/commands.tsv` |
| `git rev-parse HEAD` | 0 | baseline SHA | `b5214ce2...` | PASS | `evidence/WP-01/baseline_head.out` |
| `git log -1 --format=...` | 0 | commit identity | `docs: add release integration acceptance reports`, `2026-11-24T00:25:51Z` | PASS | `evidence/WP-01/baseline_log.out` |
| `git status --short --branch` | 0 | working tree known | 2 modified test files preserved | PASS | `evidence/WP-01/baseline_status.out` |
| `git remote -v` | 0 | Nusantara remote | `git@github-nusantara:dimasaji/mcp-nusantara.git` | PASS | `evidence/WP-01/baseline_remote.out` |
| `gh pr view 19 ...` | 0 | PR #19 status | OPEN / MERGEABLE, head `f4f8b7f5` | PASS | `evidence/WP-01/pr19.out` |
| `gh pr list --state all --limit 30` | 0 | PR inventory | 19 PRs listed, #16–#18 MERGED, #19 OPEN | PASS | `evidence/WP-01/pr_list.out` |
| `git merge-base --is-ancestor f4f8... HEAD` | 0 | RC is ancestor | yes | PASS | `evidence/WP-01/commands.tsv` |
| `git merge-base --is-ancestor b5214... HEAD` | 0 | report commit is ancestor | yes | PASS | `evidence/WP-01/commands.tsv` |
| `git diff --name-only --diff-filter=U` | 0 | no unresolved conflicts | empty | PASS | `evidence/WP-01/conflicts.out` |
| `git ls-files -u` | 0 | no unmerged index | empty | PASS | `evidence/WP-01/unmerged_index.out` |
| dependency file diff vs `origin/codex/restructure-20261123` | 0 | no drift | empty for pyproject/package/requirements | PASS | `evidence/WP-01/dependency_drift.out` |
| `git diff --stat origin/codex/restructure-20261123..HEAD` | 0 | known delta | Docker readiness + reports only | PASS | `evidence/WP-01/branch_diff.out` |
| `git rev-parse b5214 f4f8 545137e8` | 0 | rollback refs | all resolvable | PASS | `evidence/WP-01/rollback_refs.out` |
| `git worktree list --porcelain` | 0 | isolated worktree | closure worktree present | PASS | `evidence/WP-01/worktrees.out` |
| `git diff -- tests/test_control_plane_attestation_binding.py tests/test_runtime_attestation.py` | 0 | preserve local fix | 26-line patch carried over | PASS | `evidence/WP-01/pending_patch.out` |

## Reconciliation

- Active baseline is `b5214ce2`, which is `f4f8b7f5` plus the committed release-integration reports. No production code changed between those SHAs.
- `f4f8b7f5` contains PR #19 Docker readiness work and is a descendant of `545137e8`, `b77c9c6e`, `3e3eedcf`, and `ec76a9ed`.
- No dependency drift was found in `pyproject.toml`, `package.json`, `package-lock.json`, `requirements.txt`, `requirements-dev.txt`, `deploy/docker/requirements.txt`, or `deploy/docker/requirements-indobert.txt` relative to the integration branch.
- Prior release reconciliation identified duplicate evidence/report paths, not duplicate functional code. No duplicate code migration is required.
- PR #19 remains OPEN/MERGEABLE. No merge was performed.

## Root cause

- No consolidation defect requiring code change was found in WP-01. The only working-tree changes are the two intentional subprocess `PYTHONPATH` test fixes carried forward for WP-02/WP-03.
- Duplicate report basenames are documentation-history artifacts; they do not change runtime behavior.

## Modified files

- No WP-01 source file was modified.
- Preserved uncommitted changes: `tests/test_control_plane_attestation_binding.py`, `tests/test_runtime_attestation.py`.
- New report/evidence files: `reports/engineering-closure/RELEASE_CONSOLIDATION_REPORT.md`, `reports/engineering-closure/evidence/WP-01/*`, `reports/engineering-closure/evidence/run.sh`.

## Remaining blocker

- Merge approval for PR #19 and eventual PR from this engineering branch are external approvals; no merge performed.
- Windows compatibility, IndoBERT, RAG, Docker fullstack, knowledge E2E and performance remain for later work packages.

## Rollback procedure

- Engineering branch rollback reference: `f4f8b7f5b99f6fbd034d21149675fb625881a788`.
- Previous integration reference: `545137e8cfbec737488246492d59837df303cc4d`.
- Restore by creating a new worktree from either SHA; do not reset or force-push the current branch.
- Local test-harness patch is preserved at `/data/tmp/opencode/pending-engineering-tests.patch` and in `evidence/WP-01/pending_patch.out`.
