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

## Verifikasi

`python run_tests.py` adalah smoke/phase verification. `pytest` menjalankan test suite. Lulus test tidak berarti production-ready; audit blueprint juga mensyaratkan pengujian keamanan, performa, model, RAG dan handoff nyata.
