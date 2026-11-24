# Staging Acceptance Report

- SHA: `f4f8b7f5b99f6fbd034d21149675fb625881a788`
- Image: `nusantara-v1:rc-f4f8b7f5` = `sha256:289037093661de418e48da86e5626ed67df3d482950b820eb1ade16f1d76ecc7`
- Rollback image: `nusantara-v1:docker-readiness-545137e8` = `sha256:44411d0acfd45c8094c57af0680175603f073ad19cb8494a07b38419e11f4856`
- Overall staging status: **PASS**
- Production deploy: **BLOCKED** (not authorized)

## Commands and exit codes

| Command | Exit | Status | Evidence |
|---|---:|---|---|
| `docker compose -f deploy/docker/docker-compose.yml config --quiet` | 0 | PASS | `evidence/compose_config.err` |
| `docker compose ... docker-compose.audit.yml config --quiet` | 0 | PASS | `evidence/compose_audit_config.err` |
| `NUSANTARA_INDOBERT_WORKER_DIR=... docker compose ... docker-compose.indobert.yml config --quiet` | 0 | PASS | `evidence/compose_indobert_config.err` |
| `DOCKER_BUILDKIT=1 docker build ... -t nusantara-v1:rc-f4f8b7f5 .` | 0 | PASS | `evidence/docker_build.err` |
| `docker image inspect nusantara-v1:rc-f4f8b7f5 --format '{{.Id}}'` | 0 | PASS | `evidence/rc_image_digest.out` |
| `bash evidence/staging_smoke.sh` | 0 | PASS | `evidence/staging_smoke.out` |
| `docker exec -e NUSANTARA_HEALTHCHECK_PORT=18214 nusantara-rc-staging python scripts/healthcheck.py` | 0 | PASS | `evidence/staging_healthcheck.out` |
| health wait / healthy wait / restart / wait after restart | 0 | PASS | `evidence/staging_wait.*`, `staging_healthy_wait.*`, `staging_restart.*`, `staging_wait_after_restart.*` |
| provider-failure smoke | 0 | PASS | `evidence/provider_failure_*.out` |
| rollback smoke | 0 | PASS | `evidence/rollback_*.out` |
| secret scan | 0 | PASS | `evidence/secret_scan_final.out` |
| staging cleanup / active port check | 0 | PASS | `evidence/staging_cleanup.out`, `active_ports_after.out`, `staging_ports_absent.out` |

## Runtime probes

| Probe | Observed | Status |
|---|---|---|
| `/health` | HTTP 200, `status=ok`, build `sha256:8a3d91c35bdae736db381974588fb2f09b3674919debb160755071dc6240fc8f` | PASS |
| `/readyz` | HTTP 200, `status=degraded`, `provider=ok` HTTP 200, `documents=0` | PASS |
| `/v1/control-plane/model-status` before chat | HTTP 200, `provider=ollama`, `model=llama3.2:1b`, `status=NOT_VERIFIED` | PASS |
| admin negative | HTTP 403 `admin token diperlukan` | PASS |
| `/v1/chat` | HTTP 200, `provider_status=ollama`, `model=llama3.2:1b`, response `PONG` | PASS |
| `/v1/control-plane/model-status` after chat | HTTP 200, `availability=INFERENCE_OBSERVED`, `status=INFERENCE_VERIFIED`, `last_request.provider_status=ollama` | PASS |
| `/v1/chat/history` | HTTP 200, 1 SUCCEEDED turn | PASS |
| Docker healthcheck | exit 0; container reached `healthy` | PASS |

## Failure, restart, persistence, rollback

- Provider failure container used `LLM_BASE_URL=http://127.0.0.1:19999`. `/readyz` returned `degraded` with `provider.status=unavailable` and `URLError`; `/v1/chat` returned controlled HTTP 503 `PROVIDER_UNAVAILABLE` — PASS.
- Staging container was restarted. History before and after: 1 turn, same question and same response — PASS (`evidence/persistence_compare.out`).
- RC container was removed and previous image started with the same data/home volumes. Rollback `/health` 200 and history still showed the same turn — PASS (`evidence/rollback_history.out`).
- Staging used host network port `18214` to reach Ollama bound to host loopback `127.0.0.1:11434`. Active ports remained `11434`, `15274`, `18201`; staging ports `18214–18216` absent after cleanup.

## Configuration / secrets

- `secret_scan_final.out`: 1698 tracked files, 0 tracked `.env`, 39 references/variables, 10 fixtures/placeholders, 0 real credentials.
- `.env.example` uses `your-secret-token-here`; staging token was generated locally and excluded from committed evidence.

## Caveats / BLOCKED

- Knowledge DB was empty (`documents=0`); grounded SOP ingest was not proven.
- IndoBERT/Docling approved artifacts are absent; no real worker was provisioned.
- Ollama production topology is not decided: bridge compose uses `host.docker.internal`, while the active Ollama binds loopback. Staging proof used host network.
- No active service, DB, port, or production deployment was changed.
