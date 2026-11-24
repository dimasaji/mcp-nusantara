# POST_RESTRUCTURE_RUNTIME_REPORT

Date: 2026-11-23
Branch: codex/fullroot-control-20261007
Environment: Windows 11, Python 3.13.15, .venv

## Import verification
- `PYTHONPATH=backend` → `import app.main`, `app.knowledge.engine`, `app.core.nusantara_config` → OK.

## Backend startup
- Command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` (PYTHONPATH=backend)
- Result: PASS. Health endpoint `GET /health` → `{"status":"ok","version":"0.1.0","build_id":"sha256:99dd..."}`.

## Ollama
- LLM_PROVIDER=ollama, LLM_MODEL=gemma3n:e2b-it-q4_K_M, LLM_BASE_URL=http://127.0.0.1:11434
- Reachable: YES (200, model present).

## Frontend build
- `cd frontend; npm run build` → tsc --noEmit PASS (no type errors).
- `vite build` → FAILED: esbuild temp file access denied (Windows permission/antivirus). BLOCKED (environment, not code).
- Pre-built `frontend/dist` is empty.

## Database
- `data/knowledge/nusantara_knowledge.db` exists (52.75 MB). integrity_check = ok (verified in BACKUP_VERIFICATION_REPORT).

## Knowledge/RAG
- search_knowledge, process_knowledge_source paths functional (import OK).
- cv2 installed in .venv (5.0.0); docling layout tests 4 passed.

## Verdict for runtime
- Backend: PASS
- Frontend build: BLOCKED (environment)
- Ollama: PASS
- DB: PASS
- RAG import: PASS
