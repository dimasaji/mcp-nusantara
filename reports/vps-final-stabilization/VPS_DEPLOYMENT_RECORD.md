# VPS Deployment Record — Nusantara V1

- Recorded: 2026-11-23T22:31:24Z
- Integration commit deployed: `b77c9c6e3d547b1d5a34c633abd0fb01e5aef046`
- PR #18 merge commit: `3e3eedcf82f326bc609df25056c50536d487807f` (2026-11-23T22:29:26Z)
- PR #17 merge commit: `b77c9c6e3d547b1d5a34c633abd0fb01e5aef046` (2026-11-23T22:30:10Z)
- Evidence prefix: `i_*` in `/data/workspace/nus-v1-vps-final-20261123/evidence/`; bundled here in `deployment-evidence/`

## Deployment verdict

**DEPLOYED (in-place code restart)** after explicit owner confirmation. Deployment used the existing ports, environment, DB path, and process model. No Docker compose deploy, DB write, migration, port change, secret change, or frontend restart was performed.

## Pre-deploy state

| Item | Value | Evidence |
|---|---|---|
| Active commit | `b44b01e7d24efbd5ff7f4830cc71624b5aa4bf7f` | `i_head` before fast-forward |
| Backend PID | `7680`, `127.0.0.1:18201` | `i_new_process`, `i_ports` after restart shows replacement |
| Frontend PID | `7740`, `127.0.0.1:15274` | unchanged throughout |
| `/health` | HTTP 200, build `sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b4754f87478480331` | `i_pre_health` |
| `/readyz` | HTTP 404 | `i_pre_readyz` |
| DB SHA-256 | `32eb169f79dfe021e5dd4fd007e43e816369dcd80685c7b8dc4375df7b9cf122` | `i_pre_db` |
| DB mtime | `2026-11-23 17:53:05.461642521 +0000` | `i_pre_db` |
| DB path env | `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/verify-final/staging-db/verify.db` | `i_env_db` |

## Actions executed

1. `git fetch origin codex/restructure-20261123` — exit 0 (`i_fetch`).
2. `git merge --ff-only origin/codex/restructure-20261123` in active repo — exit 0 (`i_ff`); HEAD became `b77c9c6e3d547b1d5a34c633abd0fb01e5aef046` (`i_head_after`).
3. Backend PID `7680` received SIGTERM; new uvicorn started with the **same environment read from `/proc/7680/environ`**, same cwd `/data/workspace/nus-v1-postmerge-ec76a9ed/repo/backend`, same command, same port `18201` — new PID `19130` (`i_restart_backend`, `i_new_process`).
4. Frontend PID `7740` was not touched.
5. No deploy script, Docker command, DB command, or secret value was printed or changed.

## Post-deploy verification

| Probe | Result | Evidence |
|---|---|---|
| Backend `/health` | HTTP 200, same build ID | `i_health` |
| Backend `/readyz` | HTTP 200 `status=degraded`, `knowledge_database=empty`, `documents=0`, `provider=ok` | `i_readyz` |
| Backend `/v1/health/ready` | HTTP 200, same body as `/readyz` | `i_v1_ready` |
| Frontend `/` | HTTP 200 | `i_frontend` |
| Frontend `/health` | HTTP 200, same build ID | `i_frontend_health` |
| `/v1/control-plane/model-status` | HTTP 200, provider `ollama`, model `llama3.2:1b`, `status=NOT_VERIFIED`, `knowledge=NOT_VERIFIED` | `i_model` |
| Listeners | `18201` PID `19130`, `15274` PID `7740`, `11434` Ollama | `i_ports` |
| DB SHA-256 | unchanged `32eb169f...f122` | `i_db_after` |
| DB mtime | unchanged `2026-11-23 17:53:05.461642521 +0000` | `i_db_after` |
| Active repo status | clean | `i_status_after` |
| Active repo HEAD | `b77c9c6e3d547b1d5a34c633abd0fb01e5aef046` | `i_head_after` |

Model status is `NOT_VERIFIED` because no chat request was issued after restart; a synthetic chat was intentionally not run to avoid writing active DB history. The `degraded` readiness state is honest and expected with `documents=0`.

## Residual conditions

- Official PIAK-03 acceptance remains PC-bound per `PC_PIAK03_ACCEPTANCE_HANDOFF.md`.
- Docker image findings remain open per `VPS_RELEASE_AND_ROLLBACK_PLAN.md`; this deploy was in-place source/code restart only.
- Rollback target is the previous source commit `b44b01e7` with the same DB/ports/env; no DB restore is required because no DB mutation occurred.

## Command evidence index

`i_env_db.*`, `i_fetch.*`, `i_ff.*`, `i_head.*`, `i_pre_health.*`, `i_pre_readyz.*`, `i_pre_db.*`, `i_restart_backend.*`, `i_wait_new.*`, `i_health.*`, `i_readyz.*`, `i_v1_ready.*`, `i_frontend.*`, `i_frontend_health.*`, `i_model.*`, `i_ports.*`, `i_db_after.*`, `i_head_after.*`, `i_status_after.*`, `i_new_process.*`, plus `commands.tsv`. All commands, exit codes, and timestamps are in `deployment-evidence/commands.tsv`.
