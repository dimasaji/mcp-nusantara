# Release and Rollback Checklist

- SHA: `f4f8b7f5b99f6fbd034d21149675fb625881a788`
- Branch: `codex/release-integration-rc-20261123`
- Decision: **CONDITIONAL** — review allowed, deploy **BLOCKED** without owner approval
- Evidence: `reports/release-integration-rc/evidence/commands.tsv`

## 1. Pre-release gates

| Gate | Status | Command / evidence | Exit |
|---|---|---|---:|
| Git fetch all refs | PASS | `git fetch --all --prune --tags` | 0 |
| PR #16–#18 merged, #19 open/mergeable | PASS | `gh pr view 16/17/18/19 ...` → `evidence/pr*.out` | 0 |
| RC ancestry complete | PASS | `git merge-base --is-ancestor ... HEAD` → `evidence/ancestors.out` | 0 |
| Backend wheel from RC | PASS | `python -m pip wheel . --no-deps -w .../build/backend` → `evidence/backend_build_root.out` | 0 |
| Frontend build from RC | PASS | `npm ci && npm run build` → `evidence/frontend_install.out`, `frontend_build.out` | 0 |
| Docker image from RC | PASS | `docker build ... -t nusantara-v1:rc-f4f8b7f5 .` → `evidence/docker_build.err` | 0 |
| Compose configs | PASS | `docker compose ... config --quiet` → `evidence/compose_*_config.err` | 0 |
| Secret scan | PASS | `secret_scan_final` → `evidence/secret_scan_final.out` | 0 |
| No new regression IDs | PASS | `pytest -q --tb=no --continue-on-collection-errors` → `evidence/regression_after_fix.out` | 1 (expected; failures are baseline) |
| Critical regression triage | BLOCKED | 2 open critical IDs → `CRITICAL_REGRESSION_TRIAGE.md` | n/a |
| PIAK-03 / approved knowledge artifacts | BLOCKED | owner PC/artifacts required | n/a |
| Production deploy authorization | BLOCKED | not granted in this task | n/a |

## 2. Release candidate identity

| Item | Value |
|---|---|
| RC commit | `f4f8b7f5b99f6fbd034d21149675fb625881a788` |
| Base integration HEAD | `545137e8cfbec737488246492d59837df303cc4d` |
| RC image | `sha256:289037093661de418e48da86e5626ed67df3d482950b820eb1ade16f1d76ecc7` |
| Backend wheel SHA | `5d0035f86e07201e8a7dbe04610ad7e0b2823a05a1754075c25661de5e510a53` |
| Rollback image | `sha256:44411d0acfd45c8094c57af0680175603f073ad19cb8494a07b38419e11f4856` |

## 3. Rollback path — tested in staging, PASS

Evidence: `evidence/rollback_image_check.out`, `rollback_start.out`, `rollback_wait.out`, `rollback_health.out`, `rollback_history.out`, `rollback_hc.out`.

1. Stop RC staging container only: `docker rm -f nusantara-rc-staging` — exit 0.
2. Start previous image with the **same** data/home volumes on a non-active port:
   `docker run -d --name nusantara-rc-rollback --network host --read-only --tmpfs /tmp -v nusantara-rc-data:/app/data -v nusantara-rc-home:/home/appuser ... nusantara-v1:docker-readiness-545137e8 uvicorn app.main:app --host 127.0.0.1 --port 18216`
3. Verify: `GET /health` → HTTP 200; `GET /v1/chat/history` → same session/turn; healthcheck → exit 0.
4. No active service or DB was touched.

## 4. Deployment steps — NOT EXECUTED

Explicitly not performed: merge PR #19, deploy to production, restart backend PID `19130`, restart frontend PID `7740`, change Ollama port `11434`, change active API port `18201`, modify active DB, use real secrets, or force push.

Required before execution:
- Owner approval for deploy and for PR #19 merge.
- Resolve or formally accept the 2 critical regression items: IndoBERT worker availability and RAG top_k semantics.
- Provide PIAK-03 / approved IndoBERT/Docling artifacts or accept as release-note limitation.
- Decide Ollama production topology (host network vs Ollama listening on a docker-reachable interface).
- Re-run `STAGING_ACCEPTANCE_REPORT.md` checks against the exact SHA selected for deploy.

## 5. Post-deploy verification checklist — template, NOT EXECUTED

| Check | Command | Expected |
|---|---|---|
| Health | `curl -fsS http://127.0.0.1:<port>/health` | HTTP 200, `status=ok` |
| Readiness | `curl -sS -w '\nHTTP %{http_code}\n' http://127.0.0.1:<port>/readyz` | HTTP 200, dependencies known |
| Chat | `curl -sS -X POST -H 'Content-Type: application/json' -H 'X-Admin-Token: <approved-token>' -d '{"session_id":"web-...","user_input":"PONG"}' http://127.0.0.1:<port>/v1/chat` | HTTP 200, provider `ollama`, model `llama3.2:1b` |
| Model identity | `curl -sS -H 'X-Admin-Token: <approved-token>' http://127.0.0.1:<port>/v1/control-plane/model-status` | `INFERENCE_VERIFIED` after a real request |
| Rollback | repeat section 3 with the exact rollback image | health + history PASS |

Final status: **CONDITIONAL** for review; production readiness remains **BLOCKED** until owner approval and critical/artifact items are resolved.
