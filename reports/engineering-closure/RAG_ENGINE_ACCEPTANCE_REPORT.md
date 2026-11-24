# RAG Engine Acceptance Report

- Status: **PARTIAL**
- Scope: configured RAG behavior, grounding and effective-profile transparency for Nusantara V1.
- Evidence: `evidence/WP-03/commands.tsv`, `evidence/WP-03/regression_final.out`, `evidence/WP-03/regression_final_tb_line.out`.

## Accepted in isolation

- `tests/test_configuration_integration.py::test_rag_actual_query_and_ingestion_use_config` passes after the fixture was changed to ingest 3 distinct documents with `chunk_size=2000`.
- Application behavior was not changed: per-document dedup remains intact; `top_k=3` means 3 documents, not 3 chunks.
- No relevance threshold, candidate count or retrieval mode was lowered or bypassed.
- Effective-profile logging remains present in both retriever and HTTP path failures, showing `embedding_identity.status=NOT_VERIFIED`, `execution_outcome.stage=embedding`, and `status=FAILED`.

## Blocked live acceptance

| Check | Status | Reason |
|---|---|---|
| Real retriever returns grounded documents | BLOCKED | Missing IndoBERT worker at `backend/nusantara-models/.venv/bin/python`. |
| `/v1/knowledge/search` HTTP 200 | BLOCKED | Same missing worker causes HTTP 500. |
| Approved embedding identity | NOT_VERIFIED | No approved model artifact supplied. |
| Grounded SOP ingest | NOT_VERIFIED | Staging report recorded `documents=0`; approved PIAK-03 SOP not available on VPS. |

## Classification

- `APPLICATION_BUG`: none found in the configuration/ingestion path during this work package.
- `PLATFORM_DEPENDENCY`: IndoBERT/Docling worker and approved knowledge artifacts are required.
- `POLICY_DECISION`: `top_k` semantics resolved as per-document for this fixture; any change to chunk-level `top_k` requires owner approval.

Final status: **PARTIAL — RAG configuration accepted offline; live grounded retrieval remains BLOCKED**.
