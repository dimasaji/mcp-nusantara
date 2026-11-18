# SERVICE ARCHITECTURE — Nusantara V1

Date: 2026-11-18

## 1. Architecture Pattern

Modular Monolith (Backend) + SPA (Frontend) + External LLM (Ollama)

## 2. Component Diagram

Browser → Frontend (React/Vite:5180) → Backend API (FastAPI:8000) → Hermes Core → Knowledge Engine/RAG → SQLite DB
                                                                                          ↓
                                                                                     LLM Provider (Ollama:11434)

## 3. Backend Services (In-Process Modules)

- API Layer: app/api/routes.py, app/api/knowledge_pipeline.py
- Hermes Core: app/hermes/agent.py
- Knowledge Engine: app/knowledge/engine.py, app/knowledge/rag.py
- Security: app/security/v1_knowledge.py, app/security/auth.py
- SOP Management: app/knowledge/sop_review.py
- Evidence Registry: app/core/evidence_registry.py
- Fullroot Control: app/security/v1_knowledge.py
- LLM Provider: app/models/ollama_provider.py

## 4. External Services

- Ollama (LLM): port 11434
- IndoBERT Worker: subprocess (.venv-docling)
- Docling OCR: subprocess (.venv-docling)

## 5. Data Flow

1. User sends message via Frontend
2. Frontend → Backend API (POST /v1/chat)
3. Backend → HermesAgent.execute_v1()
4. Hermes → KnowledgeEngine.search_knowledge() (if needed)
5. KnowledgeEngine → RAG.query() → SQLite search
6. Hermes → OllamaProvider.generate() (if needed)
7. Response → Frontend → Browser

## 6. Security Boundaries

- Admin token required for all API calls
- V1KnowledgeBoundary gates pilot documents
- Rate limiting: 30 req/60s per session
- Response projection clears source text from public API

## 7. Status

- All services: ACTIVE
- Hermes: PARTIAL (LLM too small for grounded answers)
- Knowledge Engine: ACTIVE
- RAG: ACTIVE (Recall@5=0.8278)
