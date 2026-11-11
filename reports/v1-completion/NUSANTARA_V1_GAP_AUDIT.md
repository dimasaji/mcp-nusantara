# NUSANTARA V1 GAP AUDIT REPORT

**Contract:** NUSANTARA-V1-MASTER-2026-001
**Phase:** 0 — Safe Baseline Audit
**Date:** 2026-11-11
**Branch:** codex/fullroot-control-20261007
**HEAD:** 240e40ef
**Git Remote:** https://github.com/dimasaji/mcp-nusantara.git

---

## 1. Baseline Verification

### Git Status
- Branch: `codex/fullroot-control-20261007`
- HEAD: `240e40ef docs: operator acceptance report (35/64 Aktif, PASS for tested scope)`
- Upstream: `origin/codex/fullroot-control-20261007` (up to date)
- Untracked: `.knowledge-green/`, `.knowledge-red/`, `.knowledge-red2/`, `Audit-SOP.ps1`, `docs/audit/`, `nusantara-models/`, `output/`, `scripts/Audit-SOP.ps1`, `scripts/run_search_eval.py`, `service/`, `test.txt`, `tmp*`
- No uncommitted tracked changes

### Runtime Status
- Backend: `127.0.0.1:8000` LISTENING (PID 12532)
- Frontend: `127.0.0.1:5180` LISTENING (PID 8428)
- Ollama: `127.0.0.1:11434` LISTENING (PID 3704)
- Ollama models: `gemma3n:e2b-it-q4_K_M` (7.8GB), `tinyllama:latest` (637MB), `llama3.2:1b` (1.3GB)
- Ollama ps: no model loaded in memory (idle)
- Port 8765, 18765: NOT LISTENING (not applicable)

### Configuration
- LLM provider: `ollama`
- LLM model: `llama3.2:1b`
- Knowledge DB: `C:\Users\dmaza\mcp-starter\data\knowledge\nusantara_knowledge.db`
- Embedding: IndoBERT (768D via worker process)

### Database
- Documents: 64
- Pipeline READY: 53
- SOP summary total: 64
- SOP counts: ACTIVE=35, QUEUED=0, PROCESSING=0, REVIEW_REQUIRED=12, APPROVAL_REQUIRED=0, BLOCKED=17, UNKNOWN=0

---

## 2. Gap Analysis by Phase

### Phase 1 — Document Identity Integrity
**Status:** AUDIT COMPLETE, ROOT CAUSE IDENTIFIED (see NUSANTARA_V1_DOCUMENT_IDENTITY_REPORT.md)

**Finding:** DAFDUK_22.pdf has title "DAFDUK_22.pdf" (filename fallback) because OCR garbled "NAMA SOP" → "INO SOP", causing `_source_title` regex to fail. The source file is intact and matches the original. No metadata swap occurred. The "Penerbitan Biodata Bagi WNI melalui Website Sobat Dukcapil" title belongs to DAFDUK_21.pdf, a separate document.

**Root cause:** OCR quality on DAFDUK_22.pdf (scanned document). The "NAMA SOP" label was misread.

**Impact:** Low — document is still indexed and searchable, but its title is not human-readable. Does not affect citation or grounding.

**Fix required:** Re-process with improved OCR preprocessing, or manually set title. Requires operator approval.

### Phase 2 — RAG Quality
**Status:** PARTIAL
- Recall@5: 0.8278-0.9278 (varies with store size)
- Precision@5: 0.26-0.32 (target >0.50, NOT MET)
- MRR@10: 0.6659-0.7083
- 30 queries evaluated (target: 100+ queries with ground truth)
- Title boost (0.15) and body boost (0.05) applied
- Document-level grouping applied
- Noise filter (>=0.32) applied

**Gap:** Precision@5 below target. Need more representative queries and reranking improvements.

### Phase 3 — OCR Reliability
**Status:** PARTIAL
- PSM=6 configured
- Deskew + binarize preprocessing added to docling_worker.py
- Table structure options: cell_matching, accurate
- Timeout: 900s
- NOT validated on: clean scans, blurry scans, tilted scans, low contrast, low resolution
- No CER/WER/field accuracy measurements

**Gap:** No formal OCR accuracy report per quality category.

### Phase 4 — 42 SOP Batch Completion
**Status:** PARTIAL
- 35/64 Aktif (54.7%)
- 12 REVIEW_REQUIRED (content review pending)
- 17 BLOCKED (failed extraction, missing source, deferred, problems)
- 4 documents rated "Ada masalah" (operator: NOT OK)
- 5 documents missing source files
- 1 document deferred (CAPIL_03)
- 10 documents not yet extracted

**Gap:** 29 documents not Aktif. Need individual operator review for each.

### Phase 5 — Golden Set
**Status:** PARTIAL
- 64 Golden Set JSON files generated (in output/)
- Only 2 SOPs have detailed Golden Sets from generate_golden_set.py
- 30 queries evaluated (not 100+)
- No automated regression test for all SOPs

**Gap:** Golden Set not comprehensive for all 35 Aktif SOPs.

### Phase 6 — LangGraph Verification
**Status:** PARTIAL
- LangGraph workflow E2E tested (grounded=True, citations present)
- Feature flag default OFF
- Workflow nodes call real services (search_knowledge, provider.generate, grounding_guard.validate)
- NOT verified: all 7 nodes individually, error handling, retry, abstention in production

**Gap:** Need comprehensive node-by-node verification.

### Phase 7 — Performance
**Status:** PARTIAL
- 2 SOPs benchmarked: 132.3s total, 66.1s/SOP
- No 10-SOP batch benchmark
- No peak RAM/CPU measurement
- No concurrent request testing
- No P50/P95 latency documentation

**Gap:** Formal performance report missing.

### Phase 8 — Security & Cost Governance
**Status:** PARTIAL
- Admin token required for all review/approval
- Public (no token) → search 403, chat 0 evidence
- Audit trail: events table with kind, payload, principal, created_at
- No auto-approval
- Session binding prevents document/version switching
- NOT verified: path traversal, file size limits, secret handling, provider fallback, cost limits

**Gap:** Formal security test report missing.

### Phase 9 — Final Acceptance
**Status:** NOT STARTED
- No comprehensive E2E acceptance test run
- No formal PASS/FAIL/SKIP/BLOCKED report

---

## 3. Known Blockers

1. **Precision@5 = 0.26-0.32** (target >0.50) — metric definition limitation (Precision@5 = relevant/5, max theoretical 0.2-0.4 with 1-2 expected docs per query)
2. **OCR title extraction failure** on DAFDUK_22.pdf (and potentially others) — "NAMA SOP" label garbled
3. **5 documents missing source files** — need restore from E:/SOP/ or backup
4. **10 documents not yet extracted** — Docling OCR ~66s/SOP
5. **12 documents need content review** — operator action required
6. **4 documents have problems** — operator rated NOT OK
7. **1 document deferred** — CAPIL_03 (operator decision)
8. **OCR preprocessing not validated** on low-quality scans
9. **Golden Set not comprehensive** — only 2 SOPs with detailed sets
10. **Performance baseline not formal** — only 2 SOPs measured
11. **Security not formally tested** — no penetration test report
12. **LangGraph nodes not individually verified** in production

---

## 4. Deliverables Status

| Deliverable | Status |
|---|---|
| NUSANTARA_V1_GAP_AUDIT.md | CREATED (this file) |
| NUSANTARA_V1_DOCUMENT_IDENTITY_REPORT.md | PENDING |
| NUSANTARA_V1_RAG_EVALUATION.md | PENDING |
| NUSANTARA_V1_OCR_EVALUATION.md | PENDING |
| NUSANTARA_V1_SOP_BATCH_REPORT.md | PENDING |
| NUSANTARA_V1_GOLDEN_SET_REPORT.md | PENDING |
| NUSANTARA_V1_LANGGRAPH_VERIFICATION.md | PENDING |
| NUSANTARA_V1_PERFORMANCE_REPORT.md | PENDING |
| NUSANTARA_V1_SECURITY_REPORT.md | PENDING |
| NUSANTARA_V1_FINAL_ACCEPTANCE.md | PENDING |

---

## 5. Decision

**Phase 0 (Audit) is COMPLETE.**

No code, database, metadata, approval, or indexing changes were made during this audit.

**STOP. Awaiting operator approval before proceeding to Phase 1 (Document Identity) or any other phase.**

All findings above are based on actual repository and runtime evidence, not assumptions.
