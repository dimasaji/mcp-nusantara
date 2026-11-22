# Repository Runtime Report

Tanggal observasi: 2026-11-22  
Repository: `/data/home/mcp-nusantara`  
Branch: `codex/fullroot-control-20261007`

## Status singkat

`LOCAL SHELL RUNS` — backend FastAPI dan frontend Vite keduanya merespons di `127.0.0.1`.  
`FULL RUNTIME NOT VERIFIED` — ingest/search pengetahuan dan chat berbasis LLM masih terblokir oleh prerequisite yang tidak ada di checkout.

Semua permintaan uji memakai data sintetis. Token admin untuk endpoint lokal di-set sebagai nilai sintetis melalui environment; nilai tidak dicetak atau disimpan dalam laporan.

## Cara layanan dijalankan

Backend:

```sh
export NUSANTARA_ADMIN_TOKEN=<nilai-sintetis-lokal>
export HAYSTACK_TELEMETRY_ENABLED=False
nohup .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >/tmp/nusantara-backend.log 2>&1 &
```

Frontend:

```sh
cd control-plane
nohup npm run dev >/tmp/nusantara-frontend.log 2>&1 &
```

Proses yang teramati:

| Proses | PID | Alamat |
| --- | --- | --- |
| uvicorn backend | `28141` | `127.0.0.1:8000` |
| shell `npm run dev` | `28352` | — |
| node Vite | `28365` | `127.0.0.1:5180` |

## Bukti respons

| Permintaan | Hasil |
| --- | --- |
| `GET http://127.0.0.1:8000/health` | `200`; body `{"status":"ok","version":"0.1.0","build_id":"sha256:5b3750b8fa12b6baf91916b6e7ff7e1613aac4dccb156b374209c80cadb3877e"}` |
| `GET http://127.0.0.1:8000/` | `307`, `redirect=http://127.0.0.1:5180/` |
| `GET http://127.0.0.1:8000/v1/health/detail` | `200` |
| `GET http://127.0.0.1:5180/` | `200` |
| `GET http://127.0.0.1:5180/health` | `200` — proxy Vite → backend `:8000` terbukti merespons |

Log frontend menunjukkan `VITE v7.3.7 ready in 122 ms`. Log backend menunjukkan startup uvicorn berhasil tanpa exception saat boot.

## Entrypoint dan konfigurasi yang dipakai

- Backend: `app/main.py`, FastAPI dengan mode `NORMAL` / `ATTESTATION` / `READ_ONLY`.
- Settings: `app/core/config.py` (bukan `app/config.py`).
- Frontend: `control-plane/`, Vite dev server `:5180`, proxy ke backend `:8000` sesuai `control-plane/vite.config.ts`.
- DB pengetahuan yang dikonfigurasi: `data/knowledge/nusantara_knowledge.db` — file tidak ada di checkout saat observasi.
- Provider LLM default: Ollama, `http://localhost:11434`, model `llama3.2:1b` sesuai konfigurasi bawaan; Ollama tidak berjalan saat observasi.
- `config/local-services.json`: `host=127.0.0.1`, `backendPort=8000`, `frontendPort=5180`, `ollamaPort=11434`, `ollamaMode=external`.

## Kegagalan runtime fungsional dengan data sintetis

| Aksi | Hasil | Penyebab terbukti |
| --- | --- | --- |
| `POST /v1/documents/ingest` | `400` | `[Errno 2] No such file or directory: '/data/home/mcp-nusantara/nusantara-models/.venv/bin/python'` |
| `POST /v1/knowledge/search` | `500` | Detail publik `Terjadi kesalahan internal layanan. Coba lagi atau hubungi operator.`; traceback melalui `app/knowledge/indobert_embedding.py:42` → `app/language/semantic/indobert_client.py:107 encode` → `start()` di baris `59` (`subprocess.Popen`) gagal karena python/worker IndoBERT tidak ada |
| `POST /v1/chat` tanpa Ollama | `503` | `PROVIDER_UNAVAILABLE` |

`Dockerfile:18` merujuk `nusantara-models/indobert_worker.py`, tetapi direktori/file tersebut tidak ada di checkout dan tidak ter-track git. Worker tidak dibuat-buat atau diganti tanpa persetujuan desain.

## Kesimpulan runtime

- PASS: boot backend, root redirect, health backend, health detail, boot frontend, proxy frontend → backend, eksposur loopback-only.
- FAIL/BLOCKED: ingest dokumen SOP, pencarian pengetahuan ber-embedding, dan chat LLM nyata.
- Karena itu status runtime keseluruhan adalah `NOT READY`, meskipun shell layanan berjalan.

Bukti log: `/tmp/nusantara-backend.log`, `/tmp/nusantara-frontend.log`.
