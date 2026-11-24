# Sync Verification Report

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Execution Phase: `Phase 1 — Controlled Synchronization`
- Date: `2026-11-24`
- Worktree: `/data/workspace/nus-v1-vps-master-20261124/worktrees/engineering`
- Branch: `codex/vps-master-engineering-20261124`
- Official integration branch: `codex/restructure-20261123`
- Scripts: `scripts/sync/sync-vps.sh`, `scripts/sync/sync-local.ps1`
- Policy: `contracts/vps/VPS_SYNC_POLICY.md`

## Method

A disposable bare repository was created at `/data/tmp/opencode/nus-v1-sync-test/dimasaji/mcp-nusantara.git` from `/data/home/mcp-nusantara`. Four disposable work clones were used so no real repository, working tree, or remote branch was modified. The Linux script was executed against those clones only. `bash -n` was used for syntax validation. PowerShell was not available in this sandbox, so `sync-local.ps1` could not be executed here.

## Test matrix

| # | Case | Expected | Actual | Exit | Status |
|---:|---|---|---|---:|---|
| 1 | `bash -n sync-vps.sh` | syntax OK | `SYNTAX_OK` | 0 | PASS |
| 2 | `--dry-run` on clean clone | report before commit, no mutation | `DRY-RUN ... before=545137e8...` | 0 | PASS |
| 3 | clean and equal clone | `SYNCED`, no mutation | `SYNCED ... commit=545137e8...` | 0 | PASS |
| 4 | dirty tracked file | detection before fetch, no mutation | `working tree is not clean` | 2 | PASS |
| 5 | wrong remote URL | detection before fetch, no mutation | `unexpected remote URL: https://example.invalid/not-nusantara.git` | 2 | PASS |
| 6 | local behind remote | fetch then ff-only | `FAST-FORWARD ... before=545137e8... after=99d94ea6...` | 0 | PASS |
| 7 | local ahead of remote | stop, no push | `LOCAL_AHEAD ... push requires approval` | 3 | PASS |
| 8 | diverged histories | stop, no merge, tree unchanged | `DIVERGED ... manual reconciliation required`; status `[ahead 1, behind 1]` | 4 | PASS |
| 9 | `sync-local.ps1` execution | equivalent Windows behavior | `pwsh` not installed | n/a | NOT RUN |

## Evidence details

- Dry-run: `DRY-RUN repo=/data/tmp/opencode/nus-v1-sync-test/work-clean remote=origin branch=codex/vps-master-engineering-20261124 before=545137e8cfbec737488246492d59837df303cc4d`.
- Synced: `SYNCED repo=/data/tmp/opencode/nus-v1-sync-test/work-clean branch=codex/vps-master-engineering-20261124 commit=545137e8cfbec737488246492d59837df303cc4d`.
- Dirty: `working tree is not clean`; exit `2`; no fetch attempted.
- Wrong remote: `unexpected remote URL: https://example.invalid/not-nusantara.git`; exit `2`; HEAD remained `545137e8`.
- Fast-forward: remote advanced `545137e8..99d94ea6`; script fast-forwarded to `99d94ea63fb09d63cfd855cdbda5565d548427a1`; exit `0`.
- Local ahead: local `1185b5e4baa1553bd52239c45710132c3213461f`, remote `99d94ea63fb09d63cfd855cdbda5565d548427a1`; exit `3`; nothing pushed.
- Diverged: local `1185b5e4...`, remote `44df652a3ddc2a37c9720d7afa2b6a1c3142b988`; exit `4`; worktree status remained `## codex/vps-master-engineering-20261124...origin/codex/vps-master-engineering-20261124 [ahead 1, behind 1]`.

## Real repository status after Phase 1

No real repository was synchronized by this script during verification. The baseline from `VPS_RECONCILIATION_REPORT.md` remains:

- primary checkout clean at `e218bd61` on its own branch;
- official integration tip `545137e8`;
- local `codex/restructure-20261124` behind GitHub `f1586983` by 32 commits;
- `/data/home/mcp-nusantara-integration` behind by 30 commits with 7 staged files;
- PR #19, #20, and #21 remain open and require owner approval before merge.

## Verdict

- Linux synchronization script: **PASS** for clean-tree detection, dry-run, synced state, fast-forward, local-ahead stop, divergence stop, and wrong-remote stop.
- Windows synchronization script: **NOT RUN** in this Linux sandbox; PC/CI validation is required.
- Domain 02 overall: **PARTIAL** — automation exists and is verified on Linux, but real-branch reconciliation and Windows execution remain approval/PC-gated.

## Next action

Commit this feature branch and run Phase 2/3 checks from the same approved base. Do not merge this work into `codex/restructure-20261123` without owner approval.
