# VPS Runtime Acceptance Report

Tanggal: 2026-11-23
Executor: OpenCode VPS Instabox
Target commit: PR #16 head `58f07307db283c08fc7e956c28906c1ba9bffdda`
Mode: non-disruptif; tidak ada restart, deploy, perubahan DB, atau perubahan data

## Proses dan Port Aktif

| Port | PID | Proses | CWD | Hasil probe |
|---|---:|---|---|---|
| 8000 | 28141 | `.venv/bin/python -m uvicorn app.main:app` | `/data/home/mcp-nusantara` | `/health` 200 |
| 8100 | 346443 | `uvicorn app.main:app` | `/data/home/mcp-nusantara` | `/health` 200 |
| 5173 | 28365 | `node .../vite --host 127.0.0.1` | `/data/home/mcp-nusantara/control-plane (deleted)` | `/` 404 |
| 5200 | 347016 | `node .../vite --port 5200 --strictPort` | `/data/home/mcp-nusantara/control-plane (deleted)` | `/` 404 |
| 11434 | — | `ollama serve` | — | version `0.40.17`, model `llama3.2:1b` |

`config/local-services.json` masih menyebut `frontendPort: 5180`; port yang benar-benar listening adalah 5173 dan 5200, keduanya 404.

## Identitas Build — Temuan Kritis

Source build id dihitung dengan algoritma `app/core/runtime_identity.py::source_build_id` terhadap tree commit yang di-archive.

| Sumber | Build ID | Layout |
|---|---|---|
| Proses 8000 (`/health`) | `sha256:5b3750b8fa12b6baf91916b6e7ff7e1613aac4dccb156b374209c80cadb3877e` | commit `ddc54a2b`, root `app/` |
| Proses 8100 (`/health`) | `sha256:d5bdf8fd49a0b4d8e4579919901c6c62d6f7aeb4d7821eed097bcea30fabdbc0` | commit `e9786bb8` / `87a58034` / `5ebe32b3`, root `app/` |
| Base PR #16 `b268da1e` | `sha256:ceb32445b560a8d05856918f80d76a130ef8a73b2208d95a023f320979eed78b` | `backend/app/` |
| Head PR #16 `58f07307` | `sha256:ec290f5356965f5c64724e6dfdfbaff135485a797f9006c75d099b2433581e14` | `backend/app/` |

**Kedua backend aktif TIDAK menjalankan PR #16 atau base-nya.** Keduanya meng-import `app/` legacy di root repo (direktori ignored, ~2.5 MB, tidak terlacak di Git), bukan `backend/app/` kanonik. Tidak ada `PYTHONPATH=backend` pada PID 28141/346443.

## Backend FastAPI

| Endpoint | 8000 | 8100 |
|---|---:|---:|
| `/health` | 200 | 200 |
| `/docs` | 200 | 200 |
| `/openapi.json` | 200 | 200 |
| `/v1/health` | 200 | 200 |
| `/v1/health/detail` | 200 | 200 |
| `/v1/health/ready` | 404 (tidak didefinisikan) | 404 |
| `/v1/control-plane/model-status` | 200 | 200 |

`/v1/health/detail` melaporkan `status: ok`, provider `ollama`, model `llama3.2:1b`, namun `verification_state: NOT_VERIFIED`, build `verification_state: SOURCE_SNAPSHOT`, dan `confirmation_source: MODEL_INVENTORY_ONLY`. Model source: `DEFAULT` di 8000, `ENV` di 8100 (`LLM_PROVIDER=ollama`, `LLM_MODEL=llama3.2:1b` hanya di PID 346443).

## Frontend Vite/React

- Kedua proses Vite masih hidup tetapi CWD-nya sudah `(deleted)` akibat cleanup `control-plane/` yang disetujui sebelumnya.
- `GET /`, `/index.html`, `/@vite/client`, `/src/main.tsx`, dan `/favicon.ico` semuanya 404 di port 5173 maupun 5200.
- Ini adalah dampak runtime nyata dari cleanup; tidak ada restart atau restore yang dilakukan.

## LLM, Provider, Database, Environment

- Ollama 11434 aktif, versi `0.40.17`; `/api/tags` hanya berisi `llama3.2:1b`.
- Tidak ada `OPENROUTER_API_KEY`, tidak ada variabel `NUSANTARA_*` lain di environment; hanya `.env.example` yang ada.
- `config/rag_runtime.json` mengharuskan embedding `indobenchmark/indobert-base-p1` dengan retrieval SQLite FTS5 + embeddings; file/model tersebut tidak ditemukan.
- `data/knowledge/nusantara_knowledge.db` (94.208 byte): 9 tabel; `documents=0`, `chunks=0`, `document_extractions=0`, semua tabel review 0; `user_version=0`, `journal_mode=wal`.
- Tidak ditemukan script migrasi (`alembic.ini`, `*migrat*`, `*.sql`).
- Tidak ada perubahan DB/data yang dilakukan.

## Chat Endpoint

- `POST /v1/chat` dengan body `{}` → `422` (`user_input required`) di 8000 dan 8100; route hidup dan validasi aktif.
- `GET /v1/chat/history?session_id=probe` → `403 CHAT_SESSION_CAPABILITY_REQUIRED`.
- Generasi chat penuh tidak dijalankan: kredensial/admin capability tidak tersedia dan akan mengubah/berpotensi memakai model serta data operasional.

## Verdict

**RUNTIME ACCEPTANCE: BLOCKED / NO-GO.**

Backend legacy sehat secara HTTP, tetapi proses yang diuji bukan commit PR #16 dan frontend dalam keadaan 404. Tidak boleh diklaim bahwa PR #16 sudah terverifikasi di runtime sampai backend di-rebind ke `backend/app` pada commit PR #16 dan frontend disajikan dari `frontend/` yang kanonik, dengan approval terpisah.
