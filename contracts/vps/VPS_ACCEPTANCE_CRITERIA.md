# VPS Acceptance Criteria

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Date: `2026-11-24`
- Rule: evidence, not intent. Missing evidence means `PARTIAL` or `BLOCKED`.

## Gate Criteria

| Gate | Criterion | Evidence required | Current status |
|---|---|---|---|
| A | Official branch identified | Reconciliation report citing PR history and commits | PASS |
| B | No work lost | Read-only baseline plus worktree inventory | PASS |
| C | Controlled sync available | Sync policy, scripts, 8 Linux scenarios | PASS |
| C2 | Windows sync verified | `pwsh` execution on PC | NOT RUN |
| D | Linux portability | 39 targeted backend tests, frontend build, compose config, health | PASS |
| E | Regression no-new-ID | Closure report with `new_ids=0` | PASS |
| E2 | Full suite green | Full regression on exact release commit | BLOCKED |
| F | Docker runtime | Isolated container health/readyz with recorded build ID | PARTIAL — smoke PASS, image provenance stale |
| G | CI gate | Workflow files plus local validation | LOCAL PASS / GITHUB NOT RUN |
| G2 | CI frontend green | `npm test` green on GitHub | BLOCKED — 3 fixture failures |
| H | Staging controlled | Manual workflow with SHA and rollback record | PASS at design level |
| I | Knowledge boundary | Handoff report and no operator actions | PARTIAL / HANDOFF_REQUIRED |
| J | Security | Secret scan PASS, no data/credential in commit | PARTIAL — production ingress blockers remain |
| K | Reports complete | All Phase 0–6 files present under `reports/vps/` | PASS |
| L | Human approval | Owner approval for push/merge/deploy as applicable | PARTIAL — push authorized for this engineering branch only |
| M | Production release | All blockers closed and owner GO | NO-GO |

## Mandatory Reports

| File | Status |
|---|---|
| `reports/vps/VPS_RECONCILIATION_REPORT.md` | Present |
| `reports/vps/VPS_ENGINEERING_STATUS.md` | Present |
| `reports/vps/SYNC_VERIFICATION_REPORT.md` | Present |
| `reports/vps/PORTABILITY_TEST_REPORT.md` | Present |
| `reports/vps/DOCKER_RUNTIME_REPORT.md` | Present |
| `reports/vps/REGRESSION_TEST_REPORT.md` | Present |
| `reports/vps/CI_CD_TEST_REPORT.md` | Present |
| `reports/vps/KNOWLEDGE_FIXTURE_HANDOFF.md` | Present |
| `reports/vps/VPS_SECURITY_REPORT.md` | Present |
| `reports/vps/VPS_FINAL_READINESS_REPORT.md` | Present |

## Blocking Conditions

Production release remains `NO-GO` while any of these is true:

1. Real SOP PIAK-03 E2E is `BLOCKED`.
2. IndoBERT/Docling worker and approved model artifacts are absent.
3. Operator credential is absent.
4. Full regression has not been rerun on the exact release commit.
5. 37 Windows-native IPC cases remain unexecuted.
6. Three frontend evidence-fixture cases remain failing.
7. No TLS/auth ingress exists for production.
8. PR #19, #20, and #21 remain unmerged without owner decision.
9. Runtime provenance is split across multiple commits and worktrees.

## Final Verdict Rule

- `ENGINEERING COMPLETE`: all phases produced tracked evidence and the branch commit/push completed.
- `RELEASE NO-GO`: any blocking condition above remains open.
- `PRODUCTION READY`: forbidden unless every blocker is closed and an explicit owner GO is recorded.
