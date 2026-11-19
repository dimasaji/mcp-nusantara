# SOURCE_BASELINE_REPORT

**Project:** Nusantara V1
**Contract:** MASTER DEVELOPER CONTRACT — Phase 3 (Git and repository baseline)
**Date:** 2026-11-18
**Baseline commit:** `7867ba3508684ef47ffc586e8553cd2ebc72080e`
**Branch:** `codex/fullroot-control-20261007`
**Purpose:** Freeze the "before" state so every later change is measurable against it.

---

## 1. Repository identity

| Property | Value |
|---|---|
| Working copy | `C:\Users\dmaza\mcp-starter` |
| Backup of record | `E:\nusantara\mcp-starter` (read-only) |
| Remote | `origin` → `codex/fullroot-control-20261007` |
| Upstream HEAD | in sync with local at time of audit |
| Tracked files | **1,727** |
| Tracked bytes | ~18.6 MB |
| On-disk files (all, incl. venvs/models) | **159,704** |
| On-disk size (all) | **16.135 GB** |
| Python interpreter in `.venv` | CPython **3.13.15** (MSC v.1944 64-bit) |

The gap between 18.6 MB tracked and 16.1 GB on disk is the central finding of this baseline: **99.9 % of the bytes on disk are untracked runtime artifacts**, not the product.

---

## 2. Code baseline (lines of code)

Measured by walking the tree and counting raw lines per extension.

| Area | Path | Files | Lines |
|---|---|---|---|
| Backend application | `app\` | 247 | **52,431** |
| Backend tests | `tests\` | 182 | 21,108 |
| Frontend source | `control-plane\src\` | 35 | 3,754 |
| Frontend tests | `control-plane\tests\` | 30 | 2,377 |
| Automation scripts | `scripts\` | 165 | 33,577 |
| Documentation | `docs\` | 383 | 59,889 |

The product itself is ~56k lines of backend and ~6k lines of frontend. Everything else is scaffolding, tests, documentation, and residue.

---

## 3. Backend module baseline

36 Python packages under `app\`, 247 modules:

| Package | Modules | Package | Modules |
|---|---|---|---|
| `knowledge` | 43 | `research` | 12 |
| `developer_core` | 29 | `devcore` | 9 |
| `models` | 14 | `language` | 8 |
| `core` | 13 | `api` | 8 |
| `tools` | 7 | `approval` | 6 |
| `hardening` | 6 | `problem` | 6 |
| `security` | 6 | `workflow` | 6 |
| `app` | 5 | `context` | 5 |
| `reasoning` | 5 | `semantic` | 5 |
| `governance` | 4 | `mcp` | 4 |
| `memory` | 4 | `observability` | 4 |
| `policy` | 4 | `v2` | 4 |
| `action` | 3 | `execution` | 3 |
| `experience` | 3 | `improvement` | 3 |
| `skills` | 3 | `evaluation` | 2 |
| `handoff` | 2 | `hermes` | 2 |
| `orchestration` | 2 | `rag` | 2 |
| `sop_semantic` | 2 | `trust` | 2 |
| `runtime` | 1 | `ui` | — |

### 3.1 Structural risks visible at baseline

| Finding | Evidence | Disposition |
|---|---|---|
| `app\v2\` exists (4 modules) with a live `app\api\v2_routes.py` (23 import edges) | `main.py` line 27–28 explicitly excludes it: *"V1-only runtime: keep V2 code archived in place without importing..."*; `tests\test_v2_disabled.py` enforces the exclusion | **ARCHIVE-CANDIDATE** — V2 must not ship; see `AI_LEGACY_CLEANUP_REPORT.md` |
| `app\developer_core\` (29) vs `app\devcore\` (9) | Two parallel "developer core" trees | **MERGE-CANDIDATE** — requires functional review, not attempted in this pass |
| Three `.before_*_patch.py` files inside `app\knowledge\` | `production_kb.before_authority_patch.py`, `production_kb.before_metadata_authority_patch.py`, `production_semantic_retriever.before_authority_hydration.py` | **ARCHIVE** |
| 11 `.backup*` files inside `app\` | `routes.py.backup`, `routes.py.backup-20261001`, `agent.py.backup-score-gate-…`, `schemas.py.backup-…`, `engine.py.backup`, `engine.py.backup_1.3.0`, `engine.py.backup_1.4.0`, `intent.py.backup`, 2 × `index.html.backup-…` | **ARCHIVE** |
| `app.api.routes` has fan-out **34** | `MODULE_GRAPH_EDGES.csv` | God module — bounded by contract, not refactored |

---

## 4. API surface baseline

**61 route declarations** parsed from `app\api\*.py`.

| Route group | Count | Route group | Count |
|---|---|---|---|
| `/reviews` | 7 | `/metrics` | 2 |
| `/health` | 4 | `/memory` | 2 |
| `/chat` | 3 | `/approvals` | 2 |
| `/decisions` | 2 | `/documents` | 2 |
| `/hermes` | 2 | `/workflow` | 2 |
| `/knowledge` | 2 | `/dev` | 2 |
| remaining 26 groups | 1 each | | |

Full machine-readable inventory: `ROUTE_INVENTORY.json`.

> Note: `/v2/*` routes are declared inside `app\api\v2_routes.py` but that router is **never registered** — `app\main.py` includes only `api_router`, `inspection_preview_router` (`/v1`), and `control_plane_router`.

---

## 5. Module dependency baseline

**94 modules, 302 intra-`app` import edges.**

### Highest fan-out (imports the most of the system)

| Module | Fan-out | Reading |
|---|---|---|
| `app.api.routes` | 34 | Entry point orchestration god-module |
| `app.api.v2_routes` | 23 | Dead code (unregistered) |
| `app.hermes.agent` | 16 | Hermes orchestration |
| `app.api.control_plane` | 12 | Control Plane API |
| `app.main` | 11 | App assembly |
| `app.devcore.core` | 9 | Developer core |
| `app.models.ollama` | 8 | Provider |
| `app.api.knowledge_pipeline` | 7 | Pipeline API |
| `app.knowledge.rag` | 7 | Retrieval |
| `app.api.runtime_readiness` | 6 | Readiness |

### Highest fan-in (the spine everything depends on)

| Module | Fan-in |
|---|---|
| `app.core.runtime_identity` | 12 |
| `app.observability.context` | 10 |
| `app.core.nusantara_config` | 8 |
| `app.governance.tools` | 8 |
| `app.models.ollama` | 7 |
| `app.security.auth` | 7 |
| `app.observability.logging` | 7 |
| `app.models.base` | 7 |
| `app.core.config` | 6 |
| `app.knowledge.sop_review` | 6 |

`app.api.v2_routes` appearing at fan-out 23 while being unreachable confirms V2 is a fully-built parallel stack sitting inside the V1 product. Full edge list: `MODULE_GRAPH_EDGES.csv`.

---

## 6. Database baseline

`data\knowledge\nusantara_knowledge.db` — SQLite, 52.75 MB, `integrity_check = ok`.

| Table | Rows | Columns | Role |
|---|---|---|---|
| `documents` | 65 | 9 | Document registry |
| `chunks` | 722 | 13 | Retrieval units + embedding |
| `document_extractions` | 193 | 9 | Extraction cache |
| `knowledge_pipeline_runs` | 178 | 8 | Ingestion run log |
| `sop_review_events` | **720** | 8 | Immutable audit trail |
| `sop_review_trials` | 148 | 8 | Review Q&A trials |
| `sop_review_sessions` | 56 | 3 | Review sessions |
| `sop_review_pilots` | 14 | 1 | Pilot document set |
| `knowledge_pipeline_config` | 1 | 4 | Watcher config |

Indexes: `idx_chunks_document`, `idx_chunks_dimension`, `idx_knowledge_pipeline_hash`.

No shadow databases are used by the runtime. Other `.db` files under `data\` are historical snapshots, fixtures, or the SQLite file backing `data\nusantara\`, none of which the V1 chat path opens.

---

## 7. Frontend baseline

`control-plane\` — React 19 + Vite 7 + TanStack Router/Query + zod + @xyflow/react.

| Layer | Files | Notable |
|---|---|---|
| `src\` | 35 | 3,754 lines |
| `tests\` | 30 | vitest |
| `e2e\` | 12 | Playwright |

Largest modules: `human.tsx` 47.9 KB, `engineering-evidence.ts` 29.6 KB, `api.ts` 30 KB, `overview.tsx` 22.1 KB, `human.tsx.bak` 30.1 KB (**stale backup, ARCHIVE**).

`package.json` scripts: `dev` (`vite --host 127.0.0.1`), `build` (`tsc --noEmit && vite build`), `test` (`vitest run`), `e2e` (`playwright test`).

**Known build blocker at baseline:** `tsc` fails with `TS2322` at `src\overview.tsx(199,119)` — `onChanged` is not a declared prop. `vite build` also fails with `esbuild` "Access is denied" on a temp file inside `control-plane\.build-temp-941059bf39fc4a9496f5b341a53ea75a\` (a stale 125-file build cache). Both must be resolved before `COPY control-plane/dist` can be restored in the `Dockerfile`.

---

## 8. Dependency baseline

### Python (`pyproject.toml`, name `nusantara-ai`)

| Scope | Packages |
|---|---|
| Core | `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `pydantic>=2.9`, `pydantic-settings>=2.5`, `python-dotenv>=1.0`, `httpx>=0.27`, `haystack-ai==2.31.1` |
| `sop` | `pypdf>=6.20,<7`, `pymupdf>=1.28,<2`, `Pillow>=10` |
| `mcp` | `mcp>=1.30,<2` |
| `workflow` | `langgraph==1.2.14` |
| `langchain` | `langchain>=1.4`, `langgraph>=0.2`, `langchain-ollama>=0.2` |
| `dev` | `pytest>=8.3`, `pytest-asyncio`, `ruff`, `mypy`, `pytest-cov`, `requests` |

No `requirements.txt` exists. `requirements-docling.lock` pins the separate Docling environment.

### Node (`control-plane\package.json`)

Runtime: `react@19`, `react-dom@19`, `@tanstack/react-router@1`, `@tanstack/react-query@5`, `zod@4`, `@xyflow/react@12`.
Dev: `typescript@5`, `vite@7`, `@vitejs/plugin-react@5`, `vitest@3`, `@testing-library/*`, `@playwright/test`, `jsdom@26`, `@types/*`.

---

## 9. Test baseline

| Metric | Value |
|---|---|
| Test modules in `tests\` (root) | **165** `.py` files |
| Plus 5 `.bak-*` disabled copies | excluded by `--ignore-glob=*.bak-*.py` |
| Frontend unit tests | 30 files (vitest) |
| Frontend E2E specs | 12 (Playwright) |
| Pytest config | `testpaths=["tests"]`, `asyncio_mode=auto`, `--strict-markers`, `--strict-config` |

Measured passing counts are recorded in `TEST_RUNTIME_AUDIT.md` and `REGRESSION_TEST_REPORT.md`; this baseline only freezes the shape.

---

## 10. Metadata defect found in baseline

`pyproject.toml` declares:

```toml
name = "nusantara-ai"
version = "2.0.0a3"
description = "NUSANTARA AI V2 - FastAPI, MCP, governed tools, audit trail"
```

This is **wrong for V1**: the shipped product is Nusantara V1 and the runtime explicitly refuses to register V2. This is a documentation/metadata defect, not a functional one, and is corrected during restructuring (see `RESTRUCTURING_CHANGELOG.md`).

---

## 11. Baseline acceptance

| Baseline element | Frozen value |
|---|---|
| Commit | `7867ba35` |
| Backend LOC | 52,431 (247 files) |
| Frontend LOC | 3,754 (35 files) |
| Routes | 61 |
| Module import edges | 302 |
| DB documents / chunks / events | 65 / 722 / 720 |
| DB SHA-256 | `9e3e0d7a…f53c407` |
| Test modules | 165 |
| Tracked files | 1,727 |
| On-disk files | 159,704 |

Every subsequent section of this contract measures against these numbers. **No later claim of improvement is valid unless these values are reproduced or exceeded.**
