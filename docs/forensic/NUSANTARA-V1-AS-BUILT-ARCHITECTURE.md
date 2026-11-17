# NUSANTARA V1 AS-BUILT ARCHITECTURE

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17

---

## 1. System Overview

Nusantara V1 is a local AI knowledge system for SOP documents. It consists of:
- FastAPI backend (port 8000)
- React/Vite frontend (port 5180)
- Ollama LLM (port 11434)
- IndoBERT embeddings (768D via worker process)
- Docling OCR (via .venv-docling)
- SQLite vector store (55.3 MB, 64 documents)

## 2. Architecture

```
User → Frontend (5180) → Backend API (8000) → Hermes → Knowledge Engine → RAG (SQLite) → Ollama (11434)
```

### Backend (app/main.py)
- FastAPI + Uvicorn
- Composes KnowledgeEngine, HermesAgent, LanguageEngine, etc.
- CORS enabled for frontend

### Knowledge Engine (app/knowledge/engine.py)
- Facade over RAG
- Search with hybrid scoring (semantic + lexical)
- Document-level grouping
- Title boost + contentless filter
- Citation page assignment

### RAG (app/knowledge/rag.py)
- SQLiteVectorStore (721 chunks)
- IndoBERT embedding (768D)
- Hybrid retrieval (0.50 semantic + 0.50 lexical)
- Relevance gate (min_score=0.35, relative=0.65)

### Hermes (app/hermes/agent.py)
- Chat orchestration
- Evidence retrieval, generation, grounding
- Evidence fast path for requirements
- Abstention handling

### Grounding Guard (app/knowledge/grounding.py)
- Token subset check
- Sentence validation
- Requirement/procedure/numeric checks
- Fail-closed on exception

### SOP Review (app/knowledge/sop_review.py)
- Version-bound operator decisions
- Content OK, metadata, approval
- is_pilot() gating
- Audit trail (events, trials, sessions)

## 3. Database

- Engine: SQLite
- Path: data/knowledge/nusantara_knowledge.db
- Size: 55.3 MB
- Tables: 9 (documents, chunks, pipeline_runs, etc.)
- Source documents: 60 files, 54.6 MB

## 4. Models

- LLM: gemma3n:e2b-it-q4_K_M (2B, 7.8 GB) via Ollama
- Embedding: indobenchmark/indobert-base-p1 (768D)
- OCR: Tesseract (ind+eng, PSM 6)

## 5. Feature Flags

- NUS_LANGCHAIN_ENABLED: false
- NUS_LANGGRAPH_ENABLED: false
- NUS_OPENROUTER_ENABLED: not set

## 6. Known Issues

1. Chat abstains (LLM too small for grounded answers)
2. Precision@5 below target (metric limitation)
3. OCR ground truth not available
4. 5 test failures (environment)
5. LangGraph SOP workflow has stub nodes (partially fixed)
6. No 7B+ model available (can't download)
