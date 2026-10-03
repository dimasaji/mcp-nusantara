# ARCHITECTURE_CURRENT — V1

```
Client/UI ─► FastAPI (/v1) ─► LanguageEngine ─► ProblemEngine ─► KnowledgeEngine(RAG in-memory) ─► OllamaProvider
                                   (terpisah, tidak di jalur chat): Policy · Trust · Memory · MCP · Tools · Handoff · Reasoning · Workflow
```
| Layer | Status V1 |
|---|---|
| API | EXISTING (/v1, tanpa auth) |
| Orchestration | PARTIAL (`HermesAgent` tidak dipakai `/chat`) |
| Core engine (language/problem/reasoning) | EXISTING |
| Model | EXISTING (Ollama, OpenAI-compat, Mock, Router) |
| Memory | PARTIAL (store TTL + pickle LTM; tidak terhubung) |
| RAG | PARTIAL (parser/chunker/embedding hash/retriever/reranker; in-memory) |
| Tool/MCP | PARTIAL (registry sederhana, MCPServer lokal) |
| Security | PARTIAL (policy & trust ada, belum di jalur eksekusi) |
| Observability | MISSING |
| Storage | MISSING (semua in-process) |
| Experience / R&D | MISSING |
