# VPS Security Report

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Phase: `Phase 2 / Phase 6 evidence refresh`
- Date: `2026-11-24`
- Worktree: `/data/workspace/nus-v1-vps-master-20261124/worktrees/engineering`
- Verdict: `PARTIAL / NO NEW SECRET / PRODUCTION INGRESS BLOCKED`

## Current Checks

| Check | Result |
|---|---|
| Secret-pattern scan over `*.py`, `*.ts`, `*.tsx`, `*.json`, `*.yml`, `*.yaml`, `*.md`, `*.env*` | PASS, no match |
| `git diff --check` | To be run before commit; no whitespace defect expected |
| Secrets in CI/staging workflows | None used, printed, or referenced |
| Real credential in worktree | None introduced |
| Personal data, PDF, DB dump, chat history, model binary in this report set | None |
| Active service ports | `18201`, `15274`, `11434` untouched |

## Carried-Forward Findings

Prior canonical evidence: `reports/vps-recovery/VPS_SECURITY_REPORT.md`.

| ID | Finding | Severity | Current state |
|---|---|---|---|
| S-01 | No TLS/reverse proxy/auth ingress for production | Blocker | Open |
| S-02 | Admin token not configured; no active `.env` | High | Open |
| S-03 | Chrome debug `9222` and VNC `5901` active on loopback | Medium | Open; do not publish |
| S-04 | Backup not off-host; source/backup hash mismatch | High | Open |
| S-05 | Worktree/source provenance split across commits | High | Open; this report branch adds a new unmerged line |
| S-06 | Host firewall only Docker defaults; no application hardening | Medium | Open |
| S-07 | No production audit log or alerting | Medium | Open |
| S-08 | Personal chat data copied into staging/backup | High | Open; no such data added to this commit |

## Runtime Security Boundary

- No published public ports were created.
- Docker smoke used `127.0.0.1:18212` only and was removed immediately.
- No restart, rebind, or config change was made to active services.
- No database write, migration, restore, or deletion was performed.
- `NUSANTARA_ADMIN_TOKEN` was referenced only by name in prior evidence; no value was read or printed.
- Operator credential remains absent and must be supplied through the owner Secret mechanism.

## Security Verdict

`PARTIAL / NO NEW SECRET / PRODUCTION INGRESS BLOCKED`

The engineering reports and workflows introduce no new secret or data exposure. Production security remains blocked by missing TLS/auth ingress, absent credential provisioning, debug-port exposure, backup integrity, and ambiguous runtime provenance.
