# SOP Operator Review & Approval Report

## Current Workflow Audit

### SOPReview Backend (`app/knowledge/sop_review.py`)
- **Methods:** bind_session, confirm_metadata, decide, detail, enroll, evidence, extracted_version, is_pilot, rate, record_trial, session_binding, source
- **Actions:** content_ok, problem, resolve, approve, reject, defer, revoke
- **Statuses:** Menunggu ekstraksi → Menunggu pemeriksaan isi → Menunggu metadata resmi → Siap disetujui → Aktif / Ditolak / Ditunda / Dicabut
- **Governance:** approve checks can_approve, prevents duplicate approval, checks conflicting active versions, records trial_binding and review_binding
- **Audit trail:** events table with kind, payload, principal, created_at
- **Version history:** source_version, extraction version, metadata event
- **Access control:** V1KnowledgeBoundary filters by operator flag and approval status

### Document Extraction Pipeline
- Upload → process_knowledge_source (chunking + embedding + index)
- Docling OCR (worker subprocess, Tesseract ind+eng, PSM=6)
- Table normalization (normalize_activity_grids, ruled_grid_pipeline)
- Haystack cleaning (conservative, text blocks only)
- Metadata extraction (SOPMetadata with official fields)
- Review detail (extraction status, blocks, comparison)

### Metadata Validation
- SOPMetadata with official_title, institution, unit, sop_number, jurisdiction, issued_on, effective_on, expires_on, revision
- Status: present/not_stated/unreadable
- Validation: required fields, date format, publication_allowed()

### Knowledge Indexing
- SQLiteVectorStore, idempotent (DUPLICATE on same hash)
- Chunking: 512 chars, 64 overlap (structure-aware)
- Embedding: IndoBERT 768D via worker
- Access: V1KnowledgeBoundary filters by operator + approval status

### Operator Authorization
- require_admin(x_admin_token) — token-based
- V1KnowledgeBoundary — operator flag + provider check
- Session binding — prevents document/version switching

### Approval & Version History
- decide() with BEGIN IMMEDIATE transaction
- approve checks: can_approve, not already Aktif, no conflicting active version
- trial_binding and review_binding recorded
- approval_current check (trial_binding == review_binding)
- publication_decision tracks approve/reject/defer/revoke

## Changed Files
- No code changes in this session (governance already implemented)
- Report: `reports/langchain-langgraph/sop-operator-review-report.md`

## Status Transition Diagram
```
Upload → PROCESSING → Menunggu ekstraksi
  → (Docling complete) → Menunggu pemeriksaan isi
  → (content_ok) → Menunggu metadata resmi
  → (metadata confirmed) → Siap disetujui
  → (approve) → Aktif
  → (reject/defer/revoke) → Ditolak/Ditunda/Dicabut
```

## Test Commands and Results
```
pytest tests/test_sop_review.py -q
```
Result: **13 passed, 86 warnings** (9.75s)

Tests cover:
- Approval without manual trials activates chat and survives restart
- Review changes invalidate approval and survive restart
- Operator can activate SOP without manual chat trials
- Problem requires note and cannot inherit approval
- Session cannot switch document or version
- Pilot is private to trial before first human decision
- Publication decision blocks retrieval and cached answer
- Unapproved document cannot be revoked
- Content check event persists with optional trial_id
- Deferred document stays blocked after reload
- Correction retains category/question/answer/revision/resolution

## Security and Authorization Observations
- Operator token required for all review/approval actions
- Public (no token) → search returns 403, chat returns 0 evidence
- V1KnowledgeBoundary enforces operator flag at retrieval time
- Session binding prevents document/version switching
- Approval history preserved in SQLite events table
- No auto-approval (explicit operator action required)
- Conflicting active versions detected and blocked

## Remaining Blockers
- None identified. Governance is comprehensive and tested.

## Rollback Instructions
- No changes made in this session. No rollback needed.
- If future changes break governance, revert to commit `a15269ac` (before this contract).

## Acceptance: PASS
Operator approval is authorized (token), auditable (events table), reversible (revoke/defer), and supported by verified source and Knowledge evidence.
PY