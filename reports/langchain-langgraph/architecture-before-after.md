# Architecture Before/After — LangChain & LangGraph Integration

## Before
```
FastAPI → KnowledgeEngine → HybridRAG → SemanticRetriever → SQLiteVectorStore
       → OllamaProvider (HTTP) → Ollama
       → HermesAgent (chat orchestration)
       → SOPReview (approval)
```

## After (with feature flags OFF — default)
```
FastAPI → KnowledgeEngine → HybridRAG → SemanticRetriever → SQLiteVectorStore
       → OllamaProvider (HTTP) → Ollama
       → HermesAgent (chat orchestration)
       → SOPReview (approval)
```
No change when flags are OFF.

## After (with feature flags ON — testing only)
```
FastAPI → KnowledgeEngine → HybridRAG → SemanticRetriever → SQLiteVectorStore
       → LangChain Adapter (optional wrapper)
         → ChatOllama (wraps OllamaProvider)
         → NusantaraRetriever (wraps HybridRAG.query)
       → HermesAgent (chat orchestration, unchanged)
       → SOPReview (approval, unchanged)
       → LangGraph Workflow (optional orchestration)
         → StateGraph (typed state, conditional edges)
         → Checkpoint (per workflow run)
```

## Key Principle
Integration Layer wraps existing services. Core Engine remains unchanged.
Feature flags default OFF. Rollback = set flags to false.
PY