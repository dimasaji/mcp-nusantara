# PROJECT_BASELINE — NUSANTARA AI V1 (mcp-starter 0.1.0)

Phase 0 (Discovery). Hasil inspeksi statis kode; V1 tidak diubah pada tahap ini.

## Batas verifikasi (penting)
Sandbox audit tidak punya `fastapi`/`pydantic` dan tanpa jaringan, sehingga **`run_tests.py` V1 tidak dapat dijalankan** dan API V1 tidak diuji live.
Yang terverifikasi: struktur, isi kode, kompilasi, dan modul stdlib-only (policy, trust, memory). Klaim "phase 1–18 Implemented" di `docs/phase-status.md` belum saya reproduksi.

## Ringkasan
- ~8.500 baris Python di `app/` (FastAPI, Pydantic v2), 21 modul: api, context, core, handoff, hermes, knowledge, language, mcp, memory, models, policy, problem, reasoning, tools, trust, workflow, ui.
- Entry point: `app/main.py` (`/health`, `/`, `/ui`, router `/v1`).
- Model: Ollama lokal (`llama3.2:1b`), provider OpenAI-compatible & Mock tersedia. Vector store = memory; embedding = `local-hash`.

## Alur runtime `/v1/chat`
input → `LanguageEngine` → `ProblemEngine` → `KnowledgeEngine.search` → `OllamaProvider.generate` → respons.
Fallback teks jika Ollama offline.

## Temuan utama
1. **Policy, Trust, Memory, MCP, Handoff, Reasoning tidak dipanggil oleh `/v1/chat`.** Modul ada, tetapi tidak berada di jalur eksekusi.
2. `/v1/health/detail` menulis semua komponen `"available"` secara statis; `/v1/metrics` mengembalikan `requests_total: 0` konstan.
3. Tidak ada autentikasi/otorisasi di API. CORS dibatasi ke localhost (bukan pengganti auth).
4. `LongTermMemory` memakai `pickle` (eksekusi kode saat load bila file dimanipulasi) dan nama file dari key mentah (path traversal). **Diperbaiki di V2.**
5. `HandoffEngine()` dibuat baru per request → handoff kemungkinan tidak tersimpan (perlu diverifikasi saat runtime).
6. State (knowledge, workflow, session) hanya di memori proses; hilang saat restart.
7. Kemungkinan duplikasi (belum dibandingkan isinya): `models/mock.py` vs `mock_provider.py`, `ollama.py` vs `ollama_provider.py`, `workflow/schemas.py` vs `workflow_schema.py`, `problem/schemas.py` vs `problem_schema.py`. Ada file sisa `*.tmp` (dipindah ke `legacy_v1_artifacts/`).
8. `PolicyRule.evaluate` punya `return` ganda (kode mati) — diperbaiki di V2.
9. 46 pemakaian `datetime.utcnow()` (deprecated).
10. Tes: hanya `tests/evaluation/` berisi file; 9 folder tes lain kosong. `fail_under = 80` coverage tidak realistis saat ini.
11. Dokumen menyebut `Makefile` dan `.gitignore`, tetapi keduanya tidak ada di zip (V2 menambah `.gitignore`).
12. `__pycache__` Python 3.13 ikut ter-zip.
