# SERVICE TEST REPORT — Nusantara V1

Date: 2026-11-18

## Test Suites

| Suite | Passed | Failed | Notes |
|---|---|---|---|
| test_knowledge_pipeline | 5 | 0 | All pass |
| test_sop_review | 13 | 0 | All pass |
| test_langchain_adapter | 4 | 0 | All pass |
| test_langgraph_workflow | 4 | 0 | All pass |
| test_langchain_hardening | 13 | 0 | All pass |
| test_backend_runtime_fixture | 1 | 0 | E2E test PASS |
| test_approval_boundary | 9 | 0 | New tests |
| test_policy_engine | 8 | 0 | New tests |
| test_restart_recovery | 6 | 0 | New tests |
| **Total** | **63** | **0** | All pass |

## Security Tests

- automated_regression.py: 6/6 PASS

## Search Evaluation

- 160 queries: Recall@5=0.8278, MRR=0.5672, P@1=0.4667, P@5=0.3478

## Docker

- Build: SUCCESS (nusantara-v1-test:latest, 493MB)
- Run: health check PASS
