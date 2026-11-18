# SERVICE SECURITY AUDIT — Nusantara V1

Date: 2026-11-18

## Authentication

- Admin token: NUSANTARA_ADMIN_TOKEN (shared, single token)
- Header: X-Admin-Token
- Validation: hmac.compare_digest (timing-safe)

## Authorization

- V1KnowledgeBoundary gates pilot documents
- Operator flag required for knowledge search
- Document IDs supplied by caller cannot grant access

## Security Controls (14)

1. Runtime status check
2. Service health check
3. Model status check
4. Pipeline status check
5. Authentication (admin token)
6. Authorization (V1KnowledgeBoundary)
7. Trust metadata
8. Approval workflow (SOPReview.decide)
9. Scope enforcement
10. Secret protection (response projection - chunks cleared)
11. Evidence tracking
12. Error tracking (taxonomy: TRANSIENT/PERMANENT/NEEDS_HUMAN/POLICY_DENIED)
13. Audit history (sop_review_events)
14. Recovery (retry_knowledge_source)

## Security Tests (6/6 PASS)

- search_without_token: 403
- admin_endpoint_without_token: 403
- chat_without_token_no_evidence: 0 evidence
- empty_input_rejected: 422
- pipeline_status_accessible: PASS
- session_isolation: PASS

## Known Gaps

- Shared admin token (no individual identity) — requires auth redesign
- No penetration testing (no tools)
- No Docker isolation test
- No filesystem race condition test
