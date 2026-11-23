# VPS Runtime Verification — Stabilization V1

- Tanggal verifikasi: 2026-11-23.
- Environment: sandbox Linux, repo `/data/home/mcp-nusantara`, Python 3.13.5 (`.venv`), Node 22.23.3, npm 10.9.9.
- Branch: `codex/vps-stabilization-20261123`.
- Commit sumber terverifikasi: `4bdd387bd6b1101ca30a2fc047a93ffd0361efb8`.
- Baseline: `87a58034b8f9898850dc5a290b3f706552de0ea0` dari kontrak `NUS-V1-OLLAMA-RUNTIME-003`.

## Perintah yang dijalankan

- `git status --short`, `git branch -vv`, `git log -5 --oneline`, `git remote -v`, `git fetch origin`.
- Struktur: pengujian direktori `backend/`, `frontend/`, `deploy/docker/`, `tests/`, `docs/`, `reports/`, `app/`, `control-plane/`.
- Python: `.venv/bin/python -c "import app.main; print('IMPORT_OK')"`, `.venv/bin/pip check`.
- Runtime: `ps -p 346443 -o pid=,args=`, `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8100/health`, `curl -sS http://127.0.0.1:8100/v1/health/detail`.
- Frontend: `npm run build` di `/data/home/mcp-nusantara/control-plane`.
- Database: `sqlite3 data/knowledge/nusantara_knowledge.db "select count(*) from sqlite_master where type='table';"` dan query `documents`/`chunks`.
- Konfigurasi: `sed`/`grep` pada `app/main.py`, `config/local-services.json`, `control-plane/vite.config.ts`.

## Hasil aktual

- `backend/`, `frontend/`, `deploy/docker/`: ABSENT. Struktur aktif adalah `app/`, `control-plane/`, `tests/`, `docs/`, `reports/`.
- Import `app.main`: `IMPORT_OK`; `pip check`: `No broken requirements found`, exit `0`.
- Backend berjalan dengan `uvicorn app.main:app --host 127.0.0.1 --port 8100`, PID `346443`.
- `GET /health`: HTTP `200`; `GET /v1/health/detail`: HTTP `200`, provider `ollama`, model `llama3.2:1b`.
- Env backend aktif: `LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://127.0.0.1:11434`, `LLM_MODEL=llama3.2:1b`, `LLM_CONTEXT_TOKENS=2048`.
- Config shell tanpa override: `ollama http://localhost:11434 llama3.2:1b 4096`; perbedaan `2048` vs `4096` tercatat sebagai konfigurasi proses aktif, bukan kegagalan runtime.
- `npm run build`: PASS, `446 modules transformed`, `built in 2.30s`, exit `0`.
- DB `data/knowledge/nusantara_knowledge.db`: `tables=9`, `documents=0`, `chunks=0`.
- Endpoint `/v1/knowledge/pipeline/status` dan `/v1/runtime/readiness`: HTTP `403 {"detail":"admin token diperlukan"}`.
- Tidak ada referensi path lama yang menggagalkan startup; CORS mengizinkan origin `http://localhost:3000`, `http://127.0.0.1:8765`, `http://localhost:5180`.
- Port aktif teramati: `5180` (frontend dev), `5200` (frontend alternatif), `8000` (backend default), `8100` (backend aktif), `11434` (Ollama).

## Status bukti

- **PASS** — Lingkungan VPS dapat menjalankan backend, frontend build, Ollama, dan konfigurasi aktif tanpa import/dependency error yang baru.
- **PARTIAL** — Struktur yang diminta tidak persis `backend/frontend/deploy/docker`; pemetaan ke struktur aktif diperlukan agar audit tidak menghasilkan temuan menyesatkan.
- **BLOCKED** — Knowledge pipeline dan readiness tidak dapat diverifikasi lewat endpoint tanpa admin token; verifikasi DB langsung tetap menunjukkan DB kosong.

## Root cause dan corrective action

- Root cause temuan struktur: kontrak menuliskan layout generik, sedangkan repo V1 memakai `app/` dan `control-plane/`.
- Tindakan: gunakan pemetaan struktur aktif pada laporan ini; jangan lakukan bulk folder move dalam cakupan V1.
- Root cause 403 knowledge endpoint: autentikasi admin belum tersedia di sesi verifikasi.
- Tindakan: verifikasi DB langsung dipakai sebagai bukti batas, bukan klaim E2E.

## Pekerjaan tersisa

- Jika diperlukan, sediakan admin token untuk mengulang `/v1/knowledge/pipeline/status` dan `/v1/runtime/readiness`.
- Jangan nyatakan production-ready sampai knowledge E2E dan regression suite utama hijau.

## Bukti

- `/data/tmp/opencode/stab_phase_a.txt`
- `/data/tmp/opencode/stab_phase_b_structure.txt`
- `/data/tmp/opencode/stab_phase_b_runtime.txt`
- `/data/tmp/opencode/stab_phase_b_database.txt`
- `/data/tmp/opencode/stab_frontend_build.txt`
