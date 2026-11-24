# Performance and Reliability Report

- Status: **PARTIAL**
- Scope: stability, restart persistence, controlled failure behavior, and runtime non-interference.
- Evidence: `reports/release-integration-rc/STAGING_ACCEPTANCE_REPORT.md`, `reports/engineering-closure/evidence/WP-03/regression_final.out`, `evidence/WP-03/commands.tsv`.

## Proven at RC staging (`f4f8b7f5`)

| Reliability check | Status | Evidence |
|---|---|---|
| Container health and healthy wait | PASS | `staging_healthcheck.out`, `staging_healthy_wait.out` |
| Provider failure produces controlled HTTP 503 `PROVIDER_UNAVAILABLE` | PASS | `provider_failure_*` |
| Restart preserves one chat turn with identical question/response | PASS | `persistence_compare.out`, `staging_restart.out` |
| Rollback image with same volumes preserves history and health | PASS | `rollback_*.out` |
| Staging cleanup leaves active ports unchanged | PASS | `active_ports_after.out`, `staging_ports_absent.out` |

## WP-03 verification

- Full suite: `2 failed, 1605 passed, 82 skipped, 1086 warnings, 1 error`; `new_ids=0`, `fixed_ids=59`.
- `git diff --check` and compileall passed.
- Ruff and mypy report pre-existing findings on changed files; no semantic rewrite was performed.
- Active runtime was not touched: backend PID `19130` on `18201`, frontend PID `7740` on `15274`, Ollama `127.0.0.1:11434`, active DB unchanged.

## Not verified

- No fresh load test, latency benchmark or soak test was run against the final WP-03 tree.
- No fresh Docker staging cycle was run after WP-03 source/test changes.
- Real grounded retrieval performance remains blocked by missing IndoBERT worker.

Final status: **PARTIAL** — reliability evidence is inherited from RC staging and final-tree regression has no new IDs; performance acceptance remains **NOT_VERIFIED**.
