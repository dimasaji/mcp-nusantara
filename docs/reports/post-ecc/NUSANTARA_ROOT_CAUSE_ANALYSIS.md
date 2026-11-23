# Nusantara Root Cause Analysis

Contract: `NUS-V1-POST-ECC-001`

Scope: Nusantara V1 only

Date: 2026-11-22

HEAD: `35efdd382405442a3aabe0e05b112f47a2ff3603`

## 1. Evidence standard

A cause is marked **PROVEN** only when supported by a passing/failing test, source code, or an observed command result in this contract. A cause is marked **HYPOTHESIS** when it is plausible but cannot be confirmed without production data, a real model, or missing artifacts.

## 2. SOP aktif tetapi tidak ditemukan di Chat

### PROVEN: publication eligibility blocks retrieval before scoring

`app/security/v1_knowledge.py:147-166` enforces three gates before normal retrieval:

- no operator means `return []` (`:141-142`);
- provider other than `ollama` raises `409` (`:143-144`);
- a pilot SOP whose review status is not `Aktif` returns `[]` unless this is a review trial (`:149-153`);
- general document eligibility excludes pilot documents that are not `Aktif` (`:163-166`).

Impact: a document that exists in the catalog but is not published as `Aktif` cannot appear in chat evidence. This is deterministic and matches the contract’s publication-boundary design; it is not a random retrieval miss.

### PROVEN: the current VPS cannot complete the HTTP knowledge path

`nusantara-models/.venv/bin/python` is missing and IndoBERT HTTP ingest/search was already recorded as blocked in the ECC report. The current check confirms `indobert_worker=MISSING`.

### HYPOTHESIS: stale active version in a specific deployment

If a document is truly `Aktif` in production yet still missing from chat, the remaining candidates are stale review version binding, stale index state, or an operator/provider context mismatch. This cannot be proven from the VPS fixture suite because production SOP state was not provided.

## 3. Retrieval mengembalikan dokumen yang salah

### PROVEN: public score and internal ranking score were conflated

Before the post-ECC fix, `app/knowledge/engine.py` mutated `Evidence.score` with keyword/title boosts. The V1 boundary then sorted on that boosted score while consumers applied a separate `0.50` gate to the same field. This made relevance ordering and evidence acceptance disagree.

Current implementation separates the concepts:

- `Evidence.score` remains the canonical/base score;
- `metadata['retrieval_rank_score']` carries boost ranking;
- `app/security/v1_knowledge.py:180-183` sorts on `retrieval_rank_score` with `hybrid_score` tie-break.

Evidence: the two previously failing tests `test_facade_list_contract_filter_rejected_and_receipt` and `test_actual_v1_chat_retrieval_and_filter_block` now pass.

### PROVEN: hard post-filter in the retrieval engine removed valid V1 evidence

The engine previously filtered evidence at `>= 0.50` before the V1 consumer gate, so chunks accepted by the canonical profile could disappear before grounding. The hard filter was removed while the V1 consumer gate remains.

### PROVEN: batch sorting preserves exact-title matches

`app/security/v1_knowledge.py:171-183` requests a wider candidate window per 20-document batch and then sorts globally. This prevents batch order from deciding which exact-title match survives `top_k`.

### OPEN: top-k contract conflict remains

`tests/test_configuration_integration.py::test_rag_actual_query_and_ingestion_use_config` still expects 3 document-level results where current bounded `top_k=3` grouping returns 1. This is a contract decision, not proof of another retrieval defect.

## 4. Jawaban tidak sesuai sumber

### PROVEN: raw-source recovery was too permissive

Before the fix, `app/hermes/agent.py` could replace a failed model answer with the first validated source string for non-pilot chats and multiline requirement lists. That produced unsupported or truncated answers.

Current behavior restricts raw-source recovery to:

- `pilot_chat`;
- single-line source (`'\n' not in _src`);
- a source string that passes `EvidenceGroundingGuard.validate`.

Otherwise the agent returns a scoped abstention. Evidence: all three `tests/test_chat_source_recovery.py` failures are fixed and remain passing.

### PROVEN: service facts use a fixed source scope

`app/hermes/agent.py:812-857` fixes topic, document ID, and title before generation and validates both the model rewrite and the evidence fallback through `validate_service_rewrite`. This is a defense-in-depth layer, but it cannot be verified end-to-end without Ollama.

## 5. Sitasi tidak mendukung jawaban

### PROVEN: contextual reuse fails closed on real rebind denial

`app/hermes/agent.py:859-914` rebinds the prior citation through `reuse_prior_citation`. A real `HTTPException 409` now produces:

- no citation evidence;
- `provider_status=local_rule`;
- scoped abstention.

Evidence: `test_reuse_fails_closed_when_source_cannot_be_rebound` passes.

### PROVEN: fallback for missing boundary method is limited to test-double compatibility

When the knowledge object has no `reuse_prior_citation` method at all, the current code reuses the already-grounded snapshot text for simplification follow-ups. This preserves `test_selected_document_followup_keeps_filter_and_retrieval_context` without weakening the real 409 fail-closed path.

### OPEN: OCR-derived citation text can still be malformed

NBSP and NUL characters survive cleaning, so page-derived quotes can differ from normalized user-facing text. See section 7.

## 6. Pertanyaan lanjutan kehilangan konteks

### PROVEN: follow-up context is memory-based and scope-bound

The contextual branch requires all of:

- `previous['last_answer']`;
- scoped `document_ids`;
- `_contextual_scope_followup`;
- a citation or simplification request pattern.

It reuses the prior grounded answer rather than asking the model to invent a new one. The regression guards for both reuse and fail-closed behavior pass.

### HYPOTHESIS: context loss outside these patterns

Follow-ups that do not match citation/simplification patterns depend on normal retrieval plus provider availability. With Ollama and IndoBERT unavailable, their behavior cannot be proven on this VPS.

## 7. Pipeline OCR menghasilkan teks rusak

### PROVEN: cleaner does not normalize NBSP or NUL

`app/knowledge/text_cleaning.py:18-22` configures Haystack with:

```python
replace_regexes={r'(?<=\S)[ \t]{2,}(?=\S)': ' '}
```

This only targets repeated ASCII spaces/tabs. The fixture in `tests/test_knowledge_preparation.py:23` contains `Surat\u00a0Permohonan\x00`, and the full regression output shows the cleaned source still contains `Surat\xa0Permohonan\x00`.

Impact:

- requirement statements break token matching;
- citations contain invisible characters;
- markdown/table comparisons diverge;
- downstream LLM prompts receive polluted evidence.

Recommended minimal fix: add conservative normalization for `\u00a0` to a normal space and `\x00` to removal or a single space before the existing Haystack cleaning step, then re-run the four affected ingestion tests.

## 8. Perbedaan Control Plane dan Chat utama

### PROVEN: Control Plane is pinned to archived evidence, Chat is runtime-driven

`app/core/control_plane_projection.py:48-65` reads pinned files from `.dev/` and `docs/reports/`, including the missing R2 owner acceptance record. Frontend tests read archived JSON files directly and currently fail with `ENOENT`.

By contrast, chat retrieval uses the live knowledge engine and boundary. Therefore a Control Plane PASS cannot prove chat correctness, and a chat fixture PASS cannot repair missing Control Plane evidence.

### PROVEN: missing historical artifacts are release blockers

`FINAL_OWNER_ACCEPTANCE_RECORD.json`, `REMAINING_GATES.json`, `IMPLEMENTATION_REPORT.json`, and `OWNER_DECISION.json` paths are referenced by tests or projection code but are absent. This explains the Control Plane/test failures without implying a new V1 regression.

## 9. Root-cause priority

1. **Environment blockers**: IndoBERT worker and Ollama are unavailable, so real SOP chat E2E cannot be verified.
2. **Release evidence blockers**: R2 owner acceptance, checksum gating, Windows attestation, and archived report paths are missing or unverifiable.
3. **Knowledge quality**: OCR NBSP/NUL normalization is incomplete.
4. **Contract ambiguity**: top-k/baseline fixture conflict remains.
5. **Maintainability**: duplicated RAG constants and frontend test stability remain secondary risks.

Items 1–3 directly affect the mission’s focus on reliable SOP Knowledge and must be resolved before any claim of V1 readiness.
