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
| S-03 | No penetration testing | High | PARTIAL (targeted manual probes done 2026-11-17; full OWASP scan not performed) |
| S-04 | No path traversal test | Medium | TESTED/CONFIRMED (2026-11-17: traversal rejected, see §8) |
| S-05 | Grounding guard doesn't check negation | High | OPEN |
| S-06 | Hermes fallback validated source against itself | High | FIXED |
| S-07 | valid_chat_session accepted any string | Medium | FIXED (runtime-verified: `../evil`→403) |
| S-08 | is_pilot excluded UNVERIFIED docs | High | FIXED |
| S-09 | Raw exception interpolated into HTTP 500 detail (routes.py:1424,1510,1561); info-disclosure | Low | OPEN (new 2026-11-17) |

## 7. Test Results

- Security regression: 6/6 PASS
- test_sop_review: 13/13 PASS
- test_langchain_hardening: 9/13 PASS (4 env failures)

---

## 8. Non-Destructive Probe Results — 2026-11-17 (READ-ONLY, HEAD de5dc52b)

All probes were GET/read-only or parameterized-search; no data modified. Token loaded from .env without printing.

| Probe | Endpoint | Result |
|---|---|---|
| Auth bypass (no token) | GET /v1/knowledge/pipeline/reviews/{doc}/source | 403 "admin token diperlukan" (fail-closed) |
| Auth bypass (no token) | GET /v1/knowledge/pipeline/reviews/{doc} | 403 |
| Legitimate access (token) | GET .../source | 200 PDF 462551 bytes |
| Path traversal `..%2f..%2f..%2f.env` | GET .../reviews/{payload}/source | 404 Not Found (routing) |
| Path traversal double-encoded `..%252f..%252f.env` | same | 404 "File sumber belum ditemukan" (DB-key lookup) |
| Path traversal `%2e%2e%2f...`, `....//....//`, `..%5c..%5c` | same | 404 |
| Nonexistent doc | GET .../reviews/DOC-NONEXISTENT-999/source | 404 (DB lookup) |
| Session traversal `../evil` | GET .../citation | 403 CHAT_SESSION_CAPABILITY_REQUIRED |
| SQL injection `' OR 1=1; DROP TABLE documents;--` | POST /v1/knowledge/search | 200 empty results; DB intact (64 docs, 9 tables) |
| Search no token | POST /v1/knowledge/search | 403 |
| Secret leakage | GET snapshot / model-status / health/detail | no token, no env-name leakage |

**Traversal protection root cause (why safe):** `app/knowledge/sop_review.py:112-130` — document_id is resolved as a DB index key (`get_document_info`), never a filesystem path; candidate paths rejected if symlink, if `resolve().parent != source-documents folder`, or if not a file; SHA-256 integrity + 20MB cap enforced. `require_admin` (`app/security/auth.py:12-21`) fail-closed with hmac.compare_digest.

**New finding S-09 (Low):** `app/api/routes.py:1424,1510,1561` interpolate raw exception text into HTTP 500 `detail` (e.g. `f"Knowledge search error: {exc}"`). This contradicts §5 "No stack trace to users / Generic error messages". Exception messages may leak internal paths/SQL/config. Recommend generic client message + server-side log.

**Performance note:** normal semantic search timed out at 25s (IndoBERT embedding worker slow/unreliable, consistent with F-05). SQLi payload returned quickly with empty results (no semantic match).

---

**Status: PARTIAL (targeted probes CONFIRMED protections; full OWASP penetration scan outstanding; shared token S-01, rate limiting S-02, negation S-05, raw-exception S-09 remain OPEN)**
