# VPS Forensic Baseline — Nusantara V1

- Commit SHA: `b44b01e7d24efbd5ff7f4830cc71624b5aa4bf7f`
- Branch: `codex/vps-final-stabilization-20261123` (report worktree), source branch `codex/vps-eng-completion-20261123`
- Environment: instabox `m_agq7353a3z6y6wltyegptrsp3e`, Debian 13, 4 vCPU, 7.8 GiB RAM, 20 GiB `/data`
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Collected: 2026-11-23T22:06:27Z–22:09:36Z
- Mode: read-only forensic audit. No active service restart, port change, deploy, DB change, or secret disclosure.

## Gate A verdict

**COMPLETE** — baseline inventory verified. No production changes were made.

## Host and permissions

| Item | Value | Evidence |
|---|---|---|
| Hostname | `instabox-nusantara` | `a_uname` exit 0, 22:08:38Z |
| Kernel | `6.18.60-instabox #1 SMP PREEMPT_DYNAMIC` x86_64 | `a_uname` |
| OS | Debian 13 | `/etc/os-release`, `a_os` context |
| CPU | 4 | `a_cpu` exit 0 |
| Memory | 7.8 GiB total, 6.0 GiB free, 6.3 GiB available | `a_memory` exit 0 |
| Disk | `/dev/vdb` 20 G, 11 G used, 9.3 G available, 53% | `a_disk` exit 0 |
| Identity | `uid=1000(user) gid=1000(user)`, sudo/docker groups | `a_identity` exit 0 |
| Umask | `0002` | `a_umask` exit 0 |

## Git state

| Item | Value | Evidence |
|---|---|---|
| Current source repo | `/data/workspace/nus-v1-postmerge-ec76a9ed/repo` | `a_git_status` exit 0 |
| Current HEAD | `b44b01e7d24efbd5ff7f4830cc71624b5aa4bf7f` | `a_git_head` exit 0 |
| Worktree status | clean, tracking `origin/codex/vps-eng-completion-20261123` | `a_git_status` |
| Remote | `git@github-nusantara:dimasaji/mcp-nusantara.git` | `a_git_remote` exit 0 |
| Default branch | `codex/fullroot-control-20261007` | `a_git_branch` |
| Integration branch | `codex/restructure-20261123` @ `ec76a9ed` | `a_git_branch` |
| New report worktree | `/data/workspace/nus-v1-vps-final-20261123/worktrees/release` @ `b44b01e7` | `b_worktree_add`, `b_worktree_head` exit 0 |
| `git diff --check` | exit 0 | `a_git_diff_check` |

Observed worktrees include several historical integration/staging checkouts and two detached verification worktrees. None of them was modified during Phase A. One stale `/tmp/nus-restructure-check` entry is marked prunable; it was not pruned.

## Runtime processes and source provenance

| Component | PID(s) | Command/cwd | Source SHA | Evidence |
|---|---|---|---|---|
| Backend | 7680 | `uvicorn app.main:app --host 127.0.0.1 --port 18201` from `.../repo/backend` | `b44b01e7` | `a_backend_cwd`, `a_backend_git`, `a_processes` exit 0 |
| Frontend | 7728, 7739, 7740 | `npm run dev --port 15274` → vite from `.../repo/frontend` | `b44b01e7` | `a_frontend_cwd`, `a_frontend_git`, `a_processes` exit 0 |
| Ollama | 1090 | `/usr/local/bin/ollama serve`, systemd `ollama.service` | model `baf6a787fdff` | `a_processes`, `a_systemd`, `a_ollama_models` exit 0 |
| Docker | 1200 | `dockerd` active; no application container observed on active ports | n/a | `a_systemd`, `a_ports` |

The historical “legacy path / old backend processes” baseline is not the current active state: both running application processes resolve to the canonical `backend/` and `frontend/` directories at `b44b01e7`.

## Ports and health

| Port/process | Result | Evidence |
|---|---|---|
| `127.0.0.1:18201` backend | `/health` HTTP 200 | `a_active_backend_health` exit 0 |
| `127.0.0.1:18201/readyz` | HTTP 404 | `a_active_backend_ready` exit 0 |
| `127.0.0.1:15274` frontend | `/` HTTP 200, 516 bytes | `a_active_frontend_root` exit 0 |
| `127.0.0.1:15274/health` | HTTP 200 | `a_active_frontend_health` exit 0 |
| `127.0.0.1:11434` Ollama | `/api/version` HTTP 200 | `a_ollama_api` exit 0 |
| `127.0.0.1:5901` Xvnc, `22` SSH | infrastructure only | `a_ports` |

No reverse-proxy rules were found in `/etc/nginx`, `/etc/apache2`, `/etc/caddy`, or `/etc/haproxy` (`a_proxy_config`, exit 0, empty output).

## Toolchain and dependencies

| Tool | Version/source | Evidence |
|---|---|---|
| Python | system `python3`; application env `/data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python` | `a_python`, process command |
| Node | `/usr/local/bin/node` | `a_node` exit 0 |
| npm | `/usr/local/bin/npm` | `a_npm` exit 0 |
| Docker/Compose | installed and daemon running | `a_docker`, `a_compose`, `a_systemd` |
| Ollama model | `llama3.2:1b`, ID `baf6a787fdff`, 1.3 GB | `a_ollama_models` exit 0 |

## Environment configuration

Only key names were read from the live backend process; no values or secrets were printed.

| Key | Evidence |
|---|---|
| `NUSANTARA_ADMIN_TOKEN` | `a_backend_env_keys` exit 0 |
| `NUSANTARA_KNOWLEDGE_DB` | `a_backend_env_keys` exit 0 |

The knowledge DB path value was read because it is a filesystem path, not a credential: `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/verify-final/staging-db/verify.db`.

## Data and backup inventory

- Relevant app DBs observed: `data/knowledge/nusantara_knowledge.db`, `backend/data/knowledge/nusantara_knowledge.db`, active `runtime/verify-final/staging-db/verify.db`, and several disposable staging/probe DBs.
- Read-only PRAGMA checks: WAL journal mode, `quick_check=ok`, 9 tables for the main repo DB; 2 tables for the backend-local DB; 9 tables for the staging knowledge DB (`a_app_db_pragmas`, exit 0).
- Backup/restore rehearsal artifacts exist under `/data/workspace/nus-v1-integration-20261123/backups/20261123-active-data/` and `logs/backup-restore-rehearsal.log`; they were not modified.
- No operational DB was deleted, overwritten, migrated, or copied.

## Observed issue reconciliation

| Item | Previous claim | Current evidence | Disposition |
|---|---|---|---|
| Frontend HTTP 404 | historical baseline | HTTP 200, 516 bytes at `:15274/` | Fixed/no longer active |
| Old backend legacy paths | historical baseline | PID 7680 cwd canonical `backend/`, SHA `b44b01e7` | Not current |
| Ollama missing model | environmental concern | `llama3.2:1b` installed and daemon active | Available |
| Admin ingest regression | PR #17 | fix commit `db32ee40` in active SHA | Fixed |
| `/readyz` | expected by Phase C | active endpoint returns 404 | Unresolved; must verify canonical route and patch if missing |
| 86 failed/48 errors baseline | prior commit/environment | must be revalidated in Phase D | Not yet closed |
| 2,052 Ruff findings | prior baseline | previous isolated run showed 51 current findings | Revalidate in Phase D |
| Original SOP PDF/index | PC-side only | no official SOP dataset on VPS | Environment-blocked by design |

## Security/privacy notes

- No secret values, tokens, personal data, or database dumps were printed or copied.
- `.env.example` and compose templates exist; no real `.env` file was found in the active repo.
- Operational data remains on local disk; nothing was uploaded to GitHub during Phase A.

## Command evidence index

All commands are recorded in `/data/workspace/nus-v1-vps-final-20261123/evidence/commands.tsv` as `timestamp`, `name`, `exit_code`, `command`. Primary evidence files:
`a_uname.*`, `a_cpu.*`, `a_memory.*`, `a_disk.*`, `a_identity.*`, `a_umask.*`, `a_git_status.*`, `a_git_head.*`, `a_git_branch.*`, `a_git_worktree.*`, `a_git_remote.*`, `a_git_log.*`, `a_git_diff_check.*`, `a_ports.*`, `a_processes.*`, `a_systemd.*`, `a_backend_cwd.*`, `a_backend_git.*`, `a_frontend_cwd.*`, `a_frontend_git.*`, `a_backend_env_keys.*`, `a_ollama_models.*`, `a_ollama_api.*`, `a_active_backend_health.*`, `a_active_backend_ready.*`, `a_active_frontend_root.*`, `a_active_frontend_health.*`, `a_filesystem_scan.*`, `a_app_db_pragmas.*`, `a_proxy_config.*`, `a_log_inventory.*`, `a_pr_14.*`, `a_pr_15.*`, `a_pr_16.*`, `a_pr_17.*`, `a_pr_list.*`, `b_worktree_add.*`, `b_worktree_head.*`, `b_worktree_status.*`.
