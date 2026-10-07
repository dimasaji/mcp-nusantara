# MDE-02 effective configuration contract

2026-10-07. Discovery/design and KEEP decision. No runtime configuration was activated.

## Construction and precedence

| Owner / source | Default and resolution | Constructor / consumer | Evidence and migration risk |
| --- | --- | --- | --- |
| Settings | Defaults < configured dotenv < process ENV < init arguments; case-insensitive; extra ignored | Cached singleton imported by API/provider | Isolated actual-class probe proves precedence without reading repository dotenv. Final singleton does not retain per-source provenance. |
| NusantaraConfig loader | Defaults < explicit JSON < selected supplied ENV < explicit leaf overrides | Snapshot opt-in constructors only | No automatic process ENV/dotenv; alias conflicts reject. Validation/path resolution is not consumption. |
| API LLM URL/model | localhost:11434, llama3.2:1b defaults through Settings; request.model or Settings model | V1/V2 handler -> OllamaProvider -> generation | Source and fixture consumption; no actual service provider/health verification. No provider availability inferred. |
| Ollama snapshot | Snapshot replaces URL/model/timeout only when legacy constructor argument equals its default | Existing OllamaProvider; strips trailing URL slash | Non-default arguments win. Default-valued explicit arguments remain ambiguous by existing semantics; do not silently add sentinels. |
| Generation options | Context Settings=4096 or snapshot; max_tokens default=512 or snapshot | _options -> /api/generate payload | Request max_tokens/temperature/top_p override snapshot; request max_tokens clamps to context. MockTransport verifies payload, not live model. |
| Knowledge facade | Explicit rag wins; otherwise create_rag receives snapshot only when supplied | KnowledgeEngine -> RAG | search/search_knowledge default top_k=5 is explicitly forwarded; API supplies Settings retrieval_top_k. Snapshot top_k is not universally authoritative. |
| RAG config | Explicit KnowledgeBaseConfig wins; else snapshot mapping or KB defaults | RAG ingestion/query, chunking, result metadata | top_k or configured default retains truthiness semantics. Explicit store/embedding callback win. No scoring changes. |
| Storage | Truthy explicit db_path > NUSANTARA_KNOWLEDGE_DB > data/knowledge/nusantara_knowledge.db | SQLiteVectorStore; relative path against cwd | Constructor creates directories/schema. Snapshot passes resolved path. No production DB opened for audit; no import-time read-only guarantee. |
| Embedding | Fixed IndoBERT base-p1 / 768 | RAG -> IndoBERTEmbeddingAdapter -> IndoBERTClient | Snapshot profile validation before default store/worker construction; encode checks 768 outputs. Injected callbacks bypass adapter profile checks and do not prove persisted-index compatibility. |
| Worker paths/timeout | Explicit non-None paths > ENV > repository defaults; timeout=60s | IndoBERTClient | Snapshot adapter forwards resolved paths/timeout; fixture verifies handoff without starting actual worker. |
| V2 data/discovery | NUSANTARA_DATA_DIR=data; NUSANTARA_DISCOVERY_HOSTS empty | Audit, approval, event/feedback, memory, candidates/proposals and validator | Module-level ENV selection; not the snapshot knowledge root. Keep ownership separate. |
| Router/Gateway | Registered provider objects plus route arguments | HermesAgent registers provider; optional ModelGateway delegates | Existing priorities preserved. Gateway not default API dependency. Provider/model labels are not capability evidence. |
| Executor | Trusted constructor actor plus existing governed registry | NativeExecutor -> GovernedToolRegistry | Snapshot flags/tool arguments cannot grant permissions; denial exercised. No new security authority. |
| Hermes | HermesAgent default MockProvider; supplied language reused | V1/V2 handler; HermesV2Adapter; optional V2 callback | V2 orchestrator supports no Hermes; current API supplies it. No new mandatory Core Agent or worker startup. |
| API startup/runtime declarations | app/main.py imports route modules; lifespan only yields; title/CORS/version literals retained | FastAPI and delegated persistent/request dependencies | Snapshot runtime host/port/workers/features do not activate API controls. Settings fields are not automatically equivalent to startup literals. |

The machine-readable map records actual read sites and field-level declarations. MDE-01 historical candidates are retained as historical evidence, not automatically enabled. No precedence rule changed, so old/new runtime behavior is identical.

## EffectiveConfiguration representation

Reuse the existing validated immutable snapshot and its provenance. Do not create another loader or singleton. The designed immutable observation record contains field, owner, configured_source/value, resolved_value, consumer, consumption_evidence, verification_evidence, build_id, instance/request identity and scope. Four independent evidence flags distinguish:

1. configured: a selected input or declared default exists with attribution;
2. resolved: validation and precedence/path normalization completed;
3. consumed: a specific dependency constructor, payload or query actually used the selected value;
4. verified_live: execution in a specific running service confirms that value for the same build/instance/request, with required model/index evidence.

Read sites are candidates. Matching a consumer value to a default does not prove dataflow. Fixture consumption never sets a production/live flag. Request overrides create distinct observations; they do not mutate or relabel base-snapshot provenance. Settings source cannot be guessed from final singleton equality. Existing loader statuses remain UNWIRED/DECLARED_ONLY; test consumption evidence is separate.

Credential values/references, raw environment, actor permissions, internal context and arbitrary reprs are excluded from the safe view. Existing URL validation rejects credentials. Local path observations remain local-only. Collection must not instantiate a provider/store/worker or contact a network. There is no implemented introspection endpoint or runtime EffectiveConfiguration class in this task; this is the required design contract.

## Critical boundaries and implementation decision

MDE-CONFIG-008: loader lexical paths and fixed adapter profile do not verify persisted index identity. Define future read-only metadata preflight to reject mismatched model/dimension before embedding/writes; this task performs no migration, rebuild or production DB connection.

MDE-CONFIG-010: Trust, Policy, authentication and governed approval stay authoritative; configuration never becomes authorization.

MDE-CONFIG-004/005: canonical RAG keeps 0.70/0.30 fusion and an evidence cutoff of max(0.30, 0.50 times top score). Snapshot weights/threshold stay rejected. Separate production retriever semantics are not normalized on numeric resemblance. Reranker metadata is not proof of neural reranking.

KEEP is the smallest compatible implementation choice under Phase 7: existing application and component assembly already constructs the required dependencies, while snapshot integration is optional and tested. No second root, subsystem replacement, default activation, credential resolution, source refactor, dependency change, schema/index change, restart or deployment is needed for this scoped command. Future default adoption remains explicitly open and must prove its own compatibility.

Verification: isolated precedence probe, focused constructor/integration/CC01/DeveloperCore tests and full existing regression. No tests weakened. Source and production database byte hashes are checked separately. Human Decision Gate is not triggered by this documentation/probe/KEEP decision. Protected runtime and acceptance boundaries remain unchanged.
