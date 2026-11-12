# NUSANTARA V1 SECURITY REPORT

**Contract:** NUSANTARA-V1-MASTER-2026-001
**Phase:** 8 — Security & Cost Governance
**Date:** 2026-11-12
**Branch:** codex/fullroot-control-20261007

---

## 1. Authentication

| Control | Status | Evidence |
|---|---|---|
| Admin token required for review actions | PASS | require_admin(x_admin_token) in knowledge_pipeline.py |
| Admin token required for upload | PASS | require_admin in add_knowledge_source |
| Admin token required for process/retry | PASS | require_admin in process_review, retry |
| Public chat (no token) | PASS | Returns 200 but no evidence for internal docs |
| Token stored in frontend (localStorage) | INFO | Auth context manages token |

## 2. Authorization

| Control | Status | Evidence |
|---|---|---|
| Operator-only document chat | PASS | DOCUMENT_CHAT_REQUIRES_OPERATOR check |
| Operator-only model control | PASS | Model dikendalikan operator; perbarui status model aktif |
| No auto-approval | PASS | Approval requires explicit operator action + can_approve check |
| Session binding | PASS | bind_session prevents document/version switching |
| Pilot gating | PASS | is_pilot() gates unapproved SOPs from chat |

## 3. Access Control

| Control | Status | Evidence |
|---|---|---|
| Search without token → 403 | PASS | Tested: public search returns 403 |
| Chat without evidence → abstention | PASS | Tested: public chat returns 0 evidence |
| Document access boundary | PASS | V1KnowledgeBoundary validates response |
| Version validation | PASS | validate_response checks source_versions |

## 4. Input Validation

| Control | Status | Evidence |
|---|---|---|
| Chat input sanitization | PASS | sanitize_text in chat endpoint |
| Document ID validation | PASS | max 256 chars, existence check |
| File size limit | PASS | 20 MB max (FILE_TOO_LARGE_MAX_20MB) |
| Format validation | PASS | Supported: PDF, DOCX, TXT, MD, HTML, HTM |
| Session ID pattern | PASS | CHAT_SESSION_PATTERN = ^.{1,128}$ |

## 5. Data Protection

| Control | Status | Evidence |
|---|---|---|
| Source files stored with hash | PASS | SHA-256 digest as filename |
| Source integrity verification | PASS | STORED_SOURCE_INTEGRITY_MISMATCH check |
| No secret leakage in responses | PASS | _project_v1_chat_response strips internal fields |
| No stack trace to users | PASS | Generic error messages |
| Audit trail | PASS | sop_review_events table (kind, payload, principal, created_at) |

## 6. Cost Governance

| Control | Status | Evidence |
|---|---|---|
| Ollama (local) default | PASS | Provider: ollama, model: llama3.2:1b |
| OpenRouter disabled by default | PASS | NUS_OPENROUTER_ENABLED not set |
| Cost ledger (OpenRouter) | EXISTS | CostLedger with budget_usd=1.00, per_request_cap=0.05 |
| Model controlled by operator | PASS | Model dikendalikan operator check |
| Feature flags default OFF | PASS | NUS_LANGCHAIN_ENABLED=false, NUS_LANGGRAPH_ENABLED=false |

## 7. Known Gaps

1. **No penetration testing**: No formal security audit
2. **No path traversal test**: File upload path not tested for traversal
3. **No cost limit enforcement test**: OpenRouter cost governance not tested (disabled)
4. **No session isolation test**: Cross-session data leakage not formally tested
5. **Admin token is shared**: "shared-admin-token" — no individual identity
6. **No rate limiting**: _sync_slots (10 concurrent) but no per-user rate limit

## 8. Test Results

- test_langchain_hardening: 13 passed (includes session isolation, public access, abstention)
- test_sop_review: 13 passed (governance, approval, audit)
- test_backend_runtime_fixture: 1 passed (E2E with auth)

## 9. Commit

- Phase 8 report only, no code changes
