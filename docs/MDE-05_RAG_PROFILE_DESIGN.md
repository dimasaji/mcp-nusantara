# MDE-05 RAG Profile design — approval-gated extension

Decision: KEEP existing RAG/HybridRAG alias, KnowledgeEngine and production retrieval implementations; EXTEND their effective-profile contract only in a separately approved implementation. No new RAG engine, profile class, registry, DB/index or default startup wiring is created by this audit. Design status: NOT_IMPLEMENTED.

A configured profile is input intent. An effective profile is a captured immutable snapshot of the parameters actually consumed by a specific retriever instance and invocation. A runtime profile is that snapshot linked to execution evidence for the same invocation. Configuration repr, file name, model label, or a healthy fixture cannot promote it to runtime VERIFIED.

| Required field | Existing source/consumer and gap |
| --- | --- |
| profile_id | No dedicated profile identity; NusantaraConfig repr label is not an execution identity. |
| retriever | RAG.query hybrid differs from Retriever similarity and VersionedKnowledgeStore lexical. |
| top_k | Snapshot rag.top_k -> KB retrieval_top_k; explicit KB config wins; KnowledgeEngine default argument 5 overrides internal default; V1/V2 settings or search request override. |
| chunk_size | Snapshot/KB default 512; ingestion request override; production_kb constant 900. |
| chunk_overlap | Snapshot/KB default 64; request uses truthiness so 0 falls back; production_kb 120. |
| semantic_weight | Snapshot optional weights are rejected as unwired; canonical query hardcodes 0.70; production retriever accepts constructor value. |
| lexical_weight | Canonical query hardcodes 0.30; production semantic retriever normalizes constructor pair, hybrid wrapper requires sum 1. |
| similarity_threshold | Snapshot threshold rejected as unwired; canonical absolute gate 0.30 plus relative 0.50; V1 additionally filters >=0.50; static JSON min_score 0.35 not app-wired. |
| reranker | Config flag/model copied; query rerank defaults False; canonical uses _simple_rerank, not create_reranker; label can name unexecuted model. |
| knowledge_source | Default SQLite uses NUSANTARA_KNOWLEDGE_DB or cwd/data/knowledge/nusantara_knowledge.db; injected snapshot path optional; production uses distinct production_knowledge.db. |
| embedding_profile | Canonical default IndoBERT base-p1/768 adapter; config-injected mismatch rejected unless custom embedding supplied; actual worker/index identity not attested. |

The future descriptor must carry profile_id, implementation_id, source_build_id, config fingerprint, parameter provenance, knowledge source reference, embedding profile reference and field support status. Resolve values before retrieval; record request overrides separately from instance defaults. The proposed descriptor must retain the current consumer-specific defaults until each behavior change is reviewed: canonical hybrid weights 0.70/0.30, RAG absolute gate 0.30, relative gate 0.50, and V1 post-retrieval score gate 0.50 are different stages. JSON min_score 0.35 must not silently replace either gate.

Represent reranking as requested, configured, executed implementation, actual model (nullable), and identity status. Keyword overlap is a local algorithm, not proof that a named CrossEncoder or LLM ran. Existing reranker label must not be reused as execution attestation. Record failure/fallback reasons and no-evidence/abstention outcomes explicitly. Do not claim profile execution for tool-only or source-analysis paths without a retrieval event.

Preserve Evidence and EvidencePack attribution, chunk/source references and score-stage metadata. Future source policy checks must be explicit: canonical evidence currently permits blank source; production wrapper source-authority filtering is optional. Access/version/conflict behavior from VersionedKnowledgeStore is not automatically inherited by canonical SQLite RAG. Keep governance decisions authoritative and independent of relevance scores. Index/model compatibility is UNKNOWN in this phase and belongs to MDE06.

## Concrete Level C implementation proposal — not executed

Phase: MDE05 follow-up integration. Action: extend existing configuration-to-RAG handoff and add effective profile capture, preserving established public schemas/default behavior. Reason: current API bypasses optional snapshot and no single descriptor proves actual consumed values. Candidate affected files: app/core/nusantara_config.py, app/knowledge/schemas.py, app/knowledge/rag.py, app/knowledge/engine.py, app/api/routes.py, app/api/v2_routes.py; focused contract tests would require review alongside implementation. Production retriever/embedding files remain inspection targets unless a separately reviewed unification is necessary.

Impact: constructor precedence, request overrides, reranker/evidence metadata and API wiring can change behavior. Risk: HIGH if defaults, source authorization, score gates or embedding/index pairing change silently. Required evidence before implementation: field-by-field accepted precedence, impact graph/source consumers, approved public compatibility boundary, no worker/index activation, and explicit Level C authorization. This document is a design proposal, not an implementation approval.

Rollback: before an authorized patch, snapshot exact affected sources and verify hashes against this baseline; revert only approved patch files and rerun focused tests. No DB migration, model download or production index rebuild is part of this proposal. Snapshot/rollback source exists but production rollback was not exercised here.

Acceptance for eventual implementation: invocation-linked effective profile; consumer precedence covered by fixture tests; unsupported settings fail closed; actual reranker identity distinct from label; unchanged public compatibility unless separately approved; preserved attribution/governance; index compatibility proven under MDE06; real runtime trace under separately authorized verification. All must be evidence-backed before claiming RAGProfile COMPLETE.
