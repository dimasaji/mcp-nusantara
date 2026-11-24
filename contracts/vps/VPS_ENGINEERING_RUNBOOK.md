# VPS Engineering Runbook

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Branch: `codex/vps-master-engineering-20261124`
- Base: `codex/restructure-20261123`
- Rule: stop before any push, merge, deploy, restart, migration, or operator action unless approval is explicit.

## 1. Preflight

```bash
git status --short
git branch --show-current
git remote -v
git rev-parse HEAD origin/codex/restructure-20261123
docker ps -a --format '{{.Names}} {{.Status}} {{.Ports}}'
```

Do not continue if a dirty tree is unexplained, the remote is not `dimasaji/mcp-nusantara`, or the official branch cannot be resolved.

## 2. Controlled Sync

```bash
bash scripts/sync/sync-vps.sh --dry-run
bash scripts/sync/sync-vps.sh --branch codex/restructure-20261123
```

Exit codes:

| Code | Meaning | Action |
|---|---|---|
| `0` | `SYNCED` or `FAST-FORWARD` | Continue |
| `2` | dirty tree, wrong remote, detached HEAD, missing branch | Stop and reconcile |
| `3` | `LOCAL_AHEAD` | Request push approval |
| `4` | `DIVERGED` | Manual reconciliation only |
| `5` | fetch failed | Stop |
| `6` | fast-forward failed | Stop |

On PC/Windows, use `./scripts/sync/sync-local.ps1 -DryRun` first. It was not executed on this Linux VPS because `pwsh` is unavailable.

## 3. Backend Verification

```bash
PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m pytest -q \
  tests/test_runtime_portability.py \
  tests/test_backend_runtime_fixture.py \
  tests/test_runtime_readiness.py \
  tests/test_runtime_build_provenance.py

/data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m compileall -q backend tests
```

Do not disable, skip, or weaken tests to obtain green results.

## 4. Frontend Verification

Frontend dependencies are not committed. In this sandbox they were temporarily symlinked from the postmerge worktree, then removed.

```bash
npm ci --no-audit --no-fund
npm test
npm run build
```

`npm run build` includes `tsc --noEmit`. Record failed cases as failures; do not edit assertions without owner approval.

## 5. Compose and Docker Smoke

```bash
docker compose -f deploy/docker/docker-compose.yml config --quiet
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'
```

For an isolated smoke test, map a fresh loopback port to the container's actual internal port, use a temporary data directory writable by uid `10001`, and remove the container afterwards. Do not touch active ports `18201`, `15274`, or `11434`.

## 6. Health Checks

```bash
curl -fsS http://127.0.0.1:18201/health
curl -fsS http://127.0.0.1:15274/health
```

`/readyz = degraded` with `documents=0` is expected for the empty fixture and is not a knowledge readiness PASS.

## 7. CI and Staging

- CI is defined in `.github/workflows/ci.yml`.
- Staging is manual only via `.github/workflows/staging.yml` with an approved `commit_sha`.
- Never add a production deploy step without explicit authorization.
- Never place secrets in workflow files or reports.

## 8. Knowledge Boundary

- Do not ingest official PDFs.
- Do not write metadata, change the index, or decide on operator actions.
- Keep `reports/vps/KNOWLEDGE_FIXTURE_HANDOFF.md` as the owner handoff.
- Real PIAK-03 acceptance belongs to the PC.

## 9. Reporting

Update, in order:

1. `reports/vps/VPS_ENGINEERING_STATUS.md`
2. Phase-specific report under `reports/vps/`
3. `reports/vps/VPS_FINAL_READINESS_REPORT.md`

Before commit: `git diff --check`, secret-pattern scan, and `git status --short`.

## 10. Commit and Push

Only after explicit approval:

```bash
git add <intended-files>
git diff --cached --check
git commit -m "<conventional-message>"
git push -u origin codex/vps-master-engineering-20261124
```

No force push. No merge. No rebase of shared history.
