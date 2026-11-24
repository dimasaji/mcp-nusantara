# Nusantara V1 CI/CD Test Report

## Identitas

| Field | Value |
|---|---|
| Report | `reports/vps/CI_CD_TEST_REPORT.md` |
| Date | 2026-11-24 |
| Worktree | `/data/workspace/nus-v1-vps-master-20261124/worktrees/engineering` |
| Branch | `codex/vps-master-engineering-20261124` |
| Base | `origin/codex/restructure-20261123` @ `545137e8cfbec737488246492d59837df303cc4d` |
| Contract | `NUS-V1-VPS-MASTER-001` |
| Overall | `LOCAL PASS / GITHUB EXECUTION NOT RUN` |

## Files Created

| File | Purpose |
|---|---|
| `.github/workflows/ci.yml` | Pull-request/push CI: backend checks, targeted regression, secret pattern scan, frontend test/build, compose validation. |
| `.github/workflows/staging.yml` | Manual, controlled staging record with approved SHA input, health check, rollback record, artifact upload. |
| `reports/vps/CI_CD_TEST_REPORT.md` | This report. |

## CI Design

| Job | Trigger | Commands | Gate |
|---|---|---|---|
| `backend` | PR and push to `codex/restructure-20261123`, push to `codex/vps-master-engineering-20261124`, `workflow_dispatch` | `pip install -r requirements-lock.txt`, `python -m compileall -q backend tests`, targeted pytest, secret pattern scan | Fail on any command failure or secret-like pattern |
| `frontend` | Same as `backend` | `npm ci --no-audit --no-fund`, `npm test`, `npm run build` | Fail on test or build failure |
| `compose` | Same as `backend` | `docker compose -f deploy/docker/docker-compose.yml config --quiet` | Fail on invalid compose config |

## Staging Design

| Item | Value |
|---|---|
| Trigger | `workflow_dispatch` only |
| Required input | `commit_sha` — approved commit SHA |
| Action input | `prepare`, `healthcheck`, `rollback-record` |
| Optional input | `staging_url`, `rollback_sha` |
| Checkout | `actions/checkout@v4` with `ref: ${{ inputs.commit_sha }}` |
| Verification | `git rev-parse HEAD` must equal approved `commit_sha` |
| Health check | `curl -fsS "${staging_url}/health"` and `/readyz` when action is `healthcheck` |
| Artifact | `staging-record-${action}` containing `staging-rollback.txt` and `frontend/dist` |
| Secrets | None used or printed by workflow |
| Production deploy | Not implemented; requires explicit human approval and separate authorization |

## Locally Mirrored Validation

| Command | Result |
|---|---|
| `/data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -c "import yaml; [yaml.safe_load(open(p)) for p in ('.github/workflows/ci.yml', '.github/workflows/staging.yml')]; print('YAML parse: PASS')"` | PASS |
| `/data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m compileall -q backend tests` | PASS |
| `PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m pytest -q tests/test_runtime_portability.py tests/test_backend_runtime_fixture.py tests/test_runtime_readiness.py tests/test_runtime_build_provenance.py` | `39 passed, 0 failed, 18 warnings in 3.12s` |
| `npm test` in `frontend/` via temporary `node_modules` symlink | `218 passed`, `3 failed`, `28 files passed`, `1 failed`, duration `7.83s` |
| `npm run build` in `frontend/` | PASS; `451 modules transformed`, chunk-size warning only |
| `docker compose -f deploy/docker/docker-compose.yml config --quiet` | PASS |
| `rg -n --glob '*.py' --glob '*.ts' --glob '*.tsx' --glob '*.json' --glob '*.yml' --glob '*.yaml' --glob '*.md' --glob '*.env*' '(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----)' .` | PASS, no match |
| GitHub Actions run on GitHub | NOT RUN — no push performed, workflow files not present on remote |

## Known CI Failure On Current Base

`npm test` has 3 pre-existing fixture failures in `src/__tests__/engineering-console.test.tsx`:

| Test | Missing path |
|---|---|
| `opens the evidence bundle for the new release gates` | `docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json` |
| `opens the full regression report from the evidence index` | `docs/reports/openrouter-workflow-20261009T184538/IMPLEMENTATION_REPORT.json` |
| `navigates using the human console recovery index` | `docs/reports/human-console-recovery-20261009T200537/README.md` |

Git history shows those generated report files were removed by `0b48db2a chore: clean up git tracking - remove generated reports, caches, temp, and backup files`. Classification: pre-existing test-fixture drift, not introduced by this task. Tests were not weakened, skipped, or edited. Owner decision is required: restore the fixtures or approve updating the tests to current evidence paths.

## Approval Gates

- No push performed.
- No merge performed.
- No GitHub Actions run triggered.
- No staging deploy performed.
- No production deploy performed.
- PR #19, #20, #21 remain open and require human approval.

## Final Verdict

`LOCAL PASS / GITHUB EXECUTION NOT RUN`

CI/CD files are syntactically valid and locally mirrored checks pass, except the documented pre-existing frontend fixture drift. The first real GitHub CI run on this branch is expected to fail at the `frontend` job until the fixture decision is made.
