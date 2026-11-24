# Git reconciliation — RC f4f8b7f5

## Commands

- `git fetch --all --prune --tags`
- `gh pr view <16|17|18|19> --repo dimasaji/mcp-nusantara --json ...`
- `git merge-base --is-ancestor <sha> HEAD` for `ec76a9ed`, `3e3eedcf`, `b77c9c6e`, `545137e8`
- `git diff --stat origin/codex/restructure-20261123..HEAD`
- `git branch -a --no-color`
- `git for-each-ref --format='%(refname:short)' refs/remotes/origin`
- `git show --stat --format='' <commit>` / `git diff-tree --no-commit-id --name-only -r <commit>`

## Results

| PR | State | Merge/base | Head |
|---|---|---|---|
| #16 | MERGED | merge `ec76a9ed01f160a28d1cbe34e263b3bbe9ccb075` into `codex/restructure-20261123` | `e7da7bcbe0cbf10cef71a53c298f8a0da21c8c71` |
| #17 | MERGED | merge `b77c9c6e3d547b1d5a34c633abd0fb01e5aef046` into `codex/restructure-20261123` | `3e3eedcf82f326bc609df25056c50536d487807f` |
| #18 | MERGED | merge `3e3eedcf82f326bc609df25056c50536d487807f` into `codex/vps-eng-completion-20261123` | `11f819c347d047ee3c45126f95a9d621f516acbe` |
| #19 | OPEN / MERGEABLE | base `codex/restructure-20261123` | `f4f8b7f5b99f6fbd034d21149675fb625881a788` |

Ancestry chain: `ec76a9ed` → `3e3eedcf` → `b77c9c6e` → `545137e8` → `f4f8b7f5`. All four key SHAs are ancestors of the RC.

RC vs integration branch: 30 files, 1446 insertions, 29 deletions; all are PR #19 Docker readiness code/tests/reports/evidence. No duplicated functional change: 40/87 older unique commits outside RC have identical patch IDs to commits already in RC; the only PR16–19 commit outside RC is `e218bd61`, a doc duplicate of `dfa1c8f0`.

Duplicate evidence paths found (informational only): `reports/final-consolidation/POST_MERGE_VERIFICATION.md`, `reports/vps-final-stabilization/TEST_RESULTS.json`, `reports/vps-final-stabilization/V1_VPS_FINAL_ACCEPTANCE_REPORT.md`, and repeated `commands.tsv` basenames under `reports/vps-final-stabilization/evidence/`, `reports/vps-final-stabilization/deployment-evidence/`, and `reports/vps-docker-readiness/evidence/`.

Decision: single RC SHA `f4f8b7f5b99f6fbd034d21149675fb625881a788`.
