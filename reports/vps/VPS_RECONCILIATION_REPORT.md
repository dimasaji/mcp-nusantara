# VPS Reconciliation Report

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Execution Phase: `Phase 0 — Existing Contract Reconciliation`
- Date: `2026-11-24`
- Repository: `https://github.com/dimasaji/mcp-nusantara`
- Worktree: `/data/workspace/nus-v1-vps-master-20261124/worktrees/engineering`
- Branch: `codex/vps-master-engineering-20261124`
- Base: `origin/codex/restructure-20261123` @ `545137e8cfbec737488246492d59837df303cc4d`
- Method: read-only Git/GitHub inspection plus reuse of existing reports; no merge, push, deploy, service restart, or destructive Git command was executed.

## 1. Official integration branch

Decision: **`codex/restructure-20261123`** is the official Nusantara V1 integration branch.

Evidence:

- PR #16 (`MERGED`) and PR #17 (`MERGED`) both target `codex/restructure-20261123`; merge commits `ec76a9ed` and `b77c9c6e` are in its ancestry.
- PR #19 and PR #21 are still `OPEN` and both target `codex/restructure-20261123`.
- PR #21 body explicitly reconciles PC `ee22732d` with VPS integration history at `545137e8`.
- GitHub default branch `codex/fullroot-control-20261007` @ `8b7f9b78` is a stale legacy line and is **not** the active V1 integration line.
- No `main`/`master` branch exists locally or remotely.

## 2. Repository synchronization baseline

| Location | Branch / HEAD | Upstream | Delta | Working tree |
|---|---|---|---|---|
| `/data/home/mcp-nusantara` | `codex/final-consolidation-20261123` @ `e218bd61` | own origin | 0/0 | clean |
| `/data/home/mcp-nusantara` | `codex/restructure-20261123` @ `545137e8` | own origin | 0/0 | clean |
| `/data/home/mcp-nusantara` | `codex/restructure-20261124` @ `ee22732d` | own origin | 32 behind (`f1586983`) | clean |
| `/data/home/mcp-nusantara-integration` | `codex/integration-v1-20261123` @ `b268da1e` | misconfigured to `origin/codex/restructure-20261123` | 30 behind | dirty, 7 staged files |
| closure worktree | `codex/engineering-closure-20261124` @ `3f517294` | own origin | 0/0 | clean |
| postmerge worktree | `codex/vps-eng-completion-20261123` @ `b77c9c6e` | own origin | 1 ahead (`3e3eedcf`) | clean |
| release RC worktree | `codex/release-integration-rc-20261123` @ `b5214ce2` | own origin | 0/0 | dirty, 2 unstaged files |
| staging worktrees | detached `dfa1c8f0`, `db32ee40`, `6f037ab4` | none | n/a | clean |

Conclusion: the primary checkout is clean and synced **to its own branch**, but the VPS is not uniformly synced to the official integration tip. PR #21 head `f1586983` is fetched but not merged or pulled into a local branch. The active runtime processes also run from `/data/workspace/nus-v1-postmerge-ec76a9ed/repo` @ `b77c9c6e`, not from the primary checkout HEAD `e218bd61`.

## 3. Target deliverable inventory

| Target | Current equivalent | Status |
|---|---|---|
| `contracts/vps/VPS_MASTER_CONTRACT.md` | none; `docs/contracts/NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md` is ACTIVE but narrower | ABSENT |
| `contracts/vps/VPS_SYNC_POLICY.md` | `reports/final-consolidation/V1_PC_SYNC_HANDOFF.md` | ABSENT |
| `contracts/vps/VPS_ENGINEERING_RUNBOOK.md` | `reports/release-integration-rc/RELEASE_AND_ROLLBACK_CHECKLIST.md` | ABSENT |
| `contracts/vps/VPS_ACCEPTANCE_CRITERIA.md` | `reports/vps-final-stabilization/V1_VPS_FINAL_ACCEPTANCE_REPORT.md` | ABSENT |
| `scripts/sync/sync-vps.sh` | none | ABSENT |
| `scripts/sync/sync-local.ps1` | none | ABSENT |
| `.github/workflows/ci.yml` | none; no `.github/` directory exists | ABSENT |
| `.github/workflows/staging.yml` | none | ABSENT |
| `reports/vps/VPS_ENGINEERING_STATUS.md` | `reports/engineering-closure/V1_ENGINEERING_CLOSURE_REPORT.md` | ABSENT |
| `reports/vps/VPS_RECONCILIATION_REPORT.md` | `reports/vps-final-stabilization/GIT_RELEASE_RECONCILIATION_REPORT.md` | ABSENT |
| `reports/vps/SYNC_VERIFICATION_REPORT.md` | `reports/stabilization/GITHUB_SYNC_REPORT.md` | ABSENT |
| `reports/vps/PORTABILITY_TEST_REPORT.md` | `reports/engineering-closure/CROSS_PLATFORM_ACCEPTANCE_REPORT.md` | ABSENT |
| `reports/vps/REGRESSION_TEST_REPORT.md` | `reports/engineering-closure/FULL_REGRESSION_CLOSURE_REPORT.md` | ABSENT |
| `reports/vps/DOCKER_RUNTIME_REPORT.md` | `reports/vps-docker-readiness/VPS_DOCKER_READINESS_FINAL_REPORT.md` | ABSENT |
| `reports/vps/CI_CD_TEST_REPORT.md` | `reports/final-consolidation/VERIFICATION_SUMMARY.md` | ABSENT |
| `reports/vps/VPS_SECURITY_REPORT.md` | `reports/vps-recovery/VPS_SECURITY_REPORT.md` | ABSENT |
| `reports/vps/VPS_FINAL_READINESS_REPORT.md` | `reports/final-consolidation/RELEASE_GO_NO_GO.md` | ABSENT |

Existing equivalents are referenced rather than overwritten. New `reports/vps/` files will summarize and point to the canonical evidence.

## 4. Prior PASS work — do not repeat

- Release consolidation: `reports/engineering-closure/RELEASE_CONSOLIDATION_REPORT.md` — PASS, no conflicts or dependency drift.
- Git/PR reconciliation: `reports/vps-final-stabilization/GIT_RELEASE_RECONCILIATION.md` — PASS, canonical SHA `d2cfc60a`.
- Linux portability subset: `reports/engineering-closure/CROSS_PLATFORM_ACCEPTANCE_REPORT.md` — Linux PASS; 37 Windows-native IPC cases skipped.
- Regression ID closure: `reports/engineering-closure/FULL_REGRESSION_CLOSURE_REPORT.md` — `new_ids=0`, `fixed_ids=59`.
- Targeted regression: `reports/final-consolidation/V1_VPS_REGRESSION_DELTA.md` — `133 passed`.
- Ollama runtime/chat: `docs/reports/ollama-runtime-v1/NUSANTARA_V1_OLLAMA_FINAL_REPORT.md` — real inference, provider, backend chat, frontend chat all PASS.
- Linux staging at RC: `reports/final-consolidation/STAGING_ACCEPTANCE_REPORT.md` — Gate B PASS, build ID `sha256:e3900af2…`, production ports untouched.
- Docker readiness at RC: `reports/vps-docker-readiness/VPS_DOCKER_READINESS_FINAL_REPORT.md` — build/compose/health PASS, production deploy BLOCKED.
- Security/data integrity at RC: `reports/vps-final-stabilization/VPS_SECURITY_AND_DATA_INTEGRITY_REPORT.md` — Gate E PASS, DB hash/mtime unchanged.

## 5. Open blockers carried forward

1. **Production NO-GO**: `reports/final-consolidation/RELEASE_GO_NO_GO.md` and `reports/engineering-closure/V1_ENGINEERING_CLOSURE_REPORT.md`.
2. **Real SOP E2E BLOCKED**: no official PIAK-03 PDF, manifest, Docling env, IndoBERT model/worker, or operator credential.
3. **Three residual regression IDs**: 1 collection error (operator credential) and 2 retrieval failures (missing worker), all external.
4. **Docker evidence stale for WP-03 tree**: no fresh build after final regression work; Ollama topology unresolved (`host.docker.internal` vs loopback).
5. **Windows/PC evidence gaps**: 37 skipped native IPC cases, R2 owner hash mismatch, R3 Windows path absent.
6. **No CI gate**: PR #16 had `statusCheckRollup: []`; no GitHub Actions workflow exists on any inspected V1 branch.
7. **Runtime provenance split**: live processes run from `b77c9c6e`, primary checkout is `e218bd61`, official integration tip is `545137e8`, PR #21 head is `f1586983`.
8. **Disk pressure**: root filesystem 82% used, 2.7 GB free; two 2.22 GB Docker images cached.

## 6. Definition of Done — initial assessment

| Criterion | Initial status |
|---|---|
| VPS repository synced with official commit | PARTIAL — clean locally, but not at official tip; PR #21 not integrated |
| Integration branch verified | PASS — `codex/restructure-20261123` |
| Controlled synchronization available | BLOCKED — scripts absent |
| No loss of PC/VPS work | PASS so far — read-only phase preserved all trees |
| Linux portability verified | PARTIAL — Linux PASS, Windows pending |
| Backend startup / frontend build | PASS at RC evidence |
| Mandatory regression tests | PARTIAL — 59/62 IDs closed, 3 external blockers |
| Docker runtime verified | PARTIAL — RC PASS, final tree stale |
| CI pipeline | BLOCKED — no workflow exists |
| Staging deployment | PASS at RC, not repeatable via CI |
| Health check | PASS on current loopback services |
| Rollback verified | PASS historically, needs fresh drill before release |
| Critical security blocker | PARTIAL — no TLS/auth ingress, shared admin token |
| Knowledge fixture testing | PARTIAL — synthetic chat PASS, real SOP BLOCKED |
| Engineering reports | IN PROGRESS — this report created |
| Human approval for release | BLOCKED — not requested or granted |

## 7. Phase 0 verdict

`STATUS: COMPLETE`

No critical blocker prevents continuing to Phase 1. Next phase will implement and verify controlled synchronization scripts and a sync verification report on this feature branch. Merge of PR #19/#20/#21, any change to the official integration branch, and any production deployment remain behind human approval gates.
