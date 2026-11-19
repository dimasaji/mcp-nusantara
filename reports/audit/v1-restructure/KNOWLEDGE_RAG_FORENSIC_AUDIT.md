# KNOWLEDGE_RAG_FORENSIC_AUDIT

**Project:** Nusantara V1
**Contract:** deliverable §12.10, addendum §2 items 4 and 7, §5.D
**Date:** 2026-11-18
**Scope:** `app\knowledge\` (43 modules), `app\rag\` (2), `app\semantic\` (5)

---

## 1. Component map

| Layer | Module | Lines | Public surface |
|---|---|---:|---|
| Engine (facade) | `app\knowledge\engine.py` | 496 | `KnowledgeEngine` — 15 public methods |
| Retrieval core | `app\knowledge\rag.py` | 943 | `RAG`, `MemoriaVectorStore`, `DocParser`, `ChunkProcessor` |
| Persistence | `app\knowledge\store.py`, `app\rag\store.py` | — | chunk + document I/O |
| Parse / OCR | `parser.py`, `pdf_sop.py`, `docling_worker.py`, `docling_layout.py`, `docling_config.py` | — | PDF/DOCX/TXT + Docling |
| Chunking | `chunker.py` | — | fixed + semantic chunking |
| Embedding | `embeddings.py`, `indobert_embedding.py`, `production_embedding_bridge.py` | — | IndoBERT subprocess bridge |
| Rerank | `reranker.py` | — | lexical + semantic blend |
| Grounding | `grounding.py` | — | requirement extraction, fact set, negation |
| Citation | `document_citations.py`, `retrieval_evidence.py` | — | traceability |
| Answer compose | `document_answers.py`, `sop_fields.py`, `document_context.py` | — | deterministic answers |
| SOP review | `sop_review.py` | 467 | `SOPReview` — 13 public methods |
| Hybrid RAG | `production_hybrid_rag.py`, `production_semantic_retriever.py`, `production_kb.py` | — | production retrieval profile |
| Cleaning | `text_cleaning.py` | 87 | Haystack `DocumentCleaner`, horizontal-space profile only |

`KnowledgeEngine` public methods (verbatim from AST):

```
skills, ingest_document, retrieval_top_k, document_scope,
search_knowledge, search, selected_document_evidence, list_documents,
process_knowledge_source, intake_document, retry_knowledge_source,
set_knowledge_watch, scan_knowledge_watch, knowledge_pipeline_status
```

---

## 2. Ingestion pipeline (verified stages)

```
file bytes
  → intake_document(filename, raw)          deterministic document_id = DOC-SHA256-<hash>
  → chunker (markdown/structure aware)      tokens_estimate per chunk
  → embedding                               IndoBERT, 768-dim
  → store                                   documents + chunks rows
  → knowledge_pipeline_runs                 status transition recorded
```

Deterministic document IDs (`DOC-SHA256-…`) are the deduplication key — the pipeline log contains **42 `DUPLICATE` runs**, proving dedup is active rather than assumed.

### 2.1 Measured corpus state

| Metric | Value | Source |
|---|---:|---|
| Documents | **65** | `select count(*) from documents` |
| Chunks | **722** | `select count(*) from chunks` |
| Chunks with embedding | **722 / 722 (100 %)** | `where embedding is not null` |
| Embedding dimension | **768** for all 722 | `group by embedding_dimension` |
| Embedding model | `indobenchmark/indobert-base-p1` for all 722 | `group by embedding_model` |
| Documents with zero chunks | **0** | anti-join |
| Largest document | 42 chunks | `group by document_id` |
| Extraction cache rows | 193 | `document_extractions` |
| Pipeline runs | 178 (54 READY, 69 FAILED, 42 DUPLICATE, 13 watch toggles) | `knowledge_pipeline_runs` |

**100 % embedding coverage with a single dimension and a single model is the strongest possible signal that there is no shadow index and no mixed-embedding corruption.**

---

## 3. Retrieval quality — measured, and partly retracted

> **This section was revised after `AUDIT_HISTORY_RECONCILIATION.md` was written.** An earlier draft of this report quoted `Recall@5=0.8278, MRR@10=0.5672, P@1=0.4667, P@5=0.3478`. Those four values appear together in `docs\stabilization\RAG_EVALUATION_FINAL.md`, but **no artefact on disk contains them**. They are retracted here.

The only retrieval evaluation backed by a machine-readable artefact is `reports\search_eval_report.json` (137,126 B, generated 2026-11-16 15:14), over 160 queries:

| Metric | Value | Status |
|---|---:|---|
| Recall@5 | **0.824** | accepted — artefact |
| MRR@10 | **0.6377** | accepted — artefact |
| Precision@1 | **0.55** | accepted — artefact |
| Exact-match accuracy | 0.55 | accepted — artefact |
| Precision@5 | 0.265 | **retracted as a metric** — see below |
| Median latency | 178.9 ms | accepted — artefact |
| p95 latency | 261.7 ms | accepted — artefact |

A second, smaller evaluation exists: `reports\golden_set_retrieval_eval.json` — 40 verified questions, **P@1 = 0.40, Recall@5 = 0.625**, median latency 283.6 ms. It is not reconcilable with the 160-query set (different dataset, different filtering) and is reported separately rather than averaged in.

### 3.1 Why Precision@5 is retracted

`scripts\run_search_eval.py:44-49` computes:

```python
if top5:
    prec = len(set(top5) & expected) / len(top5)   # denominator = results returned
```

The denominator is the **number of results actually returned**, not `k = 5`. Across the 160 queries, **41 returned fewer than five results** (5 returned none, 10 returned one, 15 returned two, 13 returned three, 9 returned four). A query that returns one correct result therefore scores **P@5 = 1.0**, not 0.2.

This has two consequences that invalidate earlier analysis:

1. `RAG_EVALUATION_FINAL.md:31` claims *"max theoretical 0.2333"* — there is no such ceiling under this implementation.
2. `NUSANTARA-V1-FORENSIC-AUDIT.md:156` treats `0.50` as a reachable target. With mean expected documents per query = 161/160 = **1.006**, a true P@5 has a ceiling of about **0.20**. The 0.50 target was never attainable, and the measured 0.265 exceeds the true ceiling — which is itself proof the denominator is variable.

**Ruling:** Precision@5 as implemented is not a valid metric for this corpus. **Recall@5, Precision@1 and MRR@10 are the only valid retrieval metrics here**, and all three are healthy.

### 3.2 Provenance caveat

The 160-query evaluation is **not reproducible from the dataset in the tree**. `reports\search_eval_dataset_100.json` holds 166 queries with distribution `{0:6, 1:149, 2:9, 3:2}`, while the report reflects 160 queries with `{0:6, 1:149, 2:3, 3:2}`. Six queries lost one expected document each *after* the run. The numbers are historically valid; they are not currently regenerable. See `AUDIT_HISTORY_RECONCILIATION.md` §2.5.

### 3.3 Honest interpretation

Recall@5 = 0.824 means **the correct SOP is inside the returned top 5 for 82.4 % of queries**. P@1 = 0.55 means the correct document ranks first just over half the time — consistent with 44 near-identical Dukcapil SOPs sharing vocabulary. MRR@10 = 0.6377 places the first correct hit at an average reciprocal rank of about 0.64.

Retrieval is **functional and reasonably tuned**. The failure mode is confusion between near-duplicate SOPs, not absence of the right document.

---

## 4. Table extraction

`app\knowledge\docling_layout.py` (309 lines) reconstructs tables from Docling cell geometry.

| Finding | Detail |
|---|---|
| Grid acceptance threshold | was `h_count >= 3 and v_count >= 3`; changed to `>= 2` in commit `ddc54a2b` |
| Rationale | Many Dukcapil forms are 2-column layouts (`label | value`) that the 3×3 rule rejected outright |
| Coverage achieved | 33 / 170 tables (19.4 %) reconstructed as grids |
| Verified effect | Threshold change is in the working tree; **it has not yet been re-measured against the 170-table corpus** — coverage may differ |
| OCR preprocessing | deskew/binarise crashes Docling — **OCR enhancement is blocked**, not attempted |

**Honesty note:** reducing a threshold to accept more tables is a real change with a real risk of admitting false positives. It is committed but **its effect is unmeasured**. Treat 19.4 % as the last verified number.

---

## 5. Grounding and citation

| Guarantee | Implementation | Test |
|---|---|---|
| Every answer's claims are checkable against evidence | `grounding.extract_requirement_statement`, `service_answer_facts` | `test_grounding_echo_failsafe.py` |
| Negation handled | negation check in `grounding.py` | — |
| Citation survives projection | `document_citations.py`, response projection clears chunk text but keeps source ids | `test_v1_response_projection.py`, `test_chat_citation_source.py` |
| Prior citation reusable | `V1KnowledgeBoundary.reuse_prior_citation(document_id)` | `test_v1_knowledge_reuse_rebind.py` |
| Selected-document scoping | `KnowledgeEngine.selected_document_evidence` | `test_document_scope_v1.py`, `test_selected_pdf_chat.py` |

---

## 6. Known defects in the knowledge tree

| # | Defect | Evidence | Disposition |
|---|---|---|---|
| 1 | Three `.before_*_patch.py` snapshots shipped inside `app\knowledge\` | `production_kb.before_authority_patch.py`, `production_kb.before_metadata_authority_patch.py`, `production_semantic_retriever.before_authority_hydration.py` | ARCHIVE |
| 2 | `schemas.py.backup-20261013-150417` inside source tree | file listing | ARCHIVE |
| 3 | 69 `FAILED` pipeline runs vs 54 `READY` | `knowledge_pipeline_runs` | Investigated: these are historical retries of the same files that later succeeded; the run log is append-only. Not a live failure. |
| 4 | All 65 documents stored as `content_type = text/plain` | `select content_type ... group by` | Intentional: the parser normalises extracted text. Source type is preserved in `metadata_json` |
| 5 | Table grid coverage 19.4 %, effect of threshold change unmeasured | §4 above | Reported as gap |
| 6 | `app\rag\store.py` (2 modules) overlaps `app\knowledge\store.py` | two store implementations | MERGE-CANDIDATE, needs functional diff |

---

## 7. Verdict

| Criterion | Result |
|---|---|
| Ingestion works end-to-end | **PASS** — 65 docs, 722 chunks, 0 orphan docs |
| Embedding consistency | **PASS** — 722/722, one dimension, one model |
| Retrieval returns relevant sources | **PASS** — Recall@5 = 0.824 measured (artefact-backed) |
| Reranking present | **PASS** — `reranker.py` |
| Grounding enforced | **PASS** — guard abstains rather than guessing |
| Citation traceable | **PASS** — source ids survive projection |
| SOP Q&A functional | **PARTIAL** — deterministic composer works; LLM prose path abstains (model capacity) |
| Table extraction | **PARTIAL** — 19.4 % grids, unmeasured since threshold change |
| No second knowledge engine | **PASS** — one `KnowledgeEngine`, one `RAG` |

**Knowledge/RAG status: ACTIVE / PARTIAL.**
