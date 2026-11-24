# Nusantara V1 VPS Master Contract

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Version: `1.0`
- Date: `2026-11-24`
- Environment: `VPS Instabox — Linux`
- Executor: `OpenCode`
- Repository: `https://github.com/dimasaji/mcp-nusantara`
- Official integration branch: `codex/restructure-20261123`
- Engineering branch used for this execution: `codex/vps-master-engineering-20261124`

## 1. Objective

Make the VPS Instabox the Nusantara V1 engineering and staging authority while GitHub remains the Single Source of Truth and the PC remains the operational validation authority. Preserve all existing work, avoid rewrites, and produce evidence-based reports for every phase.

## 2. Authority Model

| System | Authority |
|---|---|
| GitHub | Source of truth for commits, branches, PRs, and review history |
| VPS Instabox | Engineering, staging, synchronization, and evidence generation |
| PC / Windows | Operational validation, official PIAK-03 acceptance, operator actions |

## 3. Non-Negotiable Rules

1. Nusantara V1 only; no V2, V3, or V4 work.
2. No full rewrite of existing code.
3. No force push, hard reset, destructive Git operation, or history rewrite without explicit approval.
4. No overwriting or deletion of legitimate Codex/PC work.
5. No secret, credential, token, personal data, SOP PDF, DB dump, chat history, model binary, or production data in reports or commits.
6. No production deployment, service restart, port rebind, database migration, or operator decision without explicit approval.
7. No PASS claim without reproducible evidence.
8. No test deletion, weakening, skip insertion, or threshold lowering to obtain PASS.
9. No auto-merge of PR #19, #20, or #21.
10. Staging must be isolated from active services and recorded.

## 4. Phase Map

| Phase | Name | Deliverable |
|---|---|---|
| 0 | Existing contract reconciliation | `reports/vps/VPS_RECONCILIATION_REPORT.md` |
| 1 | Controlled synchronization | `contracts/vps/VPS_SYNC_POLICY.md`, sync scripts, `reports/vps/SYNC_VERIFICATION_REPORT.md` |
| 2 | Linux portability/runtime evidence | `reports/vps/PORTABILITY_TEST_REPORT.md`, `reports/vps/DOCKER_RUNTIME_REPORT.md` |
| 3 | Regression classification | `reports/vps/REGRESSION_TEST_REPORT.md` |
| 4 | CI/CD and staging controls | `.github/workflows/ci.yml`, `.github/workflows/staging.yml`, `reports/vps/CI_CD_TEST_REPORT.md` |
| 5 | Knowledge fixture handoff | `reports/vps/KNOWLEDGE_FIXTURE_HANDOFF.md` |
| 6 | Final engineering acceptance | `reports/vps/VPS_FINAL_READINESS_REPORT.md`, `reports/vps/VPS_ENGINEERING_STATUS.md` |

## 5. Supporting Contracts

| File | Purpose |
|---|---|
| `contracts/vps/VPS_SYNC_POLICY.md` | Branch authority, fast-forward rules, exit codes, approval gates |
| `contracts/vps/VPS_ENGINEERING_RUNBOOK.md` | Safe execution order and command sequence |
| `contracts/vps/VPS_ACCEPTANCE_CRITERIA.md` | Evidence required for each gate and final verdict |

## 6. Evidence Standard

- Every verdict must cite a file, command output, commit, PR, or runtime response.
- Existing PASS evidence may be reused when equivalent and clearly attributed; it must not be duplicated as a new claim.
- Stale evidence must be labeled as stale and not silently promoted.
- Missing artifacts produce `BLOCKED` or `PARTIAL`, never `PASS`.
- External blockers must name the owner action needed to close them.
- Reports must be written to `reports/vps/` and tracked explicitly.

## 7. Approval Gates

- Push from the engineering branch.
- Merge, rebase, or change to `codex/restructure-20261123`.
- Merge of PR #19, #20, or #21.
- Production deployment, restart, or service rebind.
- Data migration, restore, overwrite, or deletion.
- Download/install of large model artifacts or paid services.
- Any operator action on behalf of a human.

## 8. Completion Rule

`CONTRACT EXECUTION COMPLETE` means all seven phases produced evidence, all changed files are committed on the engineering branch, and the final report records an honest release verdict. It does **not** mean production readiness. Production readiness remains `NO-GO` while any blocker from `reports/vps/VPS_ACCEPTANCE_CRITERIA.md` is open.
