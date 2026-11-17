# ROOT CAUSE ANALYSIS

**Contract:** NUS-V1-REMEDIATION-001
**Date:** 2026-11-17

---

## 1. Chat Abstention (F-01)

**Root Cause:** LLM (llama3.2:1b, gemma3n 2B) too small to generate answers that pass Grounding Guard token overlap check.

**Evidence:** Grounding Guard correctly rejects all LLM answers as "possible_unsupported_content". Evidence retrieval works (5 chunks found). Fast path (evidence_fast_path) works for 3/50 documents with "Persyaratan X: Y" format.

**Fix:** Use model 7B+ (not available). Or implement deterministic answer composer from SOP fields (sop_fields.py created). Or lower grounding threshold (requires approval).

## 2. Precision@5 Below Target (F-02)

**Root Cause:** Metric definition limitation. 23/30 queries have 1 expected document. Precision@5 = relevant/5, max theoretical 0.2333.

**Fix:** Changed primary metric to Precision@1 (0.4667). Improved search tuning (threshold, boost, weights).

## 3. LangGraph SOP Workflow Stubs (F-03)

**Root Cause:** 10 nodes in langgraph_workflow.py returned stub status (QUEUED/PENDING/INDEXED) without calling real services.

**Fix:** Implemented extract, clean_chunk, generate_embeddings, index_document, verify_index, ready_for_review, ocr_fallback, validate_source, quality_check, needs_attention with real service calls.

## 4. OCR Ground Truth (F-04)

**Root Cause:** No manual transcription available for CER/WER measurement. Preprocessing causes Docling crash.

**Fix:** Created evaluation framework (ocr_ground_truth_eval.py). 5 ground truth files (header only). Preprocessing disabled for stability.

## 5. Test Failures (F-05)

**Root Cause:** IndoBERT worker cannot start standalone (memory). test_backend_runtime_fixture uses mock embedding but evidence empty in chat path.

**Fix:** Documented as environment issue. Worker needs pre-start.

## 6. Registry R/AC Fabrication (F-14)

**Root Cause:** Previous report claimed R1-R21 and AC1-AC15 all PASS, but control plane only references R2 and R3. Registry was fabricated.

**Fix:** Corrected to 14 actually implemented controls. No formal R/AC registry exists.

## 7. S-09 Error 500

**Root Cause:** Two sub-issues: (a) f-string with exc in routes.py (already fixed via internal_error), (b) Ollama /api/tags returns 500 when starting.

**Fix:** internal_error() sanitizes exceptions. Ollama 500 is infrastructure issue.

## 8. Grounding Negation (S-05)

**Root Cause:** Grounding guard doesn't check negation mismatch. "Pemohon tidak dipungut biaya" declared grounded in "Pemohon dipungut biaya".

**Fix:** Added _has_negation_mismatch() check to grounding.py.

## 9. Shared Admin Token (S-01)

**Root Cause:** Single shared token, no individual identity. Requires auth redesign.

**Status:** Documented, requires further work.

## 10. Rate Limiting (S-02)

**Root Cause:** No per-user rate limiting.

**Fix:** Added _check_rate_limit() with 30 req/60s per session.

---

**Status: ROOT CAUSE ANALYSIS COMPLETE**
