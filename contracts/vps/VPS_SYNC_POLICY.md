# VPS Sync Policy — Nusantara V1

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Scope: controlled synchronization between PC lokal, GitHub, and VPS Instabox.
- Official integration branch: `codex/restructure-20261123`.
- GitHub repository: `https://github.com/dimasaji/mcp-nusantara`.

## Source of truth

GitHub `origin/codex/restructure-20261123` is the canonical integration line. Evidence: PR #16 and #17 were merged into it; PR #19 and #21 are open against it. The GitHub default branch `codex/fullroot-control-20261007` is legacy and is not the active V1 integration line.

## Branch policy

- OpenCode works on a feature or fix branch created from the official integration branch.
- Codex works on a coordinated PC branch.
- All integration into the official branch goes through a reviewed Pull Request.
- VPS staging uses an approved commit or release identifier only.
- No automatic production deployment is allowed.

## Preconditions

Both sync scripts stop before any mutation when:

- the path is not a Git work tree;
- the current revision is detached `HEAD`;
- the configured remote is missing or does not point to `dimasaji/mcp-nusantara`;
- the working tree has staged, unstaged, or untracked changes;
- the remote branch does not exist;
- `git fetch` fails.

## Allowed synchronization

When the local commit is an ancestor of the remote commit, the scripts perform `git merge --ff-only <remote_commit>`. Nothing is pushed, rebased, reset, or force-updated.

## Stop conditions

| Condition | Exit code | Meaning |
|---|---:|---|
| clean and equal | 0 | `SYNCED` |
| local is ancestor of remote | 0 | `FAST-FORWARD` completed |
| remote is ancestor of local | 3 | `LOCAL_AHEAD`; push requires owner approval |
| histories diverged | 4 | `DIVERGED`; manual reconciliation required |
| invalid repo, remote, branch, or dirty tree | 2 | precondition failed |
| fetch failure | 5 | network/remote failure |
| fast-forward failure | 6 | conflict or unexpected state |
| bad argument | 64 | usage error |

## Prohibited actions

- `git push --force` or any history rewrite.
- `git reset --hard`, `git clean -fd`, or overwriting local changes.
- Automatic merge on divergence.
- Silent push from the VPS.
- Pulling into a dirty worktree.
- Changing the official branch without a reviewed PR and approval.
- Copying secrets, operational databases, or resident data into GitHub.

## Usage

VPS / Linux:

```bash
scripts/sync/sync-vps.sh --repo /path/to/mcp-nusantara --branch codex/restructure-20261123 --dry-run
scripts/sync/sync-vps.sh --repo /path/to/mcp-nusantara --branch codex/restructure-20261123
```

PC / Windows:

```powershell
.\scripts\sync\sync-local.ps1 -Repo C:\Users\dmaza\mcp-starter -Branch codex/restructure-20261123 -DryRun
.\scripts\sync\sync-local.ps1 -Repo C:\Users\dmaza\mcp-starter -Branch codex/restructure-20261123
```

## Verification requirement

Every run must record repository path, remote URL, branch, before commit, after commit, exit code, and verdict in `reports/vps/SYNC_VERIFICATION_REPORT.md`. A `PASS` verdict requires a clean-tree dry run plus one successful fast-forward or synced run on a disposable clone. Dirty-tree, local-ahead, and diverged cases must be detected without mutation.
