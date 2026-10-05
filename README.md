# Nusantara Core + Hermes — Local Starter

Local-first AI Core Engine + Hermes Agent/Orchestrator. Arsitektur mengikuti blueprint 18 fase yang diberikan: LLM hanyalah salah satu komponen; tool, policy, trust, workflow, knowledge dan human handoff tetap memiliki interface sendiri.

## Jalankan di Windows / PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python run_tests.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Buka: `http://127.0.0.1:8000/` atau `http://127.0.0.1:8000/ui`

API docs: `http://127.0.0.1:8000/docs`

Endpoint `POST /v2/dev` dan `POST /v1/documents/ingest` membutuhkan
`NUSANTARA_ADMIN_TOKEN` di environment server dan header `X-Admin-Token`
yang cocok. Gunakan nilai acak yang kuat; tanpa konfigurasi token, akses ditolak.
Jangan menyimpan token di source atau dokumentasi.

Konten ingest teks adalah teks literal, termasuk string yang menyerupai path.
Parser tidak membuka file lokal secara implisit. Untuk pemrosesan PDF/DOCX offline,
pemanggil tepercaya harus membaca file yang sudah diotorisasi menjadi bytes dahulu;
path dari pengguna tidak boleh diteruskan sebagai konten parser.

## Ollama lokal

Pastikan Ollama berjalan, lalu pull model yang dipakai `.env` (default `llama3.2:1b`):

```powershell
ollama serve
ollama pull llama3.2:1b
```

Konfigurasi opsional `.env`:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://127.0.0.1:11434
LLM_MODEL=llama3.2:1b
```

Tanpa Ollama, dashboard/API tetap hidup dan menampilkan status `Ollama OFFLINE`; fitur LLM akan aktif setelah Ollama tersedia.

## Docker

```bash
docker compose up --build
```

API Docker dipublikasikan hanya pada loopback host. Volume `apidata` menyimpan
SQLite, audit, dan cache model IndoBERT di `/app/data`; root container tetap read-only.
Image menyiapkan environment IndoBERT CPU terpisah. Build membutuhkan unduhan
dependensi; penggunaan embedding pertama membutuhkan unduhan model jika cache kosong.
Ollama harus dapat dijangkau dari container melalui `LLM_BASE_URL` yang sesuai,
misalnya `http://host.docker.internal:11434` pada Docker Desktop.

Interpreter dan worker IndoBERT dapat diatur melalui `NUSANTARA_INDOBERT_PYTHON`
dan `NUSANTARA_INDOBERT_WORKER`. Image mengatur keduanya ke lokasi Linux;
instalasi Windows lokal tetap memakai environment `nusantara-models/.venv`.

Validasi runtime lokal yang terisolasi:

```powershell
python scripts/verify_audit_runtime.py
```

Pemeriksaan ini menggunakan database sementara, model IndoBERT yang sudah dicache,
dan Ollama sesuai konfigurasi server. Hasil disimpan dalam
`audit_reports/AUDIT_RUNTIME_READINESS_2026-10-05.json`. Status tetap `CONDITIONAL`
sampai deployment Docker diuji; keberhasilan runtime Windows tidak membuktikan
image Linux berhasil dibangun.

## Verifikasi

`python run_tests.py` adalah smoke/phase verification. `pytest` menjalankan test suite. Lulus test tidak berarti production-ready; audit blueprint juga mensyaratkan pengujian keamanan, performa, model, RAG dan handoff nyata.
