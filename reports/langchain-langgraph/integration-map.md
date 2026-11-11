# Integration Map — LangChain & LangGraph for Nusantara V1

## P0 — Focused Code Inspection

### Component Map

| Komponen | Implementasi saat ini | Integrasi baru | Keputusan |
|---|---|---|---|
| Ollama | `app/models/ollama.py` — `OllamaProvider` wraps HTTP calls to Ollama | LangChain `ChatOllama` adapter | Reuse / wrap |
| Retrieval | `app/knowledge/production_hybrid_rag.py` — `HybridRAG.query()` | Retriever adapter | Reuse |
| Haystack | `app/knowledge/text_cleaning.py` — `DocumentCleaner` conservative | Existing Knowledge | Preserve |
| SOP Workflow | `app/knowledge/sop_review.py` — `SOPReview` (content_ok, metadata, approve, defer, reject) | LangGraph | Extend / retain |
| Approval | `SOPReview.decide()` with operator token | Interrupt/resume | Reuse |
| Checkpoint | SQLite `knowledge_pipeline_runs` table | LangGraph persistence | Reuse / add |
| Embedding | `app/knowledge/indobert_embedding.py` — `IndoBERTEmbeddingAdapter` | Keep as-is | Preserve |
| Chat | `app/hermes/agent.py` — `HermesAgent.execute_v1()` | LangChain chain (optional) | Reuse |
| Access Control | `app/security/v1_knowledge.py` — `V1KnowledgeBoundary` | Wrap in adapter | Reuse |
| Citation | `app/knowledge/document_citations.py` — `citations_supported()` | Keep as-is | Preserve |

### Key Files
- `app/hermes/agent.py` — Chat orchestration, grounding, evidence
- `app/knowledge/rag.py` — RAG orchestrator, ChunkProcessor
- `app/knowledge/production_hybrid_rag.py` — Hybrid retrieval (lexical + semantic + fusion)
- `app/knowledge/production_semantic_retriever.py` — Semantic retriever
- `app/knowledge/sop_review.py` — SOP review, approval, metadata
- `app/models/ollama.py` — Ollama provider
- `app/knowledge/engine.py` — KnowledgeEngine (upload, search, chunking)
- `app/security/v1_knowledge.py` — Access control boundary

### LangChain/LangGraph Availability
- langchain 1.4.10 ✅
- langgraph ✅
- langchain-ollama ✅
- langchain-core ✅

### Integration Point
The smallest change: create a LangChain adapter in `app/knowledge/langchain_adapter.py` that wraps:
1. `OllamaProvider` → `ChatOllama` for LLM calls
2. `HybridRAG.query()` → LangChain `BaseRetriever` for retrieval
3. Keep all existing evidence/citation logic

Feature flags: `NUS_LANGCHAIN_ENABLED=false`, `NUS_LANGGRAPH_ENABLED=false` (default OFF)

### Dependency Impact
- langchain 1.4.10 added to .venv
- No changes to existing dependencies
- No new database or vector store
- V2 remains disabled

### Decision
- Reuse existing retriever (wrap, don't replace)
- Reuse existing Ollama provider (wrap with ChatOllama)
- Reuse existing approval (SOPReview.decide)
- LangGraph for SOP workflow orchestration (optional, behind feature flag)
PY