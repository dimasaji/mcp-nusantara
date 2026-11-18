# SERVICE LIFECYCLE — Nusantara V1

Date: 2026-11-18

## Startup Order

1. Ollama (port 11434) — external, must be running
2. Backend (port 8000) — depends on Ollama, SQLite
3. Frontend (port 5180) — depends on Backend
4. IndoBERT Worker — spawned on demand by RAG

## Startup Commands

### Windows
- start-nusantara.bat — starts all services
- stop-nusantara.bat — stops all services
- status-nusantara.bat — shows service status
- doctor-nusantara.bat — runs health checks

### Manual
- Backend: .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
- Frontend: cd control-plane && npm run dev -- --port 5180
- Ollama: ollama serve

## Health Checks

- Backend: GET http://127.0.0.1:8000/v1/health
- Ollama: GET http://127.0.0.1:11434/api/tags
- Frontend: GET http://127.0.0.1:5180

## Shutdown

1. Stop Frontend (Ctrl+C)
2. Stop Backend (Ctrl+C)
3. Ollama can remain running

## Recovery

- Database: SQLite (file-based, no recovery needed)
- Knowledge: re-ingest documents if needed
- Backup: scripts/backup_nusantara.py
