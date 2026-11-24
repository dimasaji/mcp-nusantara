# VPS Engineering Status

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Execution Phase: `Phase 6 — Final Engineering Acceptance` (all phases complete locally)
- Repository: `https://github.com/dimasaji/mcp-nusantara`
- Branch: `codex/vps-master-engineering-20261124`
- Local Commit Before Delivery: `cfd46391` (`docs(vps): add engineering reconciliation and sync controls`)
- Delivery State: Phase 2–6 files are uncommitted until the authorized delivery commit is created
- Remote Commit: `origin/codex/restructure-20261123` = `545137e8`; GitHub default `codex/fullroot-control-20261007` = `8b7f9b78`; PR #21 head = `f1586983`

## Completed

- Phase 0 read-only reconciliation; no commit was lost and no working tree was altered.
- Official integration branch identified from PR #16/#17/#19/#21 evidence: `codex/restructure-20261123`.
- Existing contracts/reports inventoried; equivalent evidence reused instead of duplicated.
- Prior PASS work catalogued in `reports/vps/VPS_RECONCILIATION_REPORT.md`.
- Feature worktree created from official integration tip without touching primary checkout.
- Phase 1 sync policy and Linux/Windows sync scripts implemented and committed at `cfd46391`.
- Linux sync script verified on disposable clones for dry-run, synced, dirty tree, wrong remote, fast-forward, local-ahead, and diverged cases.
- Phase 2 Linux portability/runtime evidence refreshed: `39 passed`, frontend build PASS, compose config PASS, health endpoints HTTP 200.
- Phase 2 Docker isolated smoke PASS: `/health` 200 with build ID `sha256:a0753f141aa1eb8a19f98265f80d59a0b96b0cb5df0d8b2dbdef85767416858d`; `/readyz` 200 degraded.
- Phase 3 regression classification refreshed: 0 new regressions; 3 external blockers and 3 frontend evidence-fixture failures documented.
- Phase 4 CI/staging workflows created and locally validated; no GitHub run, merge, or deploy performed.
- Phase 5 knowledge fixture boundary verified and owner handoff written; no ingestion or operator action performed.
- Phase 6 final readiness report written with verdict `ENGINEERING COMPLETE / RELEASE NO-GO`.

## In Progress

- Authorized delivery commit and push of this report set to `codex/vps-master-engineering-20261124`.

## Pending

- Real GitHub Actions execution after push.
- Owner decision on the 3 frontend engineering-console fixture cases.
- Owner-supplied PIAK-03 artifacts, IndoBERT/Docling worker, and operator credential.
- Windows `sync-local.ps1` execution and 37 native IPC cases.
- PR #19/#20/#21 merge decision.

## Blocked

- Real SOP E2E: no official PIAK-03 PDF, manifest, Docling env, IndoBERT model/worker, or operator credential.
- Production release: owner approval not granted; verdict remains NO-GO.
- Merge of PR #19, #20, and #21: requires owner approval.
- Windows-native validation: 37 IPC cases skipped on Linux; PC/CI evidence required.
- Runtime provenance: live services run from `b77c9c6e`, not the primary checkout or official tip.
- CI green gate: `npm test` has 3 pre-existing fixture failures until fixtures are restored or tests are approved for update.
- Docker production readiness: stale image provenance, empty healthcheck script, and missing worker copy.

## Files Changed

- `reports/vps/VPS_RECONCILIATION_REPORT.md` (new, committed at `cfd46391`)
- `reports/vps/VPS_ENGINEERING_STATUS.md` (new at `cfd46391`, updated in Phase 6)
- `contracts/vps/VPS_SYNC_POLICY.md` (new, committed at `cfd46391`)
- `scripts/sync/sync-vps.sh` (new, committed at `cfd46391`)
- `scripts/sync/sync-local.ps1` (new, committed at `cfd46391`)
- `reports/vps/SYNC_VERIFICATION_REPORT.md` (new, committed at `cfd46391`)
- `.gitignore` (unignored `reports/vps/`, committed at `cfd46391`)
- `contracts/vps/VPS_MASTER_CONTRACT.md` (new, uncommitted)
- `contracts/vps/VPS_ENGINEERING_RUNBOOK.md` (new, uncommitted)
- `contracts/vps/VPS_ACCEPTANCE_CRITERIA.md` (new, uncommitted)
- `reports/vps/PORTABILITY_TEST_REPORT.md` (new, uncommitted)
- `reports/vps/DOCKER_RUNTIME_REPORT.md` (new, uncommitted)
- `reports/vps/REGRESSION_TEST_REPORT.md` (new, uncommitted)
- `.github/workflows/ci.yml` (new, uncommitted)
- `.github/workflows/staging.yml` (new, uncommitted)
- `reports/vps/CI_CD_TEST_REPORT.md` (new, uncommitted)
- `reports/vps/KNOWLEDGE_FIXTURE_HANDOFF.md` (new, uncommitted)
- `reports/vps/VPS_SECURITY_REPORT.md` (new, uncommitted)
- `reports/vps/VPS_FINAL_READINESS_REPORT.md` (new, uncommitted)

## Tests Executed

- `bash -n scripts/sync/sync-vps.sh`.
- 8 Linux sync-script scenarios on disposable clones; details in `reports/vps/SYNC_VERIFICATION_REPORT.md`.
- `PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m pytest -q tests/test_runtime_portability.py tests/test_backend_runtime_fixture.py tests/test_runtime_readiness.py tests/test_runtime_build_provenance.py`.
- `npm test` in `frontend/` via temporary `node_modules` symlink.
- `npm run build` in `frontend/`.
- `/data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m compileall -q backend tests`.
- `docker compose -f deploy/docker/docker-compose.yml config --quiet`.
- Isolated Docker smoke on `nusantara-v1:docker-readiness-545137e8` with `/health` and `/readyz`.
- PyYAML parse of `.github/workflows/ci.yml` and `.github/workflows/staging.yml`.
- Local secret-pattern scan equivalent to the CI `git grep` step.
- HTTP GET `http://127.0.0.1:18201/health` and `http://127.0.0.1:15274/health`.

## Tests Passed

- 271 named cases: 8 sync scenarios + 39 backend pytest cases + 218 frontend cases.
- Command checks PASS: `bash -n`, frontend build/typecheck, `compileall`, compose config, Docker `/health`, Docker `/readyz`, YAML parse, secret-pattern scan, both active health endpoints.

## Tests Failed

- 3 frontend cases in `src/__tests__/engineering-console.test.tsx`, all caused by missing historical evidence fixtures removed by commit `0b48db2a`.

## Tests Skipped

- 1 (`sync-local.ps1` execution; `pwsh` unavailable in this Linux sandbox).
- 37 Windows-native IPC cases inherited as skipped from `reports/engineering-closure/CROSS_PLATFORM_ACCEPTANCE_REPORT.md`; not executed on this VPS.

## Known Issues

- Official integration branch is 30+ commits ahead of several local work branches.
- No `.github/workflows` exists on any inspected V1 remote branch; Phase 4 workflows exist only on this unmerged feature branch.
- First real GitHub CI run on this branch is expected to fail at the `frontend` job until the fixture decision is made.
- Root filesystem at 82% use with 2.7 GB free.
- Current service ports `18201`/`15274` differ from configured `8000`/`5180`.
- Hardcoded Windows paths remain in `backend/app/knowledge/docling_config.py`, `backend/app/skills/sop_semantic/engine.py`, and developer-core docstrings.
- Docker image internal port `18201` differs from current Dockerfile `8000`; `scripts/healthcheck.py` is empty and the IndoBERT worker is not copied.

## Security Findings

- Secret-pattern scan passed locally; no secrets were introduced or printed.
- CI and staging workflows use no secrets and never log credentials.
- Docker smoke used loopback-only `127.0.0.1:18212` and was removed immediately.
- Prior findings carried forward: shared admin token, no TLS/auth ingress, historical npm advisories, blocked real-SOP knowledge artifacts, and personal data in legacy backups.

## Approval Required

- Push of this feature branch: authorized by owner in this session.
- Merge or rebase of official integration branch.
- Merge of PR #19, #20, or #21.
- Any production deployment or service restart.
- Any database schema/data migration.
- Download/install of large model artifacts or paid services.
- Decision on the 3 engineering-console fixture cases.

## Next Action

Create the authorized delivery commit for Phase 2–6 files, push only `codex/vps-master-engineering-20261124` to GitHub, then record the resulting SHA and push result. Do not merge, deploy, restart services, or perform operator actions without separate owner approval.
