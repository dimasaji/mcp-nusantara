# VPS Runtime Recovery Report — Nusantara V1

- Commit SHA: `d2cfc60a0d88c93ce561f40c01d67e5f53910770`
- Branch: `codex/vps-final-stabilization-20261123`
- Worktree: `/data/workspace/nus-v1-vps-final-20261123/worktrees/release`
- Isolated runtime: backend `127.0.0.1:18211`, frontend `127.0.0.1:15284`
- Active runtime: backend `127.0.0.1:18201`, frontend `127.0.0.1:15274` — untouched
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Collected: 2026-11-23T22:14:16Z–22:15:16Z

## Gate C verdict

**PASS** — the release candidate starts cleanly in an isolated runtime, serves the canonical readiness alias, and completes an Ollama-backed chat round trip. Active runtime was not restarted, redeployed, or modified.

## Isolation controls

| Control | Implementation | Evidence |
|---|---|---|
| Source | New worktree at `d2cfc60a`; `app.__file__` resolves to `.../worktrees/release/backend/app/__init__.py` | `c_import_path` exit 0 |
| Ports | Unused `18211`/`15284` selected; `c_ports_available` empty before start | `c_ports_available` exit 0 |
| Database | Read-only source DB copied with `cp -n` to `runtime/isolated/data/knowledge.db`; source not opened for write | `c_copy_db` (copy succeeded), `c_copy_db_check` exit 0 |
| DB integrity | Isolated copy `quick_check=ok`, `9` tables | `c_copy_db_check` exit 0 |
| Secrets | Synthetic token `local-verification-only`; no live admin token read or printed | `c_start_backend` command log |
| Dependencies | Reused existing `/data/workspace/nus-v1-postmerge-ec76a9ed/env` and existing frontend `node_modules`; no new dependency installed | `c_python_version`, `c_node_modules_link` exit 0 |
| Active services | `/health` on `18201` still HTTP 200 after isolated probes; `ss` still lists active PIDs 7680/7740 | `c_active_runtime_untouched`, `c_ports_after_isolated` exit 0 |

`c_copy_db` logged exit 127 because the optional `sqlite3` CLI is not installed. The `cp -n` step had completed; the follow-up `c_copy_db_check` used Python `sqlite3` in read-only URI mode and returned `ok`/`9`.

## Runtime probe results

| Check | Result | Evidence |
|---|---|---|
| Backend `/health` | HTTP 200, `build_id sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b4754f87478480331` | `c_backend_health` |
| Backend `/v1/health` | HTTP 200 | `c_backend_v1_health` |
| Canonical `/readyz` alias | HTTP 200, `status=degraded`, `knowledge_database=empty/0 documents`, `provider=ok` | `c_readyz_alias` |
| Existing `/v1/health/ready` | HTTP 200, same body as alias | `c_v1_ready` |
| Backend `/v1/metrics` | HTTP 200 | `c_backend_metrics` |
| Frontend `/` | HTTP 200, 516 bytes | `c_frontend_root` |
| Frontend `/health` proxy → backend | HTTP 200, same build ID | `c_frontend_health_proxy` |
| Ollama `/api/version` | HTTP 200 | `c_ollama_version` |
| Chat direct `POST /v1/chat` | HTTP 200, response `PONG`, `provider_status=ollama`, model `llama3.2:1b` | `c_chat_pong_valid` |
| Chat history | HTTP 200, one `SUCCEEDED` turn for the same session | `c_chat_history_valid` |
| Model status canonical route | HTTP 200, `status=INFERENCE_VERIFIED`, `availability=INFERENCE_OBSERVED` | `c_model_status_canonical` |
| Model status through frontend proxy | HTTP 200 | `c_model_status_frontend_proxy` |
| Active backend `/health` | HTTP 200, unchanged | `c_active_runtime_untouched` |

An initial chat probe used non-conforming synthetic IDs and correctly returned HTTP 422; it was replaced with valid IDs in `c_chat_pong_valid`. An initial `model-status` probe used an undocumented path and returned HTTP 404; the canonical route is `/v1/control-plane/model-status`, verified HTTP 200.

## Findings

1. **Readiness alias fixed in candidate, not in active runtime.** `/readyz` is additive to `/v1/health/ready` and returns HTTP 200 in the isolated release candidate. Active `18201` still returns 404 because no deploy/restart was performed, as required.
2. **Readiness is honestly degraded, not falsely green.** Both isolated and active knowledge DBs contain `0` documents (`c_readyz_alias`, `c_active_db_documents`). The probe reports `degraded`; this is expected until official knowledge ingestion is authorized and completed on the PC side.
3. **Ollama path works.** Chat `PONG`, history, and model status confirm the local `llama3.2:1b` provider is reachable and observed in the isolated process.
4. **IndoBERT worker artifacts remain absent.** No `indobert_worker.py` or `nusantara-models/.venv` exists in any checked workspace; synthetic ingest/search cannot be claimed as recovered. Carried to `REGRESSION_ROOT_CAUSE_AND_FIX_REPORT.md`.
5. **No active-state mutation.** Ports, PIDs, DB contents, and service process commands for active runtime remained unchanged.

## Command evidence index

Primary evidence: `c_ports_available.*`, `c_python_version.*`, `c_import_path.*`, `c_copy_db.*`, `c_copy_db_check.*`, `c_node_modules_link.*`, `c_start_backend.*`, `c_start_frontend.*`, `c_wait_ready.*`, `c_ports_active.*`, `c_backend_health.*`, `c_backend_v1_health.*`, `c_readyz_alias.*`, `c_v1_ready.*`, `c_backend_metrics.*`, `c_frontend_root.*`, `c_frontend_health_proxy.*`, `c_ollama_version.*`, `c_chat_pong.*`, `c_chat_pong_valid.*`, `c_chat_history_valid.*`, `c_model_status.*`, `c_model_status_canonical.*`, `c_model_status_frontend_proxy.*`, `c_active_runtime_untouched.*`, `c_active_db_documents.*`, `c_isolated_processes.*`, `c_ports_after_isolated.*`. All timestamps and exit codes are in `evidence/commands.tsv`.
