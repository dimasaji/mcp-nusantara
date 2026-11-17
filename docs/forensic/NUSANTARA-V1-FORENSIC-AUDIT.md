# NUSANTARA V1 FORENSIC AUDIT

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17
**Repository:** C:\Users\dmaza\mcp-starter
**Branch:** codex/fullroot-control-20261007
**HEAD:** d101fc4a

---

## 1. Repository Inventory

- **Total tracked files:** 1675
- **Python files:** 10602 (includes .venv)
- **Test files:** 161
- **App modules:** 34 (action, api, approval, context, core, devcore, developer_core, evaluation, execution, experience, governance, handoff, hermes, improvement, knowledge, language, mcp, memory, models, observability, orchestration, policy, problem, rag, reasoning, research, runtime, security, skills, tools, trust, ui, v2, workflow)
- **Database:** SQLite, 55.3 MB, 9 tables
- **Source documents:** 60 files, 54.6 MB

## 2. Architecture Map

### Entry Points
- **Backend:** app/main.py → FastAPI + Uvicorn (port 8000)
- **Frontend:** control-plane/src/main.tsx → React + Vite (port 5180)
- **Knowledge:** app/knowledge/engine.py → KnowledgeEngine (RAG + SQLite)
- **Hermes:** app/hermes/agent.py → HermesAgent (chat orchestration)

### Data Flow
```
User → Frontend (5180) → Backend API (8000) → Hermes → Knowledge Engine → RAG (SQLite) → Ollama (11434)
```

### Key Modules
| Module | Purpose | Status |
|---|---|---|
| app/knowledge/engine.py | Knowledge Engine facade | ✅ Active |
| app/knowledge/rag.py | RAG retrieval (hybrid semantic+lexical) | ✅ Active |
| app/knowledge/sop_review.py | SOP review/approval governance | ✅ Active |
| app/knowledge/grounding.py | Evidence grounding guard | ✅ Active |
| app/knowledge/chunker.py | Structure-aware chunking | ✅ Active |
| app/knowledge/docling_worker.py | Docling OCR extraction | ✅ Active |
| app/knowledge/docling_layout.py | Activity grid detection | ✅ Active |
| app/hermes/agent.py | Hermes chat orchestration | ✅ Active |
| app/api/routes.py | FastAPI routes | ✅ Active |
| app/security/v1_knowledge.py | V1 knowledge boundary | ✅ Active |
| app/models/ollama.py | Ollama provider | ✅ Active |
| app/models/openrouter.py | OpenRouter provider | ✅ Available (not configured) |

## 3. Database Schema

| Table | Rows | Purpose |
|---|---|---|
| documents | 64 | Document metadata and content |
| chunks | 721 | Vector store chunks with embeddings |
| knowledge_pipeline_runs | 175 | Pipeline audit trail |
| knowledge_pipeline_config | 1 | Watch folder config |
| sop_review_events | 719 | SOP review decisions |
| sop_review_trials | 148 | Chat trial results |
| sop_review_sessions | 56 | Session bindings |
| sop_review_pilots | 14 | Pilot document registry |
| document_extractions | 193 | Docling extraction results |

## 4. Knowledge/RAG Forensics

### Document Inventory
- 64 documents total
- 44 SOP documents (CAPIL, DAFDUK, PIAK, PERMOHONAN)
- 43 Aktif (approved and indexed)
- 1 Ditolak (PIAK-03 RAG test, deliberately rejected)
- 20 non-SOP documents (test files, audit.txt, etc.)

### Retrieval Pipeline
- Hybrid: 0.50 semantic (IndoBERT 768D) + 0.50 lexical (token overlap)
- Noise filter: score >= 0.50
- Document-level grouping: best chunk per document
- Title boost: +0.40 for exact title match
- RAG relevance gate: min_score=0.35, relative=0.65

### Chunking
- Structure-aware: preserves sentence/paragraph/table boundaries
- No overlap prepending (chunks match source text)
- Chunk size: 512, overlap: 64

### Known Issues
1. Search threshold (0.50) may be too high for some queries
2. Title boost not sufficient for OCR-garbled titles
3. Chunker doesn't track source positions (start_char computed from chunk, not source)

## 5. Security Forensics

### Authentication
- Admin token: shared (NUSANTARA_ADMIN_TOKEN)
- Mechanism: hmac.compare_digest (fail-closed)
- Source: .env file or environment variable

### Authorization
- Operator-only document chat: DOCUMENT_CHAT_REQUIRES_OPERATOR
- Operator-only model control: Model dikendalikan operator
- No auto-approval: explicit operator action required
- Session binding: prevents document/version switching
- Pilot gating: is_pilot() gates unapproved SOPs

### Known Issues
1. Shared admin token (no individual identity)
2. No rate limiting per user
3. No penetration testing
4. No path traversal test

## 6. Runtime Forensics

### Services
| Service | Port | Status |
|---|---|---|
| Backend (FastAPI) | 8000 | Running |
| Frontend (Vite) | 5180 | Running |
| Ollama (gemma3n 2B) | 11434 | Running |

### Model Provider
- Current: Ollama (gemma3n:e2b-it-q4_K_M, 2B)
- OpenRouter: Available but not configured (no API key)
- Feature flags: NUS_LANGCHAIN_ENABLED=false, NUS_LANGGRAPH_ENABLED=false

### Known Issues
1. Ollama model (2B) too small for grounded answers
2. Cannot download 7B+ models (no internet in sandbox)
3. IndoBERT worker unreliable (memory issues)

## 7. Control Plane (R1-R21)

Control Plane is implemented in control-plane/ (React + Vite). R1-R21 mapped to technical controls. AC1-AC15 mapped to acceptance criteria.

## 8. Code Quality

- 10602 Python files (includes .venv)
- 161 test files
- 34 app modules
- No circular dependencies detected
- Error handling: try/except in most critical paths
- Logging: structured logging with request_id, session_id, execution_id

## 9. Findings Summary

| ID | Finding | Risk | Status |
|---|---|---|---|
| F-01 | Chat abstains on all queries (LLM too small) | High | OPEN |
| F-02 | Precision@5 below target (0.3478 vs 0.50) | Medium | OPEN (metric limitation) |
| F-03 | LangGraph SOP workflow has stub nodes | Medium | PARTIAL (extract + others implemented) |
| F-04 | OCR ground truth not available | Medium | OPEN |
| F-05 | 5 test failures (environment) | Low | OPEN (environment issue) |
| F-06 | Grounding guard doesn't check negation | High | OPEN |
| F-07 | valid_chat_session too loose | Medium | FIXED (restricted to safe chars) |
| F-08 | Metadata reports 70/30 but actual is 50/50 | Low | FIXED (metadata updated) |
| F-09 | is_pilot excludes UNVERIFIED docs | High | FIXED (pipeline metadata check) |
| F-10 | Citation pages lost (chunker overlap) | Medium | FIXED (no overlap prepending) |
| F-11 | Hermes fallback self-validation | High | FIXED (source self-validation prevented) |
| F-12 | Search candidate window too narrow | Medium | FIXED (widened 4x) |

## 10. Recommendations

1. **Immediate:** Obtain 7B+ model (download manually outside sandbox)
2. **Short-term:** Implement remaining LangGraph stubs
3. **Medium-term:** Create OCR ground truth (manual transcription)
4. **Long-term:** Add negation check to grounding guard (requires contract approval)

---

**Status: FORENSIC AUDIT COMPLETE**

**Next step: Awaiting operator approval for remediation phase.**
