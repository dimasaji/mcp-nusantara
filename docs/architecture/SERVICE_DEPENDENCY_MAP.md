# SERVICE DEPENDENCY MAP — Nusantara V1

Date: 2026-11-18

## Dependency Graph

Frontend → Backend API (HTTP/REST)
Backend API → Hermes Core (in-process)
Backend API → Knowledge Engine (in-process)
Backend API → V1KnowledgeBoundary (in-process)
Hermes Core → Knowledge Engine (search)
Hermes Core → LLM Provider (Ollama HTTP)
Knowledge Engine → RAG (in-process)
Knowledge Engine → SQLite DB (file)
RAG → IndoBERT Worker (subprocess)
RAG → SQLite Vector Store (file)
SOP Review → Knowledge Engine (in-process)
SOP Review → SQLite (pipeline runs)
Evidence Registry → SQLite (file)
Fullroot Control → SOP Review (in-process)
LLM Provider → Ollama (HTTP:11434)
IndoBERT Worker → .venv-docling (subprocess)
Docling OCR → .venv-docling (subprocess)

## No Circular Dependencies

Verified: no circular imports between modules.

## Startup Order

1. Ollama (port 11434) — external, must be running
2. Backend (port 8000) — depends on Ollama, SQLite
3. Frontend (port 5180) — depends on Backend
4. IndoBERT Worker — spawned on demand by RAG

## Ports

| Service | Port | Protocol |
|---|---|---|
| Backend | 8000 | HTTP |
| Frontend | 5180 | HTTP |
| Ollama | 11434 | HTTP |
