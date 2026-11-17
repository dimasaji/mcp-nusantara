# NUSANTARA V1 RUNTIME VALIDATION

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17

---

## 1. Service Status

| Service | Port | Status | Model/Info |
|---|---|---|---|
| Backend (FastAPI) | 8000 | Running | gemma3n:e2b-it-q4_K_M |
| Frontend (Vite) | 5180 | Running | — |
| Ollama | 11434 | Running | gemma3n:e2b-it-q4_K_M |

## 2. Health Check

- GET /v1/health: 200 OK
- GET /v1/health/detail: llm status ok, model gemma3n:e2b-it-q4_K_M

## 3. Knowledge Pipeline

- Documents indexed: 64
- Pipeline READY: 53
- SOP Aktif: 44
- SOP total: 44 (CAPIL, DAFDUK, PIAK, PERMOHONAN)

## 4. Search Validation

- Recall@5: 0.8278
- MRR@10: 0.5672
- Precision@1: 0.4667
- Precision@5: 0.3478
- Exact_match: 0.4667
- Latency mean: 192.2 ms

## 5. Chat Validation

- Grounded (Hermes): False (abstain)
- Grounded (LangGraph): True (fast path)
- Abstention: Works
- Citation resolution: E2E verified (200, PDF 1.1MB)

## 6. Test Results

- test_knowledge_pipeline: 5 passed
- test_sop_review: 13 passed
- test_langchain_adapter: 4 passed
- test_langgraph_workflow: 4 passed
- test_langchain_hardening: 9 passed, 4 failed (env)
- test_backend_runtime_fixture: 1 failed (env)
- Total: 35 passed, 5 env failures

## 7. Known Issues

1. Chat abstains on SOP-grounded queries (LLM too small); general chat answers naturally
2. 5 test failures (environment)
3. OCR ground truth not available
4. No full OWASP penetration testing (targeted probes done)
5. No 7B+ model available
6. Chat latency high (45.4s / 11s); semantic search timeout 25s (IndoBERT worker)
7. Live-DB on-disk backup stale (F-13)

## 8. Browser E2E + Multi-turn — 2026-11-17 (READ-ONLY, HEAD de5dc52b)

- Browser renders AI Workspace (5180). POST /v1/chat → 200 ndjson via proxy (real backend).
- Turn 1 "Apa itu KTP-el dan apa fungsinya?" → natural answer, model gemma3n:e2b-it-q4_K_M, jalur ollama, latency 45372ms.
- Turn 2 follow-up "Apa kepanjangan dari singkatan yang kamu sebutkan tadi?" → resolved to KTP-el (context works), latency 10951ms. Both SUCCEEDED.
- Honest metadata: "Jawaban percakapan; tidak dinilai sebagai validasi dokumen resmi"; grounding not_evaluated for general chat.
- Session persisted to data/knowledge/chat-history/ (FR-04).
- Evidence: docs/forensic/evidence/browser-01-home, browser-02-chat-response (PNG), browser-chat-multiturn (JSON).
- Control-plane snapshot live: phases R1=UNKNOWN,R2=NOT_VERIFIED,R3=PASS_WITH_CONDITIONS,R4/R5=LOCKED,MDE10=NOT_AUTHORIZED; 14 gates; verification PASS (fixture).
- Recovery round-trip (temp): integrity ok, 64 docs/721 chunks, hash match; existing live backup stale (21 docs/45 chunks).
