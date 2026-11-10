# Runtime Code Path — Nusantara V1 Knowledge Pipeline

## Pipeline Order (actual runtime)

```
Upload (POST /v1/knowledge/pipeline/documents)
  → KnowledgeEngine.process_knowledge_source()
    → _store_uploaded_source() (save raw PDF)
    → _record_pipeline(PROCESSING)
    → _extract_pdf_pages() (PyMuPDF, if PDF)
    → _extract_pipeline_text() (text extraction)
    → clean_text() (Haystack DocumentCleaner, conservative)
    → quality checks (length, char diversity)
    → metadata assembly (pipeline_status, source_sha256, source_authority, text_cleaning)
    → rag.ingest_document() (chunking + embedding + index)
    → _finish_pipeline(READY/FAILED)
  → SOPReview.detail() (operator review)
    → process_review() (Docling OCR, table reconstruction)
    → normalize_activity_grids() (docling_layout.py)
    → clean_extraction() (text_cleaning.py)
    → SOPReview.confirm_metadata() (operator)
    → SOPReview.decide(content_ok / approve / defer / reject)
  → V1KnowledgeBoundary.search_knowledge() (retrieval + access control)
  → HermesAgent.execute_v1() (chat + grounding)
```

## Key Files and Functions

| Stage | File | Function |
|---|---|---|
| Upload | `app/api/knowledge_pipeline.py` | `add_knowledge_source()` |
| Preflight | `app/knowledge/docling_layout.py` | `scanned_activity_grid_regions()` |
| OCR/Docling | `app/knowledge/docling_worker.py` | `convert()` |
| Table normalization | `app/knowledge/docling_layout.py` | `normalize_activity_grids()` |
| Haystack cleaning | `app/knowledge/text_cleaning.py` | `clean_text()`, `clean_extraction()` |
| Chunking | `app/knowledge/chunker.py` | `chunk_text()`, `Chunker.chunk()` |
| Embedding | `app/knowledge/indobert_embedding.py` | `IndoBERTEmbeddingAdapter.__call__()` |
| Indexing | `app/knowledge/rag.py` | `RAG.ingest_document()` |
| Search | `app/knowledge/production_hybrid_rag.py` | `HybridRAG.query()` |
| Retrieval | `app/knowledge/production_semantic_retriever.py` | `SemanticRetriever.query()` |
| Chat | `app/hermes/agent.py` | `HermesAgent.execute_v1()` |
| Grounding | `app/knowledge/grounding.py` | `EvidenceGroundingGuard.validate()` |
| Citation | `app/knowledge/document_citations.py` | `citations_supported()` |
| Access control | `app/security/v1_knowledge.py` | `V1KnowledgeBoundary.search_knowledge()` |

## Configuration

- OCR: Tesseract CLI, lang=['ind', 'eng'], psm=6, force_full_page_ocr=False
- Embedding: IndoBERT (indobenchmark/indobert-base-p1), 768D, via worker process
- Chunking: 512 chars, 64 overlap (SentenceChunker = Chunker)
- Vector store: SQLiteVectorStore
- LLM: Ollama (llama3.2:1b), local
- V2: disabled

## Commits Verified
- `d7fdaacf` — sync + fixes
- `9e0a3221` — docling_layout NameError fix
- `021f6da0` — OCR PSM tuning + template/golden set scripts
- `d394fcf5` — search precision tuning
- `3e50599c` — chore: remove trailing PY
- `8f8cd015` — table structure validation script
- `bf43c36a` — performance baseline script
- `3c50cafb` — error taxonomy
- `f4f93903` — table accuracy validation script
- `0b48db2a` — clean up git tracking

## Root Causes Found
1. **Docling NameError** (`layout_grid_regions` not defined) — fixed to `activity_grid_regions`
2. **Engine NameError** (`preparation` not defined) — fixed to `None`
3. **is_pilot()** — legacy docs gated as unapproved SOPs — fixed to exclude UNVERIFIED authority
4. **Session ID validation** — too strict (web-UUID only) — relaxed to 1-128 chars
5. **Grounding guard** — too strict for paraphrased answers — added subset-token check + evidence_fast_path
6. **Search noise** — nonsense queries returned results — added score filter (≥0.32) + document-level grouping
PY