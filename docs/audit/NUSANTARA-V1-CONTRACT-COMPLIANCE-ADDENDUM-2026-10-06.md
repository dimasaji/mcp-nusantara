# NUSANTARA V1 — Contract Compliance Clarifications

Date: 2026-10-06. Scope: V1 documentation only.

This addendum records the observed implementation and clarifies terms without overwriting any of the eight existing contracts. It does not authorize runtime changes, waive security requirements, or amend release acceptance. Source references apply to the working tree identified in `reports/V1_CONTRACT_COMPLIANCE.json`, not to an assumed clean HEAD checkout.

## Runtime execution

Observed `/v1/chat` execution is:

Client/UI -> FastAPI route -> Ollama health check -> LanguageEngine -> ProblemEngine -> KnowledgeEngine/RAG -> relevance/trust assessment -> shadow GateIntegration (Reasoning/Policy/Memory/Orchestration) -> deterministic/local response, evidence fast path, direct Ollama generation, or offline response -> applicable grounding -> memory/developer snapshot -> response.

`app/api/routes.py:803` constructs HermesAgent and uses its language/problem members. The route does **not** call `HermesAgent.run()` or ModelRouter routing; it calls `provider.generate()` directly at line 1086. Hermes remains an existing foundation and is not replaced. The Architecture Contract execution diagram is an architectural specification, not proof that Hermes.run is the main API execution driver. Actual ownership remains a documented implementation gap.

The route already instantiates GraphifyBridge and returns a DeveloperRuntime snapshot. This existing read-only bridge is not a new Graphify orchestration system. Statements prohibiting new Agent/LangGraph/Graphify runtime do not establish that all similarly named legacy modules are absent.

## Intelligence boundaries

| Boundary | Implementation status | Meaning |
|---|---|---|
| Local Intelligence | IMPLEMENTED | IndoBERT semantic intent/768D embeddings and Ollama route provider exist, with historical local evidence. Official answer quality and production capacity remain partial. |
| External Intelligence | PARTIAL | OpenAICompatibleProvider module exists; `/v1/chat` instantiates Ollama directly. External provider selection and production approval are not proven. |
| Research Intelligence | PARTIAL | Research/discovery/experiment/proposal modules exist. Autonomous research-to-production execution is a future boundary and is not approved or implemented by this audit. |

No adapter, provider API or new intelligence runtime is introduced.

## Knowledge/RAG pipeline

Document -> DocumentParser -> SentenceChunker -> IndoBERTEmbeddingAdapter -> SQLiteVectorStore -> semantic + lexical retrieval -> 0.70/0.30 hybrid ranking -> EvidencePack -> route relevance/trust checks -> applicable grounding -> response.

`RAG.query` defaults `rerank=False`; the optional `_simple_rerank` is a lexical heuristic, not proof of a deployed neural reranker. Route facade does not enable reranking. Deterministic/local-rule responses use a separate route branch; not every response executes the generated-answer grounding validator.

Source authority, service region, version, effective date and review statuses in the seven-case oracle are evaluation metadata. They do not constitute a fully enforced production provenance/validity gate. Three fixtures, one negative case, two REVIEW_REQUIRED snapshots and one MISSING case retain their statuses. Tangerang snapshots are not promoted, and no knowledge DB is changed.

## Agent boundary

**AGENT RUNTIME = NOT IMPLEMENTED IN V1**

Here “Agent runtime” means the proposed autonomous agent/registry system, not the existing HermesAgent class or legacy OrchestrationEngine/DeveloperRuntime helpers. This absence is an architectural boundary, not a defect requiring implementation in this command.

- Identity: any future agent needs a stable identity, requester and scope; identity/session labels never grant permission. No new agent identity registry exists here.
- Lifecycle: future lifecycle must have explicit start, validation, execution, result, failure and termination states; do not infer a full runtime from the request pipeline.
- Permission/tool access: use existing governed registry and approved payload; no arbitrary shell or client-granted roles.
- Trust/policy/approval/audit: retain existing assessments and authorization components; model confidence or proposal text cannot grant human approval.
- Timeout: route stage defaults to 30 seconds/two slots; worker and ToolSpec limits are separate. Thread timeout does not prove cancellation of side effects.
- Budget: context/token settings and tool timeout are not a global autonomous-agent cost/step budget. Global enforcement remains NOT_IMPLEMENTED for the proposed agent runtime.
- Failure handling: fail closed on missing evidence, permission/approval failure or unsafe action; any future retry must remain bounded and idempotent where required.
- Human escalation: unsupported facts, high-risk actions and unresolved provenance must be referred for scoped human review. A requires_human flag alone does not implement a complete escalation workflow.
- Rollback: future change requires proposal, impact, approval, isolated candidate, targeted tests, regression and evidence; no autonomous production rollback/release is enabled.

## Tool/MCP/API boundaries

Tool definition is ToolSpec/schema; permission is registry enforcement; execution is registered handler via safe_call; audit is ApprovalQueue/AuditTrail; failure is ToolOutcome/error; timeout is ToolSpec limit; tool trust is distinct from permission and policy. Registry does not perform a general TrustEngine claim assessment for each tool output. Correct schema does not prove factual trustworthiness.

Existing stdio exposes only calculator/current_time_utc through GovernedToolRegistry. Legacy `app/mcp/mcp.py` directly calls handlers and is not a privileged governed substitute. V1 automatic chat-to-tool integration is not established. Existing real stdio test evidence is reused, not represented as a new execution.

## Trust, policy, approval and response security

The nested `trust` response uses exactly supports_claim, confidence, risk_level, requires_human, evidence_count and evidence_available. This exact shape does **not** imply the entire response is public-safe.

**Blocking deviation:** `app/api/routes.py:1213` returns raw `gate_context` as `gate_pipeline`. GateIntegration returns reasoning, policy and memory at lines 90–92; reasoning serialization includes facts, inferences and explanation. This conflicts with the compliance command's prohibition on internal reasoning/private policy exposure. DeveloperRuntime also exposes policy observability. No secret value exposure is asserted without evidence.

The shadow policy assesses the request and does not establish final-chat action enforcement. `app/policy/engine.py` blocks sensitive actions pending explicit authorization; it does not itself submit an approval request. Registry policy and ApprovalQueue are separate existing interfaces. Human approval component persistence/TTL/payload binding are implemented, but a fully wired V1 chat escalation workflow is not demonstrated.

MemoryEngine keeps bounded in-process turns keyed by caller-supplied session_id; bounded turns do not prove owner binding, TTL or total session limits. These governance gaps are not waived by this addendum.

## Configuration truth

Keep `app/core/config.py::settings` and existing component environment overrides; do not create another settings authority. Audit distinguishes defaults from active wiring: Settings lists local-hash/memory, while RAG actually instantiates IndoBERT/SQLite with KnowledgeBaseConfig. Route directly chooses Ollama rather than dispatching on llm_provider. Existing divergent configuration fields are documented gaps requiring a controlled proposal; this audit does not change configuration or claim all settings govern runtime.

## Freeze/change control

**V1 CONTRACT FREEZE = BLOCKED** due to the response-security contradiction. Documented future agent boundaries remain restrictive. No engine replacement, silent architecture change, duplicate configuration, destructive migration or autonomous production modification is authorized.

Required next process: Proposal -> Impact analysis -> Approval -> Implementation -> Targeted test -> Regression -> Evidence. This audit ends at documentation/reporting. `V1 ACCEPTANCE = FAIL / HOLD` remains unchanged from the final closure report.

Rollback for this documentation-only addendum: remove only this new document after reviewing any later edits; retain audit history and all existing contracts/runtime files. No runtime restore or production rollback is performed.
