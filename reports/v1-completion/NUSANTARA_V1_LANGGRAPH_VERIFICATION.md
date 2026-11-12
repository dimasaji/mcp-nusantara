# NUSANTARA V1 LANGGRAPH VERIFICATION REPORT

**Contract:** NUSANTARA-V1-MASTER-2026-001
**Phase:** 6 — LangGraph Production Integration
**Date:** 2026-11-12
**Branch:** codex/fullroot-control-20261007

---

## 1. Implementation Overview

Two LangGraph implementations exist:

### A. langgraph_chat.py — Chat Workflow
- **Purpose:** Orchestrate chat pipeline (scope, intent, retrieval, generation, grounding, citations)
- **Nodes:** 8 (resolve_scope, classify_intent, retrieve, validate_evidence, generate, verify_grounding, verify_citations, abstain)
- **Service calls:** search_knowledge, provider.generate, grounding_guard.validate
- **Status:** E2E tested (grounded=True, citations present)
- **Feature flag:** NUS_LANGGRAPH_ENABLED (default OFF)

### B. langgraph_workflow.py — SOP Processing Workflow
- **Purpose:** Orchestrate SOP processing (Docling, cleaning, indexing, approval)
- **Nodes:** 10 (validate_source, extract, quality_check, ocr_fallback, clean_chunk, generate_embeddings, index_document, verify_index, ready_for_review, needs_attention)
- **Service calls:** NONE — all nodes are stubs (return QUEUED/PENDING/INDEXED)
- **Status:** NOT production-ready
- **Feature flag:** NUS_LANGGRAPH_ENABLED (default OFF)

## 2. Node-by-Node Verification

### langgraph_chat.py (Chat Workflow)

| Node | Service Called | Real? | Error Handling | Status |
|---|---|---|---|---|
| resolve_scope | None (state init) | N/A | N/A | PASS |
| classify_intent | None (passthrough) | N/A | N/A | PASS |
| retrieve | knowledge_engine.search_knowledge() | YES | try/except, returns [] on failure | PASS |
| validate_evidence | grounding_guard.validate() | YES | try/except, returns False on failure | PASS |
| generate | provider.generate() | YES | try/except, returns '' on failure | PASS |
| verify_grounding | grounding_guard.validate() | YES | try/except | PASS |
| verify_citations | None (projection) | N/A | N/A | PASS |
| abstain | None (fallback) | N/A | N/A | PASS |

### langgraph_workflow.py (SOP Processing Workflow)

| Node | Service Called | Real? | Error Handling | Status |
|---|---|---|---|---|
| validate_source | Path.exists() only | PARTIAL | Returns PERMANENT on missing | STUB |
| extract | None (returns QUEUED) | NO | None | STUB |
| quality_check | None (status check) | PARTIAL | None | STUB |
| ocr_fallback | None (increments retry) | NO | None | STUB |
| clean_chunk | None (returns PASS) | NO | None | STUB |
| needs_attention | None (sets NEEDS_HUMAN) | PARTIAL | None | STUB |
| generate_embeddings | None (returns PENDING) | NO | None | STUB |
| index_document | None (returns INDEXED) | NO | None | STUB |
| verify_index | None (returns VERIFIED) | NO | None | STUB |
| ready_for_review | None (returns PENDING_REVIEW) | NO | None | STUB |

## 3. E2E Test Results

### langgraph_chat.py
- Tested with real Ollama (llama3.2:1b) + retriever + grounding
- Result: grounded=True, citations present, answer generated
- Feature flag default OFF (verified)

### langgraph_workflow.py
- Tests pass (4 tests in test_langgraph_workflow.py)
- But tests only check workflow structure, not service calls
- No E2E test with real Docling/extraction/indexing

## 4. Issues Found

1. **langgraph_workflow.py nodes are all stubs** — extract, clean_chunk, generate_embeddings, index_document, verify_index, ready_for_review don't call any real services
2. **No error handling** in stub nodes — no try/except, no error codes
3. **No conditional edge for extraction failure** — quality_check returns FAIL but route_quality only checks retry count
4. **No integration with DocumentTools** — the workflow doesn't use the existing Docling pipeline
5. **No audit trail** — workflow doesn't record events to sop_review_events

## 5. Recommendations

1. **Implement real service calls** in langgraph_workflow.py nodes:
   - extract → call DocumentTools.process() (Docling)
   - clean_chunk → call clean_extraction()
   - generate_embeddings → call embedding adapter
   - index_document → call RAG.ingest_document()
   - verify_index → verify chunks in store
   - ready_for_review → enroll in SOPReview

2. **Add error handling** with try/except and error codes (TRANSIENT/PERMANENT/NEEDS_HUMAN/POLICY_DENIED)

3. **Add conditional edges** for extraction failure, indexing failure, etc.

4. **Keep feature flag OFF** until all nodes use real services

5. **Add E2E tests** with real Docling + extraction + indexing

## 6. Feature Flag Status

- NUS_LANGGRAPH_ENABLED: default 'false' (OFF)
- NUS_LANGCHAIN_ENABLED: default 'false' (OFF)
- Verified: flags OFF → legacy path used (test_flags_off_legacy_path PASS)

## 7. Commit

- Phase 6 report only, no code changes to langgraph_workflow.py
- langgraph_chat.py already E2E tested and working
- langgraph_workflow.py needs significant refactoring (deferred to operator approval)
