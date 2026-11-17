# PATCH MANIFEST

**Contract:** NUS-V1-REMEDIATION-001
**Date:** 2026-11-17

---

## Files Modified

| File | Change | Risk | Rollback |
|---|---|---|---|
| app/knowledge/engine.py | Citation fallback + contentless filter + threshold 0.50 + regex fix | Medium | git checkout HEAD~1 -- app/knowledge/engine.py |
| app/knowledge/chunker.py | Remove overlap prepending | Low | git checkout HEAD~1 -- app/knowledge/chunker.py |
| app/knowledge/sop_review.py | is_pilot pipeline metadata + PARTIAL handling | Medium | git checkout HEAD~1 -- app/knowledge/sop_review.py |
| app/knowledge/rag.py | 50/50 weights, 0.35/0.65 gate, metadata consistency | Medium | git checkout HEAD~1 -- app/knowledge/rag.py |
| app/hermes/agent.py | Prevent source self-validation | Medium | git checkout HEAD~1 -- app/hermes/agent.py |
| app/security/v1_knowledge.py | Widen search window + CHAT_SESSION_PATTERN | Medium | git checkout HEAD~1 -- app/security/v1_knowledge.py |
| app/knowledge/docling_worker.py | OCR confidence scoring | Low | git checkout HEAD~1 -- app/knowledge/docling_worker.py |
| app/knowledge/langgraph_workflow.py | Real service calls in nodes | Medium | git checkout HEAD~1 -- app/knowledge/langgraph_workflow.py |
| app/knowledge/grounding.py | Negation mismatch check | Medium | git checkout HEAD~1 -- app/knowledge/grounding.py |
| app/api/routes.py | Rate limiting per session | Low | git checkout HEAD~1 -- app/api/routes.py |
| app/exceptions.py | internal_error sanitization | Low | git checkout HEAD~1 -- app/exceptions.py |
| app/knowledge/sop_fields.py | SOP field extractor (NEW) | Low | rm app/knowledge/sop_fields.py |
| scripts/backup_nusantara.py | Backup script (NEW) | Low | rm scripts/backup_nusantara.py |
| scripts/ocr_ground_truth_eval.py | OCR GT eval (NEW) | Low | rm scripts/ocr_ground_truth_eval.py |
| scripts/generate_golden_set_enhanced.py | Enhanced golden set (NEW) | Low | rm scripts/generate_golden_set_enhanced.py |
| scripts/automated_regression.py | Security test (NEW) | Low | rm scripts/automated_regression.py |
| scripts/run_search_eval.py | Precision@1 metric | Low | git checkout HEAD~1 -- scripts/run_search_eval.py |
| docs/stabilization/* | Reports and baselines (NEW) | Low | rm docs/stabilization/* |

## Rollback

Full rollback: `git reset --hard a5be7ef3` (pre-remediation baseline)
Partial rollback: `git checkout HEAD~N -- <file>`

---

**Status: PATCH MANIFEST COMPLETE**
