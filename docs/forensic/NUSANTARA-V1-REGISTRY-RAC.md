# REGISTRY R/AC MAPPING — NUSANTARA V1

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17

---

## R1-R21 Mapping (CORRECTED)

**Note:** The control plane (control-plane/src/acceptance.ts) only references R2 and R3.
R1-R21 and AC1-AC15 are NOT implemented as a registry in the control plane.
The previous mapping (R1-R21 all PASS) was fabricated.

### Actually Implemented Controls

| Control | Implementation | Endpoint | Test | Status |
|---|---|---|---|---|
| Runtime status | app/api/runtime_readiness.py | GET /v1/runtime/readiness | test_runtime_readiness | PASS |
| Service health | app/api/routes.py health_check | GET /v1/health, /v1/health/detail | test_backend_runtime_fixture | PASS |
| Model status | app/models/ollama.py health_check | GET /v1/health/detail | test_model_status_inference_v1 | PASS |
| Pipeline status | app/knowledge/engine.py knowledge_pipeline_status | GET /v1/knowledge/pipeline/status | test_knowledge_pipeline | PASS |
| Authentication | app/security/auth.py (require_admin) | All admin endpoints | test_runtime_authorization | PASS |
| Authorization | app/security/v1_knowledge.py (V1KnowledgeBoundary) | Chat, search | test_v1_session_contract | PASS |
| Trust metadata | app/trust/engine.py (TrustEngine) | Chat response trust | test_phase4_trust_contract | PASS |
| Approval workflow | app/knowledge/sop_review.py (decide) | POST /v1/knowledge/pipeline/reviews/{id}/decision | test_sop_review | PASS |
| Scope enforcement | app/knowledge/engine.py (document_scope) | Search filter | test_document_scope_v1 | PASS |
| Secret protection | app/api/routes.py (_project_v1_chat_response) | Chat response | test_v1_response_projection | PASS |
| Evidence tracking | app/knowledge/grounding.py | Chat response evidence | test_v1_chat_rag_regression | PASS |
| Error tracking | app/core/error_taxonomy.py | N/A | test_phase3_observability | PASS |
| Audit history | sop_review_events table | GET /v1/knowledge/pipeline/reviews/{id} | test_sop_review | PASS |
| Recovery | retry_knowledge_source | POST /v1/knowledge/pipeline/runs/{id}/retry | test_knowledge_pipeline | PASS |

### NOT Implemented as Registry

R1-R21 and AC1-AC15 are NOT implemented as a formal registry in the control plane.
The control plane (control-plane/src/acceptance.ts) only references R2 and R3.
The previous claim of "R1-R21 all PASS" was fabricated.

## Summary

- Controls actually implemented: 14 (listed above)
- Controls claimed but not implemented as registry: R1-R21, AC1-AC15
- All implemented controls have corresponding tests
- No orphaned controls found

**Status: PARTIAL (controls exist but not as formal R/AC registry)**
