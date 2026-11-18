# SERVICE INVENTORY — Nusantara V1

Date: 2026-11-18
Branch: codex/fullroot-control-20261007

## 1. Backend API Service (FastAPI)

- Location: app/main.py, app/api/routes.py
- Entry point: uvicorn app.main:app --host 127.0.0.1 --port 8000
- Port: 8000 (HTTP)
- Protocol: REST/HTTP, JSON
- Status: ACTIVE
- Tests: test_backend_runtime_fixture.py, test_knowledge_pipeline.py

## 2. Frontend Control Plane (React/Vite)

- Location: control-plane/ (React/Vite)
- Entry point: npm run dev -- --port 5180
- Port: 5180 (HTTP)
- Protocol: HTTP, serves HTML/JS
- Status: ACTIVE
- Connects to: Backend API (port 8000)

## 3. Hermes Core (Agent)

- Location: app/hermes/agent.py
- Type: In-process module (not separate service)
- Entry: HermesAgent.execute_v1()
- Port: N/A (in-process)
- Status: ACTIVE (partial - LLM too small for grounded answers)
- Tests: test_hermes_v1_conversation, test_hermes_v1_context_preservation

## 4. Knowledge Engine / RAG

- Location: app/knowledge/engine.py, app/knowledge/rag.py
- Type: In-process module
- Entry: KnowledgeEngine.search_knowledge(), .ingest_document()
- Port: N/A (in-process)
- Status: ACTIVE
- Tests: test_knowledge_pipeline.py

## 5. LLM Provider (Ollama)

- Location: app/models/ollama_provider.py, app/models/ollama.py
- Type: External service
- Entry: OllamaProvider.generate()
- Port: 11434 (HTTP)
- Protocol: REST/HTTP
- Status: ACTIVE
- Models: gemma3n:e2b-it-q4_K_M (2B), tinyllama, llama3.2:1b

## 6. Database (SQLite)

- Location: data/knowledge/nusantara_knowledge.db
- Type: File-based database
- Entry: SQLiteVectorStore (app/knowledge/store.py)
- Port: N/A (file-based)
- Status: ACTIVE
- Tables: documents, chunks, knowledge_pipeline_runs, sop_review_*

## 7. Document Ingestion / Processing

- Location: app/knowledge/engine.py (process_knowledge_source)
- Type: In-process (via API)
- Entry: POST /v1/documents/ingest
- Port: N/A (via Backend API)
- Status: ACTIVE

## 8. SOP Management

- Location: app/knowledge/sop_review.py
- Type: In-process module
- Entry: SOPReview.decide(), .detail(), .content_ok()
- Port: N/A (via Backend API)
- Status: ACTIVE
- API: /v1/knowledge/pipeline/reviews/{document_id}

## 9. Evidence Registry

- Location: app/core/evidence_registry.py
- Type: In-process module
- Status: ACTIVE (partial)

## 10. Fullroot Control / Authorization

- Location: app/security/v1_knowledge.py (V1KnowledgeBoundary)
- Type: In-process module
- Entry: V1KnowledgeBoundary.search_knowledge(), .validate_response()
- Port: N/A (via Backend API)
- Status: ACTIVE

## 11. Human Approval

- Location: app/knowledge/sop_review.py (SOPReview)
- Type: In-process module
- Entry: SOPReview.decide(action='approve')
- Port: N/A (via Backend API)
- Status: ACTIVE

## 12. Monitoring / Health Check

- Location: app/api/runtime_readiness.py, app/api/runtime_verification.py
- Entry: GET /v1/health, GET /v1/runtime/readiness
- Port: N/A (via Backend API)
- Status: ACTIVE

## 13. Backup / Recovery

- Location: scripts/backup_nusantara.py
- Type: Standalone script
- Entry: python scripts/backup_nusantara.py
- Port: N/A
- Status: ACTIVE

## 14. IndoBERT Embedding Worker

- Location: nusantara-models/indobert_worker.py
- Type: Subprocess (spawned by IndoBERTClient)
- Entry: IndoBERTClient.encode()
- Port: N/A (stdin/stdout pipes)
- Status: ACTIVE (separate venv: .venv-docling)

## 15. Docling OCR Worker

- Location: .venv-docling (separate venv)
- Type: Subprocess
- Status: ACTIVE (used during document processing)

## Summary

Total services: 15
Active: 15
Partial: 3 (Hermes, Evidence Registry, Knowledge Engine)
Separate processes: 3 (Backend, Frontend, Ollama)
In-process modules: 12
