# MDE05 — RAG Profile audit completion

Status: DONE_SCOPED_KEEP_WITH_OPEN_LIMITATIONS. Authorized MDE05 audit/design is complete. RAGProfile implementation acceptance is PARTIAL / NOT_READY; production runtime NOT_VERIFIED. Overall V1 remains FAIL/HOLD; configuration DoD NOT_COMPLETE. No MDE06 execution.

Human authorization: explicit APPROVE MDE-05 in the current conversation. Contract: docs/commands/MDE-04 -09.md section 18 and MDE_command1 section IX. Previous Phase0 checkpoint and 281 baseline/evidence hashes verified before work. New golden baseline `.dev/MDE05_BASELINE_20261007.json` captures 282 protected hashes before Level B tests or outputs; historical state/checkpoints retained.

## Discovery and architecture

Existing canonical HybridRAG is an alias of RAG, with KnowledgeEngine facade. Default V1 and V2 construct KnowledgeEngine without NusantaraConfig; their retrieval callbacks pass legacy settings top_k. Snapshot integration is optional. Explicit KB configuration wins over snapshot RAG values. Facade defaults top_k to 5 even if internal configured value differs. Canonical ingestion uses config/request chunk values but zero overlap falls through truthiness. Production ingestion separately uses 900/120 instead of canonical 512/64.

Canonical hybrid retrieval hardcodes weights 0.70/0.30 and relevance gates absolute 0.30 / relative 0.50. Supplied snapshot weights or threshold are rejected before store initialization, not silently accepted. V1 additionally filters score >=0.50. Static rag_runtime.json declares min_score 0.35; no runtime reader found in scanned app. This is a static configuration/consumer gap, not evidence of active live mismatch.

Reranker flag/model exist, but query rerank defaults False. Canonical requested reranking calls local keyword-overlap _simple_rerank, while the returned model label can name an unexecuted model. CrossEncoder/LLM factory implementations are separate and have explicit Simple fallback paths. Default API does not request that factory. Configured reranker identity is not executed identity.

Evidence carries chunk/source/score metadata but source may be empty. KnowledgeEngine filter is discarded. ProductionHybridRAG/ProductionSemanticRetriever have separate DB/metadata/source-authority behavior; authority restriction is optional. Their existence and name do not prove default API or live production use. VersionedKnowledgeStore lexical/access/version/conflict adapter is used in tests and is distinct from current API callback. Retriever similarity-only/Memoria assumptions differ from canonical hybrid protocol. Developer tool/source grounding and Graphify evidence are distinct from knowledge RAG evidence. No universal effective profile or profile invocation receipt is present in audited paths.

Detailed field/consumer map: `docs/reports/MDE05_RAG_PROFILE_MAP_20261007.json` (18 consumer/implementation entries; 655 textual reference sites). Text matches include non-executable references and archive candidates; they are not proof of active composition. Design: `docs/MDE-05_RAG_PROFILE_DESIGN.md`. Graphify scoped query used as source navigation; actual JSON fingerprint remains unchanged, not runtime proof.

## Decision, changes and risk

KEEP existing implementations; EXTEND effective-profile/provenance design only. No RAGProfile class, registry, engine rewrite, default injection, public schema change, security/governance change, model installation, worker/provider call, DB schema operation or index rebuild. Only baseline/map/design/test evidence/report/integrity/checkpoint artifacts created. PROJECT_STATE/TASKS/DECISIONS and previous checkpoints remain unchanged, preserving latest checkpoint integrity.

Material risks: scattered precedence, hardcoded thresholds, misleading reranker identity, incomplete source provenance/filter enforcement, production/default implementation divergence, and absent runtime attestation. Risk HIGH for declaring full acceptance from fixture success. Concrete affected-file proposal and rollback prerequisites are recorded in the design; Level C source/runtime integration is pending separate authorization.

## Tests, regression and runtime

Fresh existing focused contracts: **60 passed**, 4 deselected, 0 failures/errors/skips; 2 datetime.utcnow deprecation warnings. Run from an isolated working directory with repository code on import path, without app/API startup and without repository dotenv loading. Configuration contracts plus RAG/store/embedding fixture tests cover unsupported parameter rejection, ingestion/query handoff, request top_k precedence, explicit overrides, facade handoff and isolated DB path forwarding. XML: `docs/reports/MDE05_FOCUSED_20261007.xml`.

Six additional isolated behavior observations passed: hardcoded fusion weight, empty attribution retained, zero top_k truthiness fallback, reranker label versus local operation, explicit KB config precedence and fail-closed unwired weights. These are observations, not additional pytest test counts or production proof. Evidence: `docs/reports/MDE05_ISOLATED_OBSERVATIONS_20261007.json`.

Full regression reused from MDE02 unchanged-source evidence: 380 passed, 28 subtests, 1 Windows symlink skip; not run again or reported fresh. No project source/test modifications. Runtime verification: production health/provider/model/worker/RAG/index compatibility NOT_RUN / UNKNOWN; actual_model=null, identity_status=NOT_VERIFIED. No execution receipt fabricated. Fixture RAG executes actual query/ingestion methods with replacement embedding/store, not deployed runtime.

## Integrity, impact, rollback and self-audit

After tests and artifacts, 282 protected file hashes match, including source, tests, config, database bytes, graph and prior evidence. No unexpected source/config/data/graph drift; index compatibility cannot be inferred from byte integrity. Integrity record: `docs/reports/MDE05_INTEGRITY_20261007.json`. Static impact remains the inventoried constructor/API/facade/production/embedding consumers; no changed source requires graph refresh. New audit documents are not claimed indexed.

Rollback for this completed audit is restricted to its new outputs if requested, after checking paths/hashes. Production rollback not needed or exercised. Future implementation requires exact approved patch snapshot and scoped verification as described in design.

Self-audit: fresh versus reused tests explicit; static versus fixture versus live evidence distinguished; configured labels not attestation; source presence not default activation; filter discard/fallbacks/legacy protocol and archive candidates visible; unsupported parameters not pretended supported; no duplicate implementation, secret disclosure, silent mutation or approval bypass. Whole-phase audit completion does not mean RAGProfile implementation or V1 acceptance COMPLETE.

## Checkpoint and next step

Checkpoint `.dev/MDE05_CHECKPOINT.json`: DONE_SCOPED_KEEP_WITH_OPEN_LIMITATIONS. Preserve completed work and hashes; resume by verifying this checkpoint without repeating Phase0/MDE01-05. Next phase MDE06 Embedding/Index Safety is approval-pending. Section 34 requires STOP / GENERATE CHECKPOINT / WAIT FOR HUMAN APPROVAL after each phase. MDE09/MDE10 roadmap conflict remains for owner resolution before final closure.
