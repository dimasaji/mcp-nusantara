# NUSANTARA V1 SECURITY AUDIT

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17
**Repository:** C:\Users\dmaza\mcp-starter

---

## 1. Authentication

| Control | Status | Evidence |
|---|---|---|
| Admin token required for review | PASS | require_admin() in knowledge_pipeline.py |
| Admin token required for upload | PASS | require_admin in add_knowledge_source |
| Admin token required for process/retry | PASS | require_admin in process_review, retry |
| Public chat (no token) | PASS | Returns 200 but no evidence for internal docs |
| Token stored in frontend | INFO | Auth context manages token in memory |
| Token comparison | PASS | hmac.compare_digest (fail-closed) |

## 2. Authorization

| Control | Status | Evidence |
|---|---|---|
| Operator-only document chat | PASS | DOCUMENT_CHAT_REQUIRES_OPERATOR check |
| Operator-only model control | PASS | Model dikendalikan operator |
| No auto-approval | PASS | Approval requires explicit operator action |
| Session binding | PASS | bind_session prevents document/version switching |
| Pilot gating | FIXED | is_pilot() now checks pipeline metadata (was excluding UNVERIFIED) |
| Admin boundary | PASS | require_admin on all privileged endpoints |

## 3. Access Control

| Control | Status | Evidence |
|---|---|---|
| Search without token → 403 | PASS | Tested |
| Chat without evidence → abstention | PASS | Tested |
| Document access boundary | PASS | V1KnowledgeBoundary validates response |
| Version validation | PASS | validate_response checks source_versions |
| Session ID validation | FIXED | Restricted to safe chars (was ^.{1,128}$) |

## 4. Input Validation

| Control | Status | Evidence |
|---|---|---|
| Chat input sanitization | PASS | sanitize_text in chat endpoint |
| Document ID validation | PASS | max 256 chars, existence check |
| File size limit | PASS | 20 MB max |
| Format validation | PASS | PDF, DOCX, TXT, MD, HTML, HTM |
| SQL injection | PASS | Parameterized queries throughout |

## 5. Data Protection

| Control | Status | Evidence |
|---|---|---|
| Source files stored with hash | PASS | SHA-256 digest as filename |
| Source integrity verification | PASS | STORED_SOURCE_INTEGRITY_MISMATCH check |
| No secret leakage in responses | PASS | _project_v1_chat_response strips internal fields |
| No stack trace to users | PASS | Generic error messages |
| Audit trail | PASS | sop_review_events table |
| Grounding guard | PASS | Fail-closed, validates all answers |

## 6. Security Risks Found

| ID | Risk | Severity | Status |
|---|---|---|---|
| S-01 | Shared admin token (no individual identity) | Medium | OPEN |
| S-02 | No rate limiting per user | Medium | OPEN |
| S-03 | No penetration testing | High | OPEN |
| S-04 | No path traversal test | Medium | OPEN |
| S-05 | Grounding guard doesn't check negation | High | OPEN |
| S-06 | Hermes fallback validated source against itself | High | FIXED |
| S-07 | valid_chat_session accepted any string | Medium | FIXED |
| S-08 | is_pilot excluded UNVERIFIED docs | High | FIXED |

## 7. Test Results

- Security regression: 6/6 PASS
- test_sop_review: 13/13 PASS
- test_langchain_hardening: 9/13 PASS (4 env failures)

---

**Status: PARTIAL (no penetration test, shared token, no rate limiting)**
