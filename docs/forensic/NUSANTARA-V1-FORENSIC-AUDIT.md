# NUSANTARA V1 FORENSIC AUDIT

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17
**Repository:** C:\Users\dmaza\mcp-starter
**Branch:** codex/fullroot-control-20261007
**HEAD:** d101fc4a

---

## 1. Repository Inventory

- **Total tracked files:** 1675
- **Python files:** 10602 (includes .venv)
- **Test files:** 161
- **App modules:** 34 (action, api, approval, context, core, devcore, developer_core, evaluation, execution, experience, governance, handoff, hermes, improvement, knowledge, language, mcp, memory, models, observability, orchestration, policy, problem, rag, reasoning, research, runtime, security, skills, tools, trust, ui, v2, workflow)
- **Database:** SQLite, 55.3 MB, 9 tables
- **Source documents:** 60 files, 54.6 MB

## 2. Architecture Map

### Entry Points
- **Backend:** app/main.py → FastAPI + Uvicorn (port 8000)
- **Frontend:** control-plane/src/main.tsx → React + Vite (port 5180)
- **Knowledge:** app/knowledge/engine.py → KnowledgeEngine (RAG + SQLite)
- **Hermes:** app/hermes/agent.py → HermesAgent (chat orchestration)

### Data Flow
```
User → Frontend (5180) → Backend API (8000) → Hermes → Knowledge Engine → RAG (SQLite) → Ollama (11434)
```

### Key Modules
| Module | Purpose | Status |
|---|---|---|
| app/knowledge/engine.py | Knowledge Engine facade | ✅ Active |
| app/knowledge/rag.py | RAG retrieval (hybrid semantic+lexical) | ✅ Active |
| app/knowledge/sop_review.py | SOP review/approval governance | ✅ Active |
| app/knowledge/grounding.py | Evidence grounding guard | ✅ Active |
| app/knowledge/chunker.py | Structure-aware chunking | ✅ Active |
| app/knowledge/docling_worker.py | Docling OCR extraction | ✅ Active |
| app/knowledge/docling_layout.py | Activity grid detection | ✅ Active |
| app/hermes/agent.py | Hermes chat orchestration | ✅ Active |
| app/api/routes.py | FastAPI routes | ✅ Active |
| app/security/v1_knowledge.py | V1 knowledge boundary | ✅ Active |
| app/models/ollama.py | Ollama provider | ✅ Active |
| app/models/openrouter.py | OpenRouter provider | ✅ Available (not configured) |

## 3. Database Schema

| Table | Rows | Purpose |
|---|---|---|
| documents | 64 | Document metadata and content |
| chunks | 721 | Vector store chunks with embeddings |
| knowledge_pipeline_runs | 175 | Pipeline audit trail |
| knowledge_pipeline_config | 1 | Watch folder config |
| sop_review_events | 719 | SOP review decisions |
| sop_review_trials | 148 | Chat trial results |
| sop_review_sessions | 56 | Session bindings |
| sop_review_pilots | 14 | Pilot document registry |
| document_extractions | 193 | Docling extraction results |

## 4. Knowledge/RAG Forensics

### Document Inventory
- 64 documents total
- 44 SOP documents (CAPIL, DAFDUK, PIAK, PERMOHONAN)
- 43 Aktif (approved and indexed)
- 1 Ditolak (PIAK-03 RAG test, deliberately rejected)
- 20 non-SOP documents (test files, audit.txt, etc.)

### Retrieval Pipeline
- Hybrid: 0.50 semantic (IndoBERT 768D) + 0.50 lexical (token overlap)
- Noise filter: score >= 0.50
- Document-level grouping: best chunk per document
- Title boost: +0.40 for exact title match
- RAG relevance gate: min_score=0.35, relative=0.65

### Chunking
- Structure-aware: preserves sentence/paragraph/table boundaries
- No overlap prepending (chunks match source text)
- Chunk size: 512, overlap: 64

### Known Issues
1. Search threshold (0.50) may be too high for some queries
2. Title boost not sufficient for OCR-garbled titles
3. Chunker doesn't track source positions (start_char computed from chunk, not source)

## 5. Security Forensics

### Authentication
- Admin token: shared (NUSANTARA_ADMIN_TOKEN)
- Mechanism: hmac.compare_digest (fail-closed)
- Source: .env file or environment variable

### Authorization
- Operator-only document chat: DOCUMENT_CHAT_REQUIRES_OPERATOR
- Operator-only model control: Model dikendalikan operator
- No auto-approval: explicit operator action required
- Session binding: prevents document/version switching
- Pilot gating: is_pilot() gates unapproved SOPs

### Known Issues
1. Shared admin token (no individual identity)
2. No rate limiting per user
3. No penetration testing
4. No path traversal test

## 6. Runtime Forensics

### Services
| Service | Port | Status |
|---|---|---|
| Backend (FastAPI) | 8000 | Running |
| Frontend (Vite) | 5180 | Running |
| Ollama (gemma3n 2B) | 11434 | Running |

### Model Provider
- Current: Ollama (gemma3n:e2b-it-q4_K_M, 2B)
- OpenRouter: Available but not configured (no API key)
- Feature flags: NUS_LANGCHAIN_ENABLED=false, NUS_LANGGRAPH_ENABLED=false

### Known Issues
1. Ollama model (2B) too small for grounded answers
2. Cannot download 7B+ models (no internet in sandbox)
3. IndoBERT worker unreliable (memory issues)

## 7. Control Plane (R1-R21)

Control Plane is implemented in control-plane/ (React + Vite).

**CORRECTION (2026-11-17 continuation, live evidence):** The earlier claim "R1-R21 mapped to technical controls, AC1-AC15 mapped to acceptance criteria" OVERSTATES the implementation. The actual runtime registry in `app/core/control_plane_projection.py:75-82` defines only **6 phases**: R1 (Configuration Intelligence), R2 (Provider/Model Runtime Identity), R3 (Effective RAG Profile), R4 (Embedding/Index Compatibility), R5 (Runtime Enforcement), MDE10 (Master Developer Engine). The master command `docs/commands/MDA-MASTER-R1-MDE10-001.md` defines R1–R6 + MDE10. There is NO literal 21-item R registry in code; "R1–R21" is a PRD/contract label (see `control-plane/src/operator.tsx:130` TechnicalPage header "Detail Teknis R1–R21" which renders the 6-phase projection).

Live `GET /v1/control-plane/snapshot` (HEAD de5dc52b) returns:
- phases: R1=UNKNOWN, R2=NOT_VERIFIED, R3=R3_IMPLEMENTATION_PASS_WITH_CONDITIONS, R4=LOCKED, R5=LOCKED, MDE10=NOT_AUTHORIZED
- gates: 14 (R3.1–R3.14)
- verification: focused=PASS, regression=PASS, query-parity=PASS (FIXTURE/historical evidence, not live attestation)
- warnings: r1/r2/r2-owner/r2-runtime evidence files FileNotFoundError (`.dev/MDA_R1_*`, `.dev/MDA_R2_*` missing)

**AC1–AC15:** The only literal AC-01..AC-15 list is the service/startup acceptance registry in `docs/operational/NUSANTARA-V1-AUTOSTART-REPORT.md` (ports, listeners, chat, autostart) — NOT product acceptance criteria. Product human acceptance is `control-plane/src/acceptance.ts` (8 humanCases + 5 stages System/Evidence/Test/Review/Decision), which is not numbered AC1-AC15. See finding F-14.

## 8. Code Quality

- 10602 Python files (includes .venv)
- 161 test files
- 34 app modules
- No circular dependencies detected
- Error handling: try/except in most critical paths
- Logging: structured logging with request_id, session_id, execution_id

## 9. Findings Summary

| ID | Finding | Risk | Status |
|---|---|---|---|
| F-01 | Chat abstains on all queries (LLM too small) | High | OPEN |
| F-02 | Precision@5 below target (0.3478 vs 0.50) | Medium | OPEN (metric limitation) |
| F-03 | LangGraph SOP workflow has stub nodes | Medium | PARTIAL (extract + others implemented) |
| F-04 | OCR ground truth not available | Medium | OPEN |
| F-05 | 5 test failures (environment) | Low | OPEN (environment issue) |
| F-06 | Grounding guard doesn't check negation | High | OPEN |
| F-07 | valid_chat_session too loose | Medium | FIXED (restricted to safe chars) |
| F-08 | Metadata reports 70/30 but actual is 50/50 | Low | FIXED (metadata updated) |
| F-09 | is_pilot excludes UNVERIFIED docs | High | FIXED (pipeline metadata check) |
| F-10 | Citation pages lost (chunker overlap) | Medium | FIXED (no overlap prepending) |
| F-11 | Hermes fallback self-validation | High | FIXED (source self-validation prevented) |
| F-12 | Search candidate window too narrow | Medium | FIXED (widened 4x) |

## 10. Recommendations

1. **Immediate:** Obtain 7B+ model (download manually outside sandbox)
2. **Short-term:** Implement remaining LangGraph stubs
3. **Medium-term:** Create OCR ground truth (manual transcription)
4. **Long-term:** Add negation check to grounding guard (requires contract approval)

---

## 11. Continuation Audit — 2026-11-17 (READ-ONLY, HEAD de5dc52b)

Baseline: branch `codex/fullroot-control-20261007`, HEAD `de5dc52b` (3 commits ahead of prior audit baseline d101fc4a: docs deliverables, grounding fail-closed echo fix d860c241, acceptance report 6261f998). Working tree has untracked files (scripts, docs/audit, service/, .venv-laya, nusantara-models). Services live: backend 8000, frontend 5180, Ollama 11434.

### 11.1 Browser E2E (FR-08) — CONFIRMED working (was NOT TESTED)
- Browser (in-app) renders AI Workspace at http://127.0.0.1:5180/.
- Chat question "Apa itu KTP-el dan apa fungsinya?" → natural correct answer from gemma3n:e2b-it-q4_K_M via ollama.
- Network log: `POST /v1/chat → 200 (application/x-ndjson)` via 5180→8000 proxy; `GET /v1/control-plane/model-status → 200`; `GET /v1/chat/history → 200`. Real backend, NOT mock.
- Answer detail panel shows honest runtime metadata: model, Jalur=ollama, Latensi=45372ms, timestamp, and label "Jawaban percakapan; tidak dinilai sebagai validasi dokumen resmi."
- Evidence: `evidence/browser-01-home-20261117.png`, `evidence/browser-02-chat-response-20261117.png`, `evidence/browser-chat-multiturn-20261117.json`.

### 11.2 Multi-turn conversation (FR-01) — context resolution CONFIRMED (2 turns; 10-message PASS criterion NOT fully executed)
- Turn 2 follow-up "Apa kepanjangan dari singkatan yang kamu sebutkan tadi?" correctly resolved "singkatan ... tadi" to KTP-el from turn 1. Answer: "KTP-el adalah singkatan dari Kartu Tanda Penduduk elektronik."
- Session continuity: same session_id across 4 context messages; both turns status=SUCCEEDED. Latency 45372ms / 10951ms.
- Both turns honestly labeled grounding grounded=false reason=not_evaluated, intent=ask_general_info, evidence_count=0 (general chat not grounded in official SOP).
- Persisted to `data/knowledge/chat-history/v1-chat-473fe2f4....json` (FR-04 persistence confirmed).
- Status: PARTIAL toward FR-01 full PASS (needs 10 sequential messages + topic-switch test); core follow-up/reference capability CONFIRMED.

### 11.3 Security probes (S-03/S-04) — non-destructive, TESTED
| Probe | Result | Verdict |
|---|---|---|
| Privileged source/detail without token | 403 "admin token diperlukan" | fail-closed CONFIRMED |
| Valid source with token | 200 PDF 462551 bytes | baseline OK |
| Path traversal (5 payloads: single/double-encoded, backslash) | 404 (routing or DB-key lookup) | protection CONFIRMED |
| SQL injection `' OR 1=1; DROP TABLE documents;--` | 200 empty results; DB intact (64 docs, 9 tables) | parameterized CONFIRMED |
| Citation session `../evil` | 403 CHAT_SESSION_CAPABILITY_REQUIRED | session validation CONFIRMED |
| Secret leakage in snapshot/model-status/health-detail | none | CONFIRMED |
| Search semantic query (normal) | TimeoutError 25s | IndoBERT worker slow (perf, known F-05) |

- `source()` defense-in-depth confirmed at `app/knowledge/sop_review.py:112-130`: document_id is a DB key (not a path), symlink rejection, resolved-parent==source-documents containment, SHA-256 integrity, 20MB cap.
- S-04 upgraded OPEN→TESTED/CONFIRMED. S-03: targeted manual probes done; full OWASP ZAP/Burp scan NOT performed → PARTIAL.

### 11.4 Recovery (FR-10) — mechanism PROVEN, live backup STALE
- Safe backup→restore round-trip of CURRENT live DB in temp: integrity_check=ok, 64 docs/721 chunks, backup==restored SHA-256 match. Temp cleaned. Production untouched.
- Existing on-disk live-DB backup `data/knowledge/nusantara_knowledge.sqlite.backup` (Oct 22, 274KB) is STALE: 21 docs/45 chunks vs live 64/721. Restoring it would lose ~67% of documents / ~94% of chunks.
- Legacy `production_knowledge.db` has multiple backups (Oct 1-2) but is a different/legacy DB, not the live one.
- FR-10: PARTIAL (restore mechanism works; NO current backup of live data). See F-13.

### 11.5 New findings
| ID | Finding | Risk | Status |
|---|---|---|---|
| F-13 | Live-DB backup stale (Oct 22: 21 docs/45 chunks vs live 64/721); restore would lose most data | High | OPEN |
| F-14 | R1–R21/AC1–AC15 mapping overstated; actual registry R1–R5+MDE10 (6 phases)+R3.1–R3.14; AC-01..15 only autostart criteria; R1/R2 evidence files missing | Medium | OPEN (doc/registry gap) |
| S-09 | Raw exception interpolated into HTTP 500 detail at routes.py:1424,1510,1561 (contradicts "generic error messages"); info-disclosure risk | Low | OPEN |
| F-15 | Chat latency high (45.4s turn1, 11s turn2); search semantic timeout 25s (IndoBERT worker) | Medium | OPEN (perf) |
| F-16 | Doc says model 2B; Ollama reports gemma3n:e2b parameter_size=4.5B (e2b=2B active/4.5B total) | Low | DOC CORRECTION |

### 11.6 Model identity correction
Ollama `/api/tags` reports gemma3n:e2b-it-q4_K_M `parameter_size: 4.5B` (effective-2B active, 4.5B total). Prior docs state "2B". Corrected here; does not change the abstention finding (F-01) for SOP-grounded answers.

---

**Status: FORENSIC AUDIT COMPLETE + CONTINUATION (read-only) 2026-11-17.**

**Next step: Awaiting operator approval for remediation phase. New remediation candidates: F-13 (current backup), F-14 (R/AC registry honesty), S-09 (generic error messages), F-15 (performance).**
