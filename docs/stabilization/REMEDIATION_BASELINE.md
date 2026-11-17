# REMEDIATION BASELINE

**Contract:** NUS-V1-REMEDIATION-001
**Date:** 2026-11-17
**Repository:** C:\Users\dmaza\mcp-starter
**Branch:** codex/fullroot-control-20261007
**HEAD:** 5f0197909ff3a22655888941302a22336660a9d2
**Tag:** v1-stab-baseline

---

## 1. Git Status

- Branch: codex/fullroot-control-20261007
- HEAD: 5f019790 (feat: SOP field extractor)
- Working tree: clean (no uncommitted tracked changes)
- Untracked: .venv-laya/, docs/audit/, nusantara-models/, output/, scripts/Audit-SOP.ps1, service/, Modelfile, where, whoami

## 2. Service Status

| Service | Port | Status |
|---|---|---|
| Backend (FastAPI) | 8000 | Running |
| Frontend (Vite) | 5180 | Running |
| Ollama (gemma3n 2B) | 11434 | Running |

## 3. Database

- Path: data/knowledge/nusantara_knowledge.db
- Documents: 65
- Chunks: 722
- SOP total: 44
- SOP Aktif: 43
- SOP Ditolak: 1 (PIAK-03 RAG test)

## 4. Test Baseline

- test_knowledge_pipeline: 5 passed
- test_sop_review: 13 passed
- test_langgraph_workflow: 4 passed
- test_langchain_adapter: 4 passed
- test_langchain_hardening: 13 passed
- Total: 39 passed, 0 failed

## 5. Search Metrics

- Recall@5: 0.8278
- MRR@10: 0.6377 (from 160-query eval)
- Precision@1: 0.55
- Precision@5: 0.265
- Exact_match: 0.55

## 6. Known Issues (from audit)

1. Chat abstains (LLM too small) — F-01
2. Precision@5 below target — F-02
3. LangGraph SOP workflow has stubs — F-03 (partially fixed)
4. OCR ground truth not available — F-04
5. 5 test failures (environment) — F-05
6. Grounding guard doesn't check negation — FIXED (S-05)
7. valid_chat_session too loose — FIXED (S-01 related)
8. Metadata reports 70/30 but actual is 50/50 — FIXED
9. is_pilot excludes UNVERIFIED docs — FIXED
10. Citation pages lost — FIXED
11. Hermes fallback self-validation — FIXED
12. Search candidate window too narrow — FIXED

## 7. Backup Status

- Latest backup: backups/nusantara_knowledge_20261117_105754.db
- SHA-256: 288f4e802fb8fc8741029a2535acff1acf21f146e3c9dae52be5d499130d3086
- Documents: 64, Chunks: 721
- Restore verified: PASS

## 8. Remediation Priority

P0: Backup & Restore (DONE)
P1: F-01 Chat, F-02 RAG, F-03 LangGraph, Hermes integration
P2: F-14 Registry, S-09 Error handling, S-03/S-04 Security
P3: F-04 OCR, F-05/F-15 Performance, F-06 Grounding, F-16 Model ID
P4: 42 SOP regression, Hermes validation
P5: Hardening, performance, recovery, documentation

---

**Status: T0 COMPLETE**

**Next step: Awaiting operator approval for remediation.**
