# RUNTIME_MODULE_MAP

**Project:** Nusantara V1
**Contract:** deliverable §12.6, addendum §5.B
**Date:** 2026-11-18
**Method:** live process inspection (`Get-NetTCPConnection`, `Get-CimInstance Win32_Process`) + static subprocess-site scan
**Companion:** `docs/architecture/SERVICE_PORTS.md`

---

## 1. Live runtime topology — measured, not designed

Five TCP listeners were observed on the audit machine. **Only three belong to Nusantara.**

| Port | PID | Process | Command | Owner | Nusantara? |
|---:|---:|---|---|---|---|
| **8000** | 6508 | `python.exe` | `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning` | backend | **YES** |
| **5180** | 14184 | `node.exe` | `vite` dev server | frontend | **YES** |
| **11434** | 14324 | `ollama.exe` | Ollama server | model runtime | **YES (external)** |
| 8001 | 20504 | `python.exe` | `python "C:\Users\dmaza\mcp-setup\pc_api_server.py"` | unrelated project | **NO** |
| 8001 | 20504 | (same process, dual-stack bind) | — | unrelated project | **NO** |

> **Disambiguation.** Port 8001 is served by `C:\Users\dmaza\mcp-setup\pc_api_server.py`, a different repository that happens to be running on the same machine. It is **not** a second Nusantara engine, not a V2 runtime, and shares no code with this repository. It is recorded here so that a later auditor does not mistake it for a duplicate service.

### 1.1 Verdict on the "no second engine" rule

| Rule | Evidence | Result |
|---|---|---|
| Exactly one backend process serving the product | one listener on 8000, `app.main:app` | **PASS** |
| No second Nusantara API port | 8001 belongs to another project entirely | **PASS** |
| No V2 listener | `app.api.v2_routes` router never registered; no `/v2` port exists | **PASS** |
| No duplicate launcher | only `start-nusantara.bat` starts services | **PASS** |

---

## 2. Process inventory

### 2.1 Backend — port 8000

| Property | Value |
|---|---|
| Entry | `uvicorn app.main:app` |
| Module graph root | `app\main.py` (depth 12 — deepest in the graph) |
| Threads | single event loop; blocking work offloaded to subprocesses |
| Health | `GET /v1/health` → `200` `{"status":"ok","service":"nusantara-core","version":"0.1.0","build_id":"sha256:…"}` |
| Healthcheck script | `scripts\healthcheck.py` (used by Docker `HEALTHCHECK`) |
| Log sink | `data\service-v1\` (1,133 run logs) |

Routers registered (`app\main.py:84-86`):

| Router | Prefix | Source |
|---|---|---|
| `api_router` | *(none — `/v1/*` declared per route)* | `app\api\routes.py`, `knowledge_pipeline.py`, `skills.py` |
| `inspection_preview_router` | `/v1` | `app\api\inspection_preview.py` |
| `control_plane_router` | *(none — `/v1/control-plane/*` per route)* | `app\api\control_plane.py` |

`app\api\v2_routes.py` is **not** in this list. That is the whole reason V2 is dead.

### 2.2 Frontend — port 5180

| Property | Value |
|---|---|
| Dev server | `vite` (`npm run dev -- --port 5180`), bound to `127.0.0.1` |
| Production artefact | `control-plane\dist\` (built: 446 modules, `index-Bg4-yd-G.js` 689.90 kB / 206.31 kB gzip) |
| Backend access | same-origin proxy configured in `control-plane\vite.config.ts` |
| Health | HTTP `200` on `/` |

### 2.3 Model runtime — port 11434

| Property | Value |
|---|---|
| Server | Ollama |
| Model in use | `gemma3n:e2b-it-q4_K_M` (~4.5 B parameters, Q4 quantised) |
| Configured by | `.env` → `LLM_PROVIDER=ollama`, `LLM_MODEL=gemma3n:e2b-it-q4_K_M` |
| Outbound from | `app\models\ollama.py` (fan-out 8, fan-in 7 — the most central concrete module) |

`ollama serve` is launched by `start-nusantara.bat` only if `GET /api/tags` fails. It is an **external dependency**, not a Nusantara module. It is the only component whose quality ceiling caps the product (see `HERMES_FORENSIC_AUDIT.md` §4).

### 2.4 Embedding worker — subprocess, no port

| Property | Value |
|---|---|
| Model | `indobenchmark/indobert-base-p1`, 768-dim |
| Measured coverage | 722 / 722 chunks |
| Spawn site | `app\knowledge\worker_process.py` (`StartIndoBertWorker`) |
| Kill path | `worker_process.py:17` — `taskkill.exe /PID <pid> /T /F` |
| Bridge | `app\knowledge\indobert_embedding.py`, `production_embedding_bridge.py` |
| Docker path | separate venv at `/opt/indobert` (`Dockerfile:7-9`), `NUSANTARA_INDOBERT_WORKER=/app/nusantara-models/indobert_worker.py` |

**This is the only in-process-spawned worker on the hot path.** It communicates over stdin/stdout, not HTTP, so it has no port and cannot be reached from outside the host.

> Note: `.env` sets `EMBEDDING_MODEL=local-hash`. The database nevertheless contains 722 chunks embedded with IndoBERT 768-dim. The two are consistent only because ingestion used the IndoBERT bridge explicitly rather than the env default. **This is a configuration ambiguity worth recording** — a fresh ingest run with the default env would produce `local-hash` embeddings and a mixed-dimension corpus. It did not happen here because all 722 chunks carry the same model and dimension. See `DATABASE_SOP_FORENSIC_AUDIT.md` §4.

### 2.5 Tesseract — subprocess, no port

| Property | Value |
|---|---|
| Spawn site | `app\knowledge\sop_table_ocr.py:23` — `subprocess.run([... 'tsv'], input=…)` |
| Purpose | Table OCR fallback |
| Docker image | **not installed** in `python:3.12-slim` — OCR path unavailable inside the container |

### 2.6 Docling worker — subprocess, no port

| Property | Value |
|---|---|
| Modules | `app\knowledge\docling_worker.py`, `docling_layout.py`, `docling_config.py` |
| Environment | separate `requirements-docling.lock` venv (`.venv-docling`, excluded from backup as re-creatable) |
| Known defect | deskew/binarise preprocessing crashes the Docling process — OCR enhancement abandoned |
| Docker | **not included** — container has no Docling |

### 2.7 Git — subprocess, no port

Multiple read-only `git` invocations for provenance and attestation:

| Module | Call |
|---|---|
| `app\devcore\control_plane_projection.py:103` | `git -c core.quotepath=false …` (timeout 5 s) |
| `app\developer_core\gate.py:124` | `git -C <repo> branch -- <branch> HEAD` |
| `app\developer_core\sandbox.py:35` | `subprocess.run(argv, shell=False, cwd=cwd, timeout=…)` |

All are `shell=False` with explicit argv arrays except the sandbox runner, which is the guarded execution path.

---

## 3. Complete request path — browser to answer

```
┌──────────┐   HTTP 5180    ┌───────────────┐   proxy /v1/*   ┌──────────────────┐
│ Browser  │ ─────────────► │ Vite (node)   │ ──────────────► │ uvicorn :8000    │
└──────────┘                └───────────────┘                 │ app.main:app     │
                                                              └────────┬─────────┘
                                                                       │
                          ┌────────────────────────────────────────────┘
                          ▼
                ┌──────────────────────┐
                │ app.api.routes:1103  │  chat()
                │ require_admin        │  app.security.auth:12
                │ _check_rate_limit    │  30 req / 60 s / session
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │ HermesAgent          │  app.hermes.agent:219
                │ .execute_v1(request) │
                └──────────┬───────────┘
             ┌─────────────┼──────────────┬────────────────┐
             ▼             ▼              ▼                ▼
     ┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌──────────────┐
     │ arithmetic │ │ SOP fields │ │ Knowledge   │ │ provider     │
     │ (no model) │ │ (no model) │ │ Engine      │ │ ollama:11434 │
     └────────────┘ └────────────┘ └──────┬──────┘ └──────┬───────┘
                                          ▼               ▼
                                  ┌──────────────┐ ┌────────────┐
                                  │ SQLite       │ │ grounding  │
                                  │ 52.75 MB     │ │ guard      │
                                  └──────────────┘ └─────┬──────┘
                                                          ▼
                                              grounded answer  OR  abstain
```

Every arrow was verified by reading the call site, not inferred from names.

---

## 4. Startup and shutdown sequence

`start-nusantara.bat` (verbatim behaviour):

1. `python --version` guard → abort if Python missing.
2. `curl http://127.0.0.1:11434/api/tags` → if absent, `start "" ollama serve` and wait 5 s.
3. Start backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000` in its own `cmd` window.
4. Wait 8 s, then `curl http://127.0.0.1:8000/v1/health` → abort if not healthy.
5. Start frontend: `npm run dev -- --port 5180` in its own `cmd` window.
6. Print the three URLs.

`stop-nusantara.bat` — kills by port/window title.
`status-nusantara.bat` — `curl` health + `curl /api/tags`, prints RUNNING/NOT RUNNING per service.
`doctor-nusantara.bat` — deeper diagnostics.

**No duplicate launcher exists.** There is no PowerShell launcher, no Docker-Compose launcher, and no `Makefile` that starts services. `docker-compose.yml` builds the container but is not the official local start path.

---

## 5. Module → runtime role

| Package | Modules | Runtime role |
|---|---:|---|
| `app.api` | 8 | HTTP surface (61 routes; `v2_routes` dead) |
| `app.hermes` | 2 | Orchestrator (`agent.py`, 1,468 lines) |
| `app.knowledge` | 43 | Ingestion, retrieval, grounding, SOP review |
| `app.models` | 14 | Provider adapters (Ollama primary) |
| `app.core` | 13 | Identity, config, error taxonomy |
| `app.security` | 6 | Auth + V1 knowledge boundary |
| `app.observability` | 4 | Logging, correlation context |
| `app.approval` | 6 | Runtime authorisation, approval state |
| `app.policy` | 4 | Policy engine |
| `app.memory` / `app.context` | 8 | Session state |
| `app.workflow` / `app.orchestration` | 8 | LangGraph paths |
| `app.developer_core` / `app.devcore` | 38 | Developer-control surface (**parallel trees**) |
| `app.v2` | 4 | **Dead** — never imported by a registered router |
| `app.language` | 8 | Normalisation, intent |
| `app.tools` / `app.mcp` | 11 | Tool governance, MCP |
| remaining 18 packages | 71 | Supporting domains |

---

## 6. Ports and their justification

| Port | Service | Bind | Reachable from outside host | Justification |
|---:|---|---|---|---|
| 8000 | backend | `127.0.0.1` | **No** | API |
| 5180 | frontend dev | `127.0.0.1` | **No** | UI |
| 11434 | Ollama | loopback default | **No** | model inference |
| — | IndoBERT worker | stdio | No | no socket |
| — | Docling worker | stdio | No | no socket |
| — | Tesseract | stdio | No | no socket |

**Every Nusantara listener binds to loopback.** The product is not exposed to the network by default. This is correct for a single-operator V1 and is the reason the shared admin token is an accepted risk rather than a critical one.

---

## 7. Findings

| # | Finding | Severity | Action |
|---|---|---|---|
| R1 | Exactly one backend process, one frontend, one model runtime | — | Verified |
| R2 | Port 8001 belongs to an unrelated project, not a second engine | — | Documented for future auditors |
| R3 | `EMBEDDING_MODEL=local-hash` in `.env` contradicts the 768-dim IndoBERT corpus | **Medium** | Recorded; a fresh ingest with defaults would corrupt corpus consistency |
| R4 | Tesseract and Docling absent from the container | Medium | OCR unavailable in Docker, available on host |
| R5 | Worker teardown uses `taskkill.exe` (Windows-only) | Low | Blocks Linux portability |
| R6 | All listeners loopback-bound | — | Correct |

---

## 8. Reproducing this map

```powershell
Get-NetTCPConnection -State Listen | Where-Object LocalPort -in 8000,5180,11434
Get-CimInstance Win32_Process -Filter "ProcessId=<pid>" | Select-Object CommandLine
```
