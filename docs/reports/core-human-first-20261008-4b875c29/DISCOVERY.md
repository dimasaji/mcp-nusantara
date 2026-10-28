# Human-first Core discovery

This discovery uses actual source inspection and bounded local tests, not runtime/provider/knowledge operations. R2-A14 is a known limitation; it is not a prerequisite for this work. No R2 assurance continuation or new gate was created.

## Current state

| Area | Observed implementation and dependency | Current evidence and gap |
| --- | --- | --- |
| A. Core Engine | `app/main.py` composes NORMAL/ATTESTATION; V1/V2 API owners, Hermes language→problem→reasoning pipeline, injectable `V2Orchestrator` stages | Source inspected. NORMAL route import eagerly constructs KnowledgeEngine/LanguageEngine. No live boot or useful-answer/provider proof collected; operation NOT_VERIFIED. |
| B. Configuration | `app/core/nusantara_config.py` validated immutable snapshots; `app/core/config.py` one-time effective owner; provider/RAG consume supplied snapshot | Source inspected. `runtime.stage_timeout_s` exists, while V1 `_run_sync_v1` defaults to 30 and DevCore defaults to 60; `/v2/dev` passes neither effective timeout nor effective generation defaults, explicitly overriding temperature/max_tokens. Configuration-consumer consistency is PARTIAL, not proven globally. |
| C. Provider/Model | `app/models/base.py`, `router.py`, `gateway.py` provide abstraction/selection and binding checks | Gateway is opt-in; current V1/V2 routes directly construct OllamaProvider; effective provider schema permits only ollama. Multiple-provider application composition is not complete. Providers not imported/invoked in the selected tests. Runtime identity remains NOT_VERIFIED. |
| D. RAG/Knowledge | KnowledgeEngine→RAG→SQLiteVectorStore, retrieval evidence and EvidenceGroundingGuard | Source inspected only. Store `_connect` runs SQLite WAL PRAGMA; NORMAL eager composition can reach this path. Protected database, WAL/SHM, worker and retrieval were not inspected or invoked. Actual grounding/data quality NOT_VERIFIED. |
| E. Tool Governance | GovernedToolRegistry checks permissions, risk/policy, schemas and approval consumption; classifications READ/WRITE/DELETE/EXECUTE/EXTERNAL | Source inspected. Selected tests use actual READ/LOW registry paths with no approval mutation. No risky capability was granted; privileged operation remains human-controlled. |
| F. Developer Engine | DevCore performs bounded file lookup/read/list and static/model analysis; DeveloperCoreEngine provides existing-graph analysis; controlled plan/patch classes also exist separately | DevCore workflow tested. Unsupported model analysis was still presented as the main answer after grounding rejection; fixed in this task. Write/execute remains blocked. General goal→scoped engineering plan is not integrated into the read-only intent router. |
| G. Control Plane | React router defines SYSTEM→EVIDENCE→TEST→REVIEW→DECISION; strict NORMAL/ATTESTATION projections and distinct browser intention flow | Source and prior report inspected. Existing isolated UI/browser reports are historical only. No UI/HTTP/browser tests in this task. Production completion/native integration NOT_VERIFIED; existing HOLD preserved. |
| H. Existing Tests | `tests/v2/test_devcore.py`, developer-core/configuration/provider/RAG/Control Plane/runtime tests and mock browser specs exist | Only changed-path tests and DevCore regression actually executed here. Existence of other tests does not count as passing. Live, provider, protected-state, API and browser suites NOT RUN. |

## Top five real blockers

1. **Rejected model claims reach the human answer.** `app/devcore/core.py` originally assigned model_text as the body and appended warnings when check_grounding found violations. Two new tests reproduce unsupported retry/timeout/output claims in the answer. Highest immediate value: remove rejected model text from the answer while preserving review diagnostics. **Resolved in this bounded change.**
2. **Broad human engineering goals cannot become bounded plans without concrete file/directory references.** `app/devcore/router.py:50` handles references/find/list and returns unhandled at line 79 otherwise. The pure router probe records the contract's RAG repair goal as unhandled. Existing modify requests remain blocked. Next safe work: design a no-write goal-to-inspection-plan preview, preserving current authority; no autonomous patch/execute or production tool expansion.
3. **Some important consumers override or omit effective settings.** `runtime.stage_timeout_s` is declared in nusantara_config.py; V1 helper's literal 30-second default and DevCore's 60-second default are independent. v2_routes.py:331 supplies fixed 0.1/700 generation overrides. These are observed hard-coded route defaults, not a claim that every request override is invalid. Next safe work: explicit default-versus-request override policy and isolated consumer tests before narrowly wiring effective settings.
4. **Provider abstraction is not the production composition boundary.** ModelRouter/ModelGateway exist, but effective schema restricts the provider and routes construct Ollama directly. General provider support needs a deliberate composition plan and isolated tests. No reason exists to swap the live provider/model now; any consequential operation or new security boundary requires a human decision.
5. **Safe application discovery is coupled to eager protected-resource initialization.** NORMAL imports construct KnowledgeEngine and LanguageEngine; store code opens SQLite and selects WAL. Importing the full app to discover status can therefore cross protected-state/worker boundaries. Plan narrowly separated composition or injected no-I/O diagnostic/test paths; do not open the production database or restart to test this finding.

These are concrete delivery limitations, not new gate requirements. Other gaps, including broader ASK/BUILD user experience, may remain; discovery does not assert an exhaustive audit of every code path.

## Dependencies and safe next changes

Human request→DevCore router→Workspace/read-only tools→GovernedToolRegistry→source result→static_facts/model callback→grounding→answer/verification→memory-only audit. This task changes only the answer selection after the existing grounding decision. No model callback was connected to a real provider.

Future bounded priorities follow P1 first: an explicit inspection-plan preview for broad human goals; then effective configuration consumer defaults; then provider composition through existing abstractions. RAG live evidence and production readiness require the protected-resource/provider operational decisions first. Control Plane should expose honest delivery states instead of forcing identity assurance PASS.

## Human decisions required

No extra decision was needed for this small presentation fix and isolated tests; the supplied master contract authorizes them. Restart/reload/deployment is not authorized. Provider/model operations, protected database actions, authorization activation, new security/capability boundaries and consequential external actions remain human decisions. None was performed. No decision is requested merely to erase NOT_VERIFIED identity statuses.
