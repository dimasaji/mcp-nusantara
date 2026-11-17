# TEST EXECUTION REPORT

**Contract:** NUS-V1-REMEDIATION-001
**Date:** 2026-11-17

---

## Test Results

| Test Suite | Passed | Failed | Notes |
|---|---|---|---|
| test_knowledge_pipeline | 5 | 0 | All pass |
| test_sop_review | 13 | 0 | All pass |
| test_langchain_adapter | 4 | 0 | All pass |
| test_langgraph_workflow | 4 | 0 | All pass |
| test_langchain_hardening | 13 | 0 | All pass (was 9+4 env failures) |
| test_backend_runtime_fixture | 0 | 1 | Pre-existing (evidence empty in chat) |
| **Total** | **39** | **1** | 1 pre-existing env failure |

## Security Tests

- automated_regression.py: 6/6 PASS
- search_without_token: PASS
- admin_endpoint_without_token: PASS
- chat_without_token_no_evidence: PASS
- empty_input_rejected: PASS
- pipeline_status_accessible: PASS
- session_isolation: PASS

## Search Evaluation

- 160 queries: Recall@5=0.8278, MRR=0.5672, P@1=0.4667, P@5=0.3478

## OCR Ground Truth

- 5 SOPs evaluated: CER 27-51% (header only)
- Framework ready for full transcription

## Status: PARTIAL (1 pre-existing test failure)
