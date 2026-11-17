# REGISTRY R/AC MAPPING — NUSANTARA V1

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17

---

## R1-R21 Mapping

| R# | Control | Implementation | Endpoint | Test | Status |
|---|---|---|---|---|---|
| R1 | Runtime status | app/api/runtime_readiness.py | GET /v1/runtime/readiness | test_runtime_readiness | PASS |
| R2 | Service health | app/api/routes.py health_check | GET /v1/health, /v1/health/detail | test_backend_runtime_fixture | PASS |
| R3 | Model status | app/models/ollama.py health_check | GET /v1/health/detail | test_model_status_inference_v1 | PASS |
| R4 | Pipeline status | app/knowledge/engine.py knowledge_pipeline_status | GET /v1/knowledge/pipeline/status | test_knowledge_pipeline | PASS |
| R5 | Tool execution status | app/tools/ | N/A | test_executable_skills | PASS |
| R6 | Evidence tracking | app/knowledge/grounding.py | Chat response evidence | test_v1_chat_rag_regression | PASS |
| R7 | Error tracking | app/core/error_taxonomy.py | N/A | test_phase3_observability | PASS |
| R8 | Audit history | app/knowledge/sop_review.py (events table) | GET /v1/knowledge/pipeline/reviews/{id} | test_sop_review | PASS |
| R9 | Recovery status | app/knowledge/engine.py (retry_knowledge_source) | POST /v1/knowledge/pipeline/runs/{id}/retry | test_knowledge_pipeline | PASS |
| R10 | Authentication | app/security/auth.py (require_admin) | All admin endpoints | test_runtime_authorization | PASS |
| R11 | Authorization | app/security/v1_knowledge.py (V1KnowledgeBoundary) | Chat, search | test_v1_session_contract | PASS |
| R12 | Risk assessment | app/trust/engine.py (TrustEngine) | Chat response trust | test_phase4_trust_contract | PASS |
| R13 | Approval | app/knowledge/sop_review.py (decide) | POST /v1/knowledge/pipeline/reviews/{id}/decision | test_sop_review | PASS |
| R14 | Deny | app/security/v1_knowledge.py | Chat (403, 409) | test_runtime_authorization | PASS |
| R15 | Audit trail | sop_review_events table | GET /v1/knowledge/pipeline/reviews/{id} | test_sop_review | PASS |
| R16 | Scope enforcement | app/knowledge/engine.py (document_scope) | Search filter | test_document_scope_v1 | PASS |
| R17 | Secret protection | app/api/routes.py (_project_v1_chat_response) | Chat response | test_v1_response_projection | PASS |
| R18 | Human override | app/knowledge/sop_review.py (decide) | Operator actions | test_sop_review | PASS |
| R19 | Verification | app/knowledge/grounding.py (validate) | Chat response grounding | test_v1_chat_rag_regression | PASS |
| R20 | Observability | app/observability/ | Metrics endpoint | test_phase3_observability | PASS |
| R21 | Recovery | Backup/restore scripts | N/A | test_backup_restore | PASS |

## AC1-AC15 Mapping

| AC# | Criteria | Implementation | Status |
|---|---|---|---|
| AC1 | Runtime status accurate | runtime_readiness.py | PASS |
| AC2 | Service health check | health/detail endpoint | PASS |
| AC3 | Model status verified | health/detail + provider | PASS |
| AC4 | Pipeline status accurate | knowledge_pipeline_status | PASS |
| AC5 | Tool execution tracked | executable_skills | PASS |
| AC6 | Evidence tracked | grounding.py + citation | PASS |
| AC7 | Error tracked | error_taxonomy.py | PASS |
| AC8 | Audit history | sop_review_events | PASS |
| AC9 | Recovery tracked | retry_knowledge_source | PASS |
| AC10 | Auth enforced | require_admin | PASS |
| AC11 | Authorization enforced | V1KnowledgeBoundary | PASS |
| AC12 | Trust metadata | TrustEngine | PASS |
| AC13 | Approval workflow | SOPReview.decide | PASS |
| AC14 | Scope enforcement | document_scope | PASS |
| AC15 | Secret protection | _project_v1_chat_response | PASS |

## Summary

- R1-R21: All mapped to implementations, all PASS
- AC1-AC15: All mapped to implementations, all PASS
- No orphaned controls found
- All controls have corresponding tests

**Status: PASS**
