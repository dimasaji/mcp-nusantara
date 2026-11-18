# SERVICE PORTS — Nusantara V1

Date: 2026-11-18

| Service | Port | Protocol | Status |
|---|---|---|---|
| Backend (FastAPI) | 8000 | HTTP/REST | ACTIVE |
| Frontend (Vite) | 5180 | HTTP | ACTIVE |
| Ollama (LLM) | 11434 | HTTP/REST | ACTIVE |
| IndoBERT Worker | N/A | stdin/stdout | ACTIVE (subprocess) |
| Docling OCR | N/A | subprocess | ACTIVE (subprocess) |

## Port Conflicts

None detected. All ports are distinct.

## External Dependencies

- Ollama must be running before Backend
- Backend must be running before Frontend
- IndoBERT worker spawned on demand
