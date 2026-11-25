# VPS_DEPLOYMENT_ARCHITECTURE — Nusantara V1

- Audit: 2026-11-23 (UTC), **READ-ONLY**. Dokumentasi ini merekam keadaan aktual, bukan desain target produksi.

## 1. Arsitektur deployment saat ini

```
PC Windows / operator
   └─ git worktree + PR (PC → GitHub)
        ├─ /data/home/mcp-nusantara              (branch vps-stabilization)
        ├─ /data/home/mcp-nusantara-integration  (branch integration, dirty)
        └─ /data/workspace/nus-v1-integration-20261123/{worktrees,staging,backups}

Browser/UI (loopback)
   └─ vite 127.0.0.1:5180 / :5200
        └─ FastAPI 127.0.0.1:8000 / :8100  (proses user, bukan systemd)
             ├─ app/main.py → /health, /v1/health
             ├─ LanguageEngine → ProblemEngine → KnowledgeEngine (SQLite + RAG)
             ├─ OllamaProvider → 127.0.0.1:11434 (systemd, llama3.2:1b)
             └─ data/knowledge/nusantara_knowledge.db (+ chat-history, evidence)

Docker daemon (aktif, TIDAK ada container/image/volume yang dipakai)
   └─ docker-compose.yml (definisi saja): nusantara-api + postgres:16 + redis:7
```

Konfigurasi `ARCHITECTURE_CURRENT.md` menyatakan API `/v1` tanpa auth, orkestrasi/RAG/security bersifat PARTIAL, observability/storage MISSING.

## 2. Struktur direktori aktual

| Root | Isi penting |
|---|---|
| `/data/home/mcp-nusantara` | `app/`, `control-plane/`, `config/`, `data/`, `docs/`, `reports/`, `scripts/`, `tests/`, `.venv/`, `docker-compose*.yml`, salinan `mcp-nusantara/` (untracked) |
| `/data/home/mcp-nusantara-integration` | `backend/`, `frontend/`, `deploy/docker/`, `data/`, `config/`, `tests/`, `reports/`, `.venv/` |
| `/data/workspace/nus-v1-integration-20261123` | `baseline/`, `backups/`, `staging/{runtime-data,restore-test}/`, `worktrees/{baseline-b268,integration-work,rc-verify}/`, `evidence/`, `deliverables/`, `rc/`, `logs/`, `env/` |
| `/usr/share/ollama/.ollama/models` | Model `llama3.2:1b` (1,3 GB), di root disk |

Layout `backend/frontend/deploy/docker` tidak ada di worktree utama; pemetaan ini harus dipakai dalam dokumentasi rilis agar tidak salah arah.

## 3. Dependensi aplikasi

| Lapisan | Dependensi |
|---|---|
| Backend (`pyproject.toml`, `nusantara-ai 2.0.0a3`) | `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `pydantic>=2.9`, `pydantic-settings>=2.5`, `python-dotenv>=1.0`, `httpx>=0.27`, `haystack-ai==2.31.1` |
| Frontend / control-plane | React, React DOM, TanStack Router, TanStack Query, zod, `@xyflow/react`, Vite, TypeScript, Vitest, Playwright |
| Model | Ollama eksternal (`llama3.2:1b`); konfigurasi IndoBERT di `config/rag_runtime.json` tetapi cache model tidak ada |
| Data | SQLite; FTS5 + embedding di skema; tidak ada Postgres/Redis aktif |
| Infrastruktur | systemd hanya untuk Ollama, Docker daemon tanpa workload, SSH, Xvnc/Chromium untuk desktop |

## 4. Koneksi database

- env `NUSANTARA_KNOWLEDGE_DB` → default `data/knowledge/nusantara_knowledge.db` (`app/core/nusantara_config.py`, `app/knowledge/store.py`).
- env `NUSANTARA_DATA_DIR` → default `data`; dipakai control-plane, memory, MCP, dan developer-core.
- `config/rag_runtime.json`: `semantic_enabled: true`, `use_sqlite_fts5: true`, `use_embeddings: true`, `rerank: true`, grounding `allow_model_only_answer: false`.
- `config/local-services.json`: backend 8000, frontend 5180, Ollama 11434 mode `external`.
- compose menetapkan `NUSANTARA_DATA_DIR=/app/data`, `NUSANTARA_KNOWLEDGE_DB=/app/data/knowledge/nusantara_knowledge.db`, volume `apidata`.
- Tidak ada kredensial DB yang dibaca atau ditampilkan dalam audit ini.

## 5. Storage persisten

| Storage | Jenis | Catatan |
|---|---|---|
| `/` (16G ext4, `vda`) | Disk instabox | Berisi OS, `.venv` 480M, model Ollama 1,3G, source 908M |
| `/data` (20G ext4, `vdb`) | Disk instabox | Berisi worktree, data, backup, staging; survive stop |
| Docker named volumes | Tidak ada | `pgdata`, `apidata`, `apphome` hanya definisi |
| Swap | `/data/swapfile` 4G | File, bukan partisi |

Snapshots instabox dapat menyimpan kedua disk, tetapi tidak dapat diverifikasi tanpa API key.

## 6. Topologi jaringan

- Semua layanan aplikasi, Ollama, Vite, desktop (VNC 5901), dan Chrome debug (9222) terikat **loopback**.
- Port 22 terbuka untuk gateway instabox; `instabox-port list` → tidak ada published port.
- NAT/filter hanya aturan default Docker; tidak ada reverse proxy, TLS terminator, atau load balancer.
- Docker bridge belum dipakai (0 container).

## 7. Proses deployment

**Aktual:** perubahan masuk lewat git worktree/branch/PR; aplikasi dijalankan manual sebagai proses user; tidak ada systemd unit, tidak ada pipeline deploy otomatis, tidak ada health-gated promotion.

**Didefinisikan tetapi tidak aktif:** `docker compose` dengan image `nusantara-api` (build Dockerfile), `postgres:16-alpine`, `redis:7-alpine`; `docker-compose.audit.yml` menyediakan override port 8001 dan reset `env_file` untuk audit terisolasi.

**Dilarang oleh kontrak rilis:** direct folder overwrite, pengiriman DB/model/secret/persistent knowledge lewat source synchronization. Mekanisme yang harus dipakai: Git release untuk kode + prosedur migrasi/backup terpisah untuk data.

## 8. Kesenjangan arsitektur

| Kesenjangan | Dampak |
|---|---|
| Tidak ada reverse proxy/TLS/ingress | Tidak dapat menerima traffic produksi |
| Compose tidak pernah dijalankan | Volume dan jaringan produksi belum teruji |
| Proses aplikasi ad-hoc | Tidak ada restart policy, rollback, atau orkestrasi yang andal |
| Dua worktree source + satu salinan untracked | Provenance rilis ambigu |
| Observability MISSING | Tidak ada metrik/alert produksi |
| Data knowledge kosong, model IndoBERT tidak ada | Jalur RAG penuh belum terverifikasi |

Detail temuan dan blocker: `VPS_BASELINE_REPORT.md`, `VPS_BLOCKER_REGISTER.md`. Des staging: `VPS_STAGING_READINESS.md`.
