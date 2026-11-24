# Docker Runtime Report

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Phase: `Phase 2 / Phase 6 evidence refresh`
- Date: `2026-11-24`
- Worktree: `/data/workspace/nus-v1-vps-master-20261124/worktrees/engineering`
- Branch: `codex/vps-master-engineering-20261124`
- Base: `origin/codex/restructure-20261123` @ `545137e8cfbec737488246492d59837df303cc4d`
- Verdict: `PARTIAL / ISOLATED SMOKE PASS / PRODUCTION DEPLOY BLOCKED`

## Images And Containers

| Item | Result |
|---|---|
| `docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'` | `nusantara-v1:rc-f4f8b7f5 289037093661 2.22GB`; `nusantara-v1:docker-readiness-545137e8 44411d0acfd4 2.22GB` |
| Containers before test | None |
| Containers after test | None; smoke container removed |
| `docker compose -f deploy/docker/docker-compose.yml config --quiet` | PASS |

## Isolated Smoke Test

| Field | Value |
|---|---|
| Image | `nusantara-v1:docker-readiness-545137e8` |
| Host port | `127.0.0.1:18212` |
| Container port | `18201` |
| Data mount | `/data/tmp/opencode/vps_phase6_docker_data` mapped to `/app/data` |
| Env | `NUSANTARA_DATA_DIR=/app/data`, `NUSANTARA_KNOWLEDGE_DB=/app/data/knowledge/nusantara_knowledge.db` |
| Cleanup | `docker stop` then `docker rm -f`; active ports `18201`/`15274`/`11434` untouched |

Responses:

```json
{"status":"ok","version":"0.1.0","build_id":"sha256:a0753f141aa1eb8a19f98265f80d59a0b96b0cb5df0d8b2dbdef85767416858d"}
```

`/readyz` returned HTTP 200:

```json
{"status":"degraded","components":{"knowledge_database":{"status":"empty","documents":0},"provider":{"status":"unavailable","error":"URLError"}}}
```

The provider is unavailable inside the container because Ollama is not reachable from the isolated container network. This is expected for the smoke setup and is not a chat PASS.

## Findings

| ID | Finding | Impact |
|---|---|---|
| D-01 | Image listens on internal port `18201`, while current `deploy/docker/Dockerfile` declares `EXPOSE 8000` and `CMD ... --port 8000` | Image provenance is stale relative to this tree; compose port mapping needs correction or a fresh build |
| D-02 | `scripts/healthcheck.py` is empty in the current tree | Docker `HEALTHCHECK` is nonfunctional until repaired |
| D-03 | Dockerfile sets `NUSANTARA_INDOBERT_WORKER=/opt/indobert-worker/indobert_worker.py` but does not copy that worker | Knowledge worker missing in image; retrieval cannot be production-validated |
| D-04 | Compose includes unused Postgres and Redis services | Extra attack surface and operational complexity |
| D-05 | `documents=0` and `/readyz=degraded` | No real knowledge index is proven |
| D-06 | No fresh image build was performed for the final report commit | Build evidence is at tag `docker-readiness-545137e8`, not the report commit |

## Prior Evidence Boundary

Earlier reports reference `reports/vps-docker-readiness/VPS_DOCKER_READINESS_FINAL_REPORT.md` for build/compose/health PASS at RC. That file is not present in this checkout, so it is not silently imported as fresh evidence. The isolated smoke above is the current Docker runtime evidence.

## Verdict

`PARTIAL / ISOLATED SMOKE PASS / PRODUCTION DEPLOY BLOCKED`

Container startup, `/health`, and `/readyz` were verified on a loopback-only smoke container. Docker readiness for production remains blocked by stale image provenance, empty healthcheck script, missing worker, empty knowledge DB, and unresolved Ollama topology.
