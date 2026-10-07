# Composition root: scoped design and impact

2026-10-07. MDE-02 discovery: app/main.py is the actual application entrypoint. It imports V1/V2 route modules, where persistent services are assembled before FastAPI creation. Request handlers assemble providers, Hermes and V2 callbacks; KnowledgeEngine/RAG and HermesAgent own delegated component assembly. Lifespan only yields. These existing boundaries are retained. No additional composition root was created.

MDE-02 decision: KEEP existing implementation; source changes are not required for the scoped discovery, precedence and effective-configuration design. The earlier factory proposal below is deferred design, not the actual root or an automatic instruction to create a parallel factory. Default snapshot/gateway/executor activation remains future work. The verified contract is docs/MDE02_EFFECTIVE_CONFIGURATION_CONTRACT.md; evidence and current status are reports/MDE02_REPORT_20261007.md and .dev/MDE02_CHECKPOINT.json.

Preserve existing Settings, constructor signatures, explicit dependency precedence and API/CC01 response projection. A future `app/core/composition.py` should expose a factory taking an already validated immutable NusantaraConfig plus explicitly supplied provider/store/embedding/actor dependencies. No global mutable configuration, implicit dotenv load, worker start or production DB selection at import time.

Compatibility mode retains current Settings paths. Snapshot mode must be explicit: DEFAULT < JSON FILE < selected ENV mapping < EXPLICIT snapshot override, followed by reviewed consumer/request overrides. Do not merge provider selection, knowledge/index selection and request authorization into one mutable map. Default-valued legacy constructor arguments currently treated as unspecified must be documented before introducing any sentinel semantics.

Reuse ModelRouter/ModelGateway, existing KnowledgeEngine/RAG/IndoBERT adapter, governed NativeExecutor and optional AgentExecutorInterface. Missing actual adapters/capabilities fail before side effects; no OpenAI/Anthropic capability or real reranker is inferred from configuration/model labels. HermesV2Adapter is a pluggable structural executor, not a mandatory new Core Agent.

Actor role/permissions originate from trusted authentication/wiring, not snapshot flags or request tool arguments. Existing Trust/Policy/governance remain authoritative. Secret references stay separate from public effective configuration; do not resolve credentials into dumps, errors or traces.

Effective context must record per-field source, actual consumer, selected value, and DECLARED/CONSUMED/EFFECTIVE/VERIFIED status. Model payload identity must agree with selected-model metadata. Unsupported RAG weights/thresholds remain rejected until behavior contracts are implemented. Verify index model/dimension before any new embedding capability; persisted data migration is separately scoped.

First implementation must use injected MockProvider/MockTransport, isolated in-memory store/callback and worker-client fixture. Required tests: unchanged no-snapshot behavior; explicit dependency priority; deterministic source precedence; no import-time startup/DB/worker/network; actor permission denial; supported versus declared capabilities; selected model/payload consistency; CC01/API compatibility; full regression and protected integrity.

Impact: dependency construction only; no new API response fields or endpoint, no database schema change, deployment, restart, model install, credential/security-policy change. Rollback: exact pre-change source backup and scoped restore; retain legacy constructors and startup until opted-in equivalence is proven. Fundamental ownership/architecture changes require Human Decision Gate rather than implicit migration.

Status: EXISTING_COMPOSITION_IDENTIFIED_AND_RETAINED; future factory/default activation IMPLEMENTATION_NOT_DONE. MDE-02 does not close Configuration DoD or V1 acceptance.
