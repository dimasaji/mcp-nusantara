# Portability Test Report — Nusantara V1 VPS

- Contract ID: `NUS-V1-VPS-MASTER-001`
- Execution Phase: `Phase 2 — Runtime Stabilization / Linux Portability`
- Date: `2026-11-24`
- Worktree: `/data/workspace/nus-v1-vps-master-20261124/worktrees/engineering`
- Branch / commit under test: `codex/vps-master-engineering-20261124` @ `cfd46391` (base `origin/codex/restructure-20261123` @ `545137e8`)
- Method: reuse existing acceptance evidence, then run only targeted tests and read-only environment checks. No service restart, production deployment, or full regression was performed.

## 1. Environment inventory

| Item | Observed value | Status |
|---|---|---|
| OS | Debian GNU/Linux 13 (trixie) | PASS |
| Kernel | `6.18.60-instabox` | PASS |
| CPU | 4 cores | PASS |
| RAM | 7.8 Gi total, 6.3 Gi available | PASS |
| Root disk | 82% used, 2.7 GB free | PARTIAL |
| Python | `3.13.5` | PASS |
| Node.js | `v22.23.3` | PASS |
| Docker | `29.8.2` | PASS |
| Docker Compose | `5.6.0` | PASS |
| Git | `2.47.3` | PASS |
| Ollama | `0.40.17`, model `llama3.2:1b` | PASS |

## 2. Targeted backend / portability tests

Command:

```bash
env PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m pytest -q \
  tests/test_runtime_portability.py \
  tests/test_backend_runtime_fixture.py \
  tests/test_runtime_readiness.py \
  tests/test_runtime_build_provenance.py
```

Result: **39 passed, 0 failed, 18 warnings in 3.12s**.

Per-file result:

- `tests/test_runtime_portability.py` — 6 passed.
- `tests/test_backend_runtime_fixture.py` — 1 passed.
- `tests/test_runtime_readiness.py` — 8 passed.
- `tests/test_runtime_build_provenance.py` — 24 passed.

Warnings are deprecation/asyncio configuration warnings, not failures.

## 3. Frontend production build

Command: `npm run build` in `frontend/`.

Dependencies were reused from `/data/workspace/nus-v1-postmerge-ec76a9ed/repo/frontend/node_modules` through a temporary symlink. `package.json` and `package-lock.json` are byte-identical between the two worktrees (`sha256 2353a705…` and `256db854…`). The symlink was removed after the build; the worktree is clean.

Result: **PASS**. TypeScript check and Vite build completed, producing `dist/index.html`, two CSS assets, and two JS assets. Rollup emitted only a chunk-size advisory for a 690.49 kB bundle; no build error.

## 4. Docker / compose configuration

Command: `docker compose -f deploy/docker/docker-compose.yml config --quiet`.

Result: **PASS** (`COMPOSE_CONFIG_OK`).

Historical runtime evidence reused, not rerun:

- `reports/vps-docker-readiness/VPS_DOCKER_READINESS_FINAL_REPORT.md` — Docker build, compose config, container smoke, `/health` and `/readyz` PASS at RC commit.
- `reports/engineering-closure/DOCKER_FULLSTACK_ACCEPTANCE_REPORT.md` — marked `PARTIAL / STALE FOR FINAL WP-03 TREE`; no fresh build was performed here to avoid disk pressure and duplicate work.
- Current `docker ps` shows no running containers; live loopback services are process-based, not container-based.

## 5. Current runtime health

Observed on loopback only:

- `http://127.0.0.1:18201/health` → HTTP `200`.
- `http://127.0.0.1:15274/health` → HTTP `200`.

Provenance remains split: those processes run from `/data/workspace/nus-v1-postmerge-ec76a9ed/repo` @ `b77c9c6e`, not from this feature branch or the official integration tip. This is recorded as a reconciliation issue, not a runtime failure.

## 6. Windows-path findings

Targeted scan of `backend/app/**/*.py` found four occurrences:

| File | Finding | Classification |
|---|---|---|
| `backend/app/knowledge/docling_config.py:9` | `LEGACY_TESSERACT = Path('C:/Program Files/Tesseract-OCR/tesseract.exe')` | legacy fallback constant; portability tests pass |
| `backend/app/skills/sop_semantic/engine.py:12` | `ROOT = Path(r"C:\Users\dmaza\mcp-starter")` | isolated helper, no import found from active runtime |
| `backend/app/developer_core/snapshot_manager.py:15` | docstring mentions PowerShell/cmd | documentation only |
| `backend/app/developer_core/hermes_acp_connection.py:49` | reads `LOCALAPPDATA` environment | guarded Windows-only branch |

Conclusion: no active Linux runtime blocker was proven. The isolated `sop_semantic` hardcoded path and legacy Tesseract constant remain tracked portability debt and must be covered by PC/CI Windows validation before cross-platform acceptance is `PASS`.

## 7. Reused prior evidence

- `reports/engineering-closure/CROSS_PLATFORM_ACCEPTANCE_REPORT.md` — Linux portability PASS; 37 Windows-native IPC cases skipped.
- `reports/final-consolidation/STAGING_ACCEPTANCE_REPORT.md` — Gate B PASS for Linux staging at RC with matching build ID.
- `docs/reports/ollama-runtime-v1/NUSANTARA_V1_OLLAMA_FINAL_REPORT.md` — Ollama install, model pull, real inference, provider, backend chat, and frontend chat PASS.

## 8. Verdict

- Linux backend/runtime portability: **PASS** for the targeted suite executed here.
- Frontend production build: **PASS**.
- Docker/compose config: **PASS**; fresh image build on this exact feature commit: **NOT RUN** (stale evidence carried forward).
- Current loopback health: **PASS**, with provenance caveat.
- Full Windows compatibility: **PARTIAL / BLOCKED** pending PC/CI evidence for 37 skipped native IPC cases.

Overall Phase 2: **PARTIAL PASS**. No new critical blocker was introduced; Windows evidence and fresh Docker build remain gated.
