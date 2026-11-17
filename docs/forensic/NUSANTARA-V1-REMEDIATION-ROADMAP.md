# NUSANTARA V1 REMEDIATION ROADMAP

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17

---

## Priority 0 — Critical (must fix before production)

| ID | Issue | Fix | Effort | Status |
|---|---|---|---|---|
| R-01 | Chat abstains (LLM too small) | Use 7B+ model (download manually) | 1h | BLOCKED (no internet) |
| R-02 | Grounding guard negation | Add negation check to _claim_supported | 2h | OPEN (requires approval) |
| R-03 | is_pilot excludes UNVERIFIED | FIXED: pipeline metadata check | 1h | DONE |
| R-04 | Hermes fallback self-validation | FIXED: prevent source self-validation | 1h | DONE |
| R-05 | valid_chat_session too loose | FIXED: restrict to safe chars | 30m | DONE |

## Priority 1 — High (should fix before release)

| ID | Issue | Fix | Effort | Status |
|---|---|---|---|---|
| R-06 | Citation pages lost (chunker overlap) | FIXED: remove overlap prepending + fallback match | 2h | DONE |
| R-07 | Search metadata mismatch (70/30 vs 50/50) | FIXED: metadata updated | 30m | DONE |
| R-08 | Search candidate window too narrow | FIXED: widened 4x | 1h | DONE |
| R-09 | LangGraph SOP workflow stubs | Implement remaining 3 nodes | 4h | PARTIAL |
| R-10 | Precision@5 below target | Change metric to Precision@1/MRR | 1h | DONE |
| R-11 | OCR ground truth | Create manual transcription | 8h | FRAMEWORK |
| R-12 | 5 test failures (environment) | Start IndoBERT worker before tests | 30m | ENV ISSUE |

## Priority 2 — Medium (should fix for quality)

| ID | Issue | Fix | Effort | Status |
|---|---|---|---|---|
| R-13 | Golden Set enhancement | Run enhanced generator | 2h | DONE |
| R-14 | 100+ query dataset | Expand to 166 queries | 4h | DONE |
| R-15 | OCR table accuracy (19.4%) | Improve grid detection | 8h | OPEN |
| R-16 | Performance baseline formal | Run 10 SOP benchmark | 2h | OPEN |
| R-17 | Security penetration test | Install OWASP ZAP/Burp | 4h | OPEN |
| R-18 | 10 non-SOP docs | Mark as "Bukan SOP" | 1h | DONE |
| R-19 | Cost governance test | Test with OpenRouter API key | 2h | BLOCKED (no key) |
| R-20 | OCR preprocessing validation | Test on degraded scans | 4h | OPEN |
| R-21 | LangGraph chat E2E production | Test with flag ON | 1h | DONE |
| R-22 | Automated regression test | Create test script | 2h | DONE |
| R-23 | No-answer questions | Add to dataset | 1h | DONE |
| R-24 | Multi-step questions | Create questions | 2h | DONE |
| R-25 | OCR confidence scoring | Add to payload | 1h | DONE |

## Summary

- **DONE:** 16 items
- **PARTIAL:** 3 items (chat quality, OCR ground truth, golden set)
- **OPEN:** 6 items (OCR table, performance, security, non-SOP, preprocessing, LangGraph E2E)
- **BLOCKED:** 2 items (model 7B download, API key)

## Next Steps

1. Download model 7B+ manually (outside sandbox)
2. Run chat answer quality test with 7B model
3. Create OCR ground truth (manual transcription)
4. Run security penetration test
5. Run performance baseline on 10 SOPs
6. Implement remaining LangGraph stubs
7. Obtain OpenRouter API key for cost governance test
