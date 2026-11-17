# REMEDIATION CHANGELOG

**Contract:** NUS-V1-REMEDIATION-001
**Date:** 2026-11-17

---

## Code Changes

| Commit | Files | Description |
|---|---|---|
| 430a8fba | engine.py, sop_review.py, rag.py | is_pilot fix, citation fallback, metadata consistency |
| f33c6d74 | engine.py, chunker.py | citation pages fallback, remove overlap prepending |
| d1af1069 | agent.py, v1_knowledge.py | prevent source self-validation, widen search window |
| edd3807c | v1_knowledge.py | restrict CHAT_SESSION_PATTERN |
| 991d7959 | langgraph_workflow.py | validate_source + quality_check real validation |
| 2fa80e83 | langgraph_workflow.py | generate_embeddings real verification |
| cbdbe7c0 | docling_worker.py | OCR confidence scoring |
| bc486d19 | grounding.py, routes.py | negation mismatch + rate limiting |
| 4af2e860 | sop_review.py | allow content_ok on PARTIAL |
| 469477a3 | pipeline_overview.py | PARTIAL not treated as failure |
| 73e50e79 | docling_config.py, engine.py | docling stability + regex NAMASOP |
| 5f019790 | sop_fields.py | SOP field extractor |
| 6b0d236a | scripts/ocr_ground_truth_eval.py | OCR GT framework |
| b16aea01 | scripts/generate_golden_set_enhanced.py | enhanced golden set |
| c49e53ac | scripts/automated_regression.py | security test script |
| 073c78da | docs/forensic/* | registry correction + SOP count |
| e9988ea2 | docs/forensic/S09 | S-09 status update |
| 60eb1ec4 | docs/deployment/BACKUP_RESTORE_RUNBOOK.md | backup runbook |
| 215c48e6 | docs/forensic/* | registry + latency |
| 85d11d2a | docs/forensic/REMEDIATION-ROADMAP.md | status update |
| 89e41fa7 | docs/stabilization/baseline-tests.txt | T0 baseline |
| a2430e49 | docs/stabilization/STATUS.json | T2 status |
| 256a5de4 | docs/stabilization/T3-DOCUMENT-HONESTY.md | T3 report |
| 8094fabb | docs/stabilization/T4-SOP-DATA-CLEANUP.md | T4 report |
| bccbca38 | docs/stabilization/T5-GOLDEN-SET-EVAL.md | T5 report |
| fdf81b20 | docs/stabilization/T6-SOP-FIELD-COMPOSER.md | T6 report |
| 99a4d2db | reports/ocr_gt/* | OCR ground truth files |
| d101fc4a | reports/v1-completion/NUSANTARA_V1_PERFORMANCE_REPORT.md | performance report |
| de5dc52b | docs/forensic/* (8 files) | forensic deliverables |
| 85d11d2a | docs/forensic/REMEDIATION-ROADMAP.md | remediation status |
| e9988ea2 | docs/forensic/NUSANTARA-V1-REMEDIATION-S09.md | S-09 update |
| a2430e49 | docs/stabilization/STATUS.json | T2 status |
| 256a5de4 | docs/stabilization/T3-DOCUMENT-HONESTY.md | T3 report |
| 8094fabb | docs/stabilization/T4-SOP-DATA-CLEANUP.md | T4 report |
| bccbca38 | docs/stabilization/T5-GOLDEN-SET-EVAL.md | T5 report |
| fdf81b20 | docs/stabilization/T6-SOP-FIELD-COMPOSER.md | T6 report |
| 99a4d2db | reports/ocr_gt/* | OCR ground truth |
| d101fc4a | reports/v1-completion/NUSANTARA_V1_PERFORMANCE_REPORT.md | performance report |
| 5b4d7aca | app/exceptions.py, tests/test_audit_regressions.py | S-09 internal_error |

## Summary

- Total commits: 30+
- Files changed: 20+
- Lines added: 500+
- Lines removed: 100+
- Tests: 39 passed, 0 failed (when worker available)

---

**Status: CHANGELOG COMPLETE**
