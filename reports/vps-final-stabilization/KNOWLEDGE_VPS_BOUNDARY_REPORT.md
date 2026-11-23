# Knowledge VPS Boundary Report — Nusantara V1

- Commit SHA: `d2cfc60a0d88c93ce561f40c01d67e5f53910770`
- Branch: `codex/vps-final-stabilization-20261123`
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Collected: 2026-11-23T22:06:27Z–22:22:27Z

## Gate F verdict

**PASS (boundary verified) / BLOCKED (grounded SOP unavailable on VPS)** — the VPS can run Ollama inference and honest readiness reporting, but it does not contain the IndoBERT/Docling artifacts or the official PIAK-03 oracle. No production knowledge, personal data, or model artifact was uploaded to satisfy the gap.

## Verified VPS capabilities

| Capability | Evidence | Result |
|---|---|---|
| Ollama service | `a_processes`, `a_ollama_version`, `f_ollama_model` | PID `1090`, systemd `ollama.service`, `llama3.2:1b` ID `baf6a787fdff`, `/api/version` and `/api/show` HTTP 200 |
| Inference verification | `c_model_status_canonical`, `c_model_status_frontend_proxy` | `provider=ollama`, `model=llama3.2:1b`, `status=INFERENCE_VERIFIED`, `availability=INFERENCE_OBSERVED` |
| Chat path | `c_chat_pong_valid`, `c_chat_history_valid` | Synthetic non-grounded `PONG` HTTP 200; history 200 with one `SUCCEEDED` turn |
| Honest readiness | `c_readyz_alias`, `c_v1_ready` | HTTP 200 `status=degraded`, `knowledge_database=empty`, `documents=0`, `provider=ok` |
| Model-status boundaries | `c_model_status_canonical` | `knowledge=NOT_VERIFIED`, `official_oracle=REVIEW_REQUIRED`, `approval=REVIEW_REQUIRED`, `memory=LEGACY_BEHAVIOR_PRESERVED_TEMPORARILY` |
| DB contents | `c_active_db_documents`, `e_db_pragmas` | Active and isolated DBs have `9` tables and `0` documents; `quick_check=ok` |

## Missing artifacts

`f_missing_artifacts` confirms all are **MISSING** in both the RC worktree and the active repo:

- `backend/nusantara-models`
- `backend/nusantara-models/.venv/bin/python`
- `backend/nusantara-models/indobert_worker.py`

The RC expects these paths via `backend/app/core/nusantara_config.py:405-407`. The resulting live failure is recorded in `runtime/isolated/logs/backend.log`: `FileNotFoundError` when `IndoBERTClient.start()` calls the missing worker Python.

`f_pc_artifacts` also confirms these official inputs are absent from the VPS:

- `SOP_R2_Verified_PDF_20261005.zip`
- `data-pribadi-referential-manifest-20261005-160000.json`
- `ops-print-normalisasi.csv`
- `Nusantara-Hermes-ACP-Connection-Patch`

This is intentional. They were not requested, copied, or generated on the VPS.

## Live RAG profile observed

From `d2_full_regression_continue.out` `effective_rag_profile` and `d2_synthetic_search.err`:

- `retrieval_mode=hybrid`
- `lexical_normalization=token_overlap/query_tokens_capped_at_1`
- `lexical_weight=0.3`, `semantic_weight=0.7`
- `relative_threshold=0.5`, `absolute_relevance_gate=0.3`
- `top_k=5`, `candidate_count=20`
- `rerank_enabled=false`, `actual_reranker=NOT_APPLICABLE`
- `embedding_identity.status=NOT_VERIFIED`
- `configured_model=indobenchmark/indobert-base-p1`, `configured_dimension=768`, `actual_model=null`
- `knowledge_source.status=EFFECTIVE`, reference `/data/workspace/nus-v1-vps-final-20261123/runtime/isolated/test-knowledge.db`

## Grounded probe results

| Probe | Result |
|---|---|
| `d2_synthetic_ingest` | HTTP 400, missing IndoBERT worker Python |
| `d2_synthetic_search` | HTTP 500, generic public message; backend log shows same missing worker |
| `d2_synthetic_chat` | HTTP 422 `DOCUMENT_NOT_INDEXED` |
| `d2_synthetic_langchain` | 3 passed only under `env-langchain`; no dependency added to main env |

The failures are environment-boundary failures, not regressions: the same RC passes `tests/test_synthetic_retriever.py::test_synthetic_retriever_exposes_evidence_to_langchain` in the optional LangChain environment.

## Official PIAK-03 oracle (from prior forensic evidence only)

- Title: `SOP Permohonan Data Pribadi (PIAK-03)`
- Answer: `Persyaratan permohonan data pribadi: Surat Permohonan.`
- Source SHA-256: `e5cb6261e9b724fa17b1c9b303c9d0e921f122e0046b62dc716a41f04fa10b35`
- Report date: `2025-09-08`
- Docling: `4` pages / `22` chunks, stage `machine_parser`
- Chunk chars: min `304`, max `2000`, median `1501`
- Evidence: `a_sop_inventory.out`, `a_sop_sha256.out`, `a_sop_manifest.out`, `a_docling_profile.out`, `VPS_FORENSIC_BASELINE.md`
- The ZIP was inspected only as metadata/inventory; content was never copied to this workspace.

## Boundary statement

- VPS may be used for build, static checks, isolated runtime smoke, auth probes, and honest degraded readiness.
- VPS must **not** be used to claim official SOP acceptance, grounded PIAK-03 answers, or production knowledge readiness.
- No IndoBERT model, Docling cache, SOP PDF, manifest, personal data, or production DB dump may be uploaded to the VPS as part of this stabilization.
- Official E2E remains a PC-only handoff; see `PC_PIAK03_ACCEPTANCE_HANDOFF.md`.

## Command evidence index

`f_missing_artifacts.*`, `f_pc_artifacts.*`, `f_ollama_model.*`, `a_sop_inventory.*`, `a_sop_sha256.*`, `a_sop_manifest.*`, `a_docling_profile.*`, `a_ollama_model.*`, `a_processes.*`, `c_model_status.*`, `c_model_status_canonical.*`, `c_model_status_frontend_proxy.*`, `c_readyz_alias.*`, `c_chat_pong_valid.*`, `d2_synthetic_ingest.*`, `d2_synthetic_search.*`, `d2_synthetic_chat.*`, `d2_synthetic_langchain.*`, `runtime/isolated/logs/backend.log`. Full commands and exit codes: `evidence/commands.tsv`.
