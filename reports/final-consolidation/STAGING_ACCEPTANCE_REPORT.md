# Staging Acceptance Report — Nusantara V1

Tanggal: 2026-11-23
Fase: Phase B — Isolated Linux Staging
Status Gate B: **PASS**

## Sumber yang diuji

| Item | Nilai |
|---|---|
| RC SHA | `6f037ab491d0ae2793db69d380b0d3e82ec88872` |
| Worktree | `/data/workspace/nus-v1-staging-6f037ab4/repo` |
| HEAD worktree | `6f037ab4` detached |
| Python env | `/data/workspace/nus-v1-staging-6f037ab4/env/bin/python` |
| Frontend deps | `npm ci --offline --no-audit --no-fund`, 198 packages |
| Vite | `7.3.7` |
| Backend port | `18100` |
| Frontend port | `15173` |
| Ollama | external `127.0.0.1:11434`, version `0.40.17`, model `llama3.2:1b` |
| Staging DB | `/data/workspace/nus-v1-staging-6f037ab4/runtime/staging-db/nusantara_knowledge.db` |
| Production DB/data | tidak dipakai, tidak disalin, tidak dimodifikasi |

Port produksi/lama `8000`, `8100`, `5173`, dan `5200` tidak disentuh.

## Build identity

Semua respons backend yang relevan dan proxy frontend melaporkan build ID yang sama:

`sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b4754f87478480331`

Build identity ini berasal dari source SHA yang sama, yaitu RC `6f037ab4`.

## Proses

| Proses | PID | CWD | Perintah |
|---|---:|---|---|
| Backend | `461803` | `/data/workspace/nus-v1-staging-6f037ab4/repo/backend` | `env/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 18100 --log-level info` |
| Frontend npm wrapper | `461811` | `/data/workspace/nus-v1-staging-6f037ab4/repo/frontend` | `npm run dev -- --port 15173` |
| Frontend Vite shell | `461823` | `/data/workspace/nus-v1-staging-6f037ab4/repo/frontend` | `sh -c vite --host 127.0.0.1 --port 15173` |

Log:

- `/data/workspace/nus-v1-staging-6f037ab4/runtime/backend/uvicorn.log`
- `/data/workspace/nus-v1-staging-6f037ab4/runtime/frontend/vite.log`

## Deteksi legacy path

| Pemeriksaan | Hasil |
|---|---|
| `/proc/461803/cwd` | staging `repo/backend` |
| `/proc/461811/cwd` | staging `repo/frontend` |
| `app.main.__file__` | `/data/workspace/nus-v1-staging-6f037ab4/repo/backend/app/main.py` |
| legacy `/app` imports | tidak ada |
| source build ID | sama di `/health`, `/v1/health`, `/v1/health/detail`, dan frontend proxy |

Tidak ada indikasi proses staging memakai CWD lama, `app/` legacy, atau service port `8000`/`8100`.

## Endpoint checks

| Endpoint | Hasil |
|---|---|
| `GET http://127.0.0.1:18100/health` | 200 |
| `GET /docs` | 200 |
| `GET /openapi.json` | 200 |
| `GET /v1/health` | 200 |
| `GET /v1/health/detail` | 200, provider `ollama`, model `llama3.2:1b`, available `true` |
| `GET /v1/control-plane/model-status` sebelum chat | 200, `NOT_VERIFIED` |
| `GET http://127.0.0.1:15173/` | 200 |
| `GET http://127.0.0.1:15173/health` | 200, build ID identik |
| `GET http://127.0.0.1:11434/api/version` | 200, `0.40.17` |
| `GET /api/tags` | 200, `llama3.2:1b` tersedia |

## Model chat PASS

Dua permintaan chat nyata dijalankan dari RC yang sama:

1. Direct backend `POST http://127.0.0.1:18100/v1/chat`.
2. Frontend proxy `POST http://127.0.0.1:15173/v1/chat`.

Keduanya:

- status `200`;
- `response: "PONG"`;
- `model: "llama3.2:1b"`;
- `provider_status: "ollama"`;
- build ID sumber sama;
- tidak memakai mock provider.

Setelah chat, `/v1/control-plane/model-status` berubah menjadi:

- `availability: INFERENCE_OBSERVED`;
- `status: INFERENCE_VERIFIED`;
- `verified_at` terisi;
- `last_request.model: llama3.2:1b`;
- `last_request.provider_status: ollama`.

Riwayat chat dengan header `x-chat-session` yang valid juga mengembalikan 200 dan menampilkan turn yang sama.

Batas penting: chat ini adalah verifikasi model generatif, bukan SOP official knowledge E2E. Respons memiliki `grounding.grounded: false`, `evidence_count: 0`, dan `trust.supports_claim: false`.

## Gate B

| Kriteria | Hasil |
|---|---|
| Backend health PASS | PASS |
| Frontend PASS | PASS |
| Model chat PASS dari SHA yang sama | PASS |

**Gate B: PASS**
