# Current Nusantara architecture

Updated 2026-10-07. This describes existing source plus tested optional boundaries, not a production-ready verdict.

V1 API uses Settings, KnowledgeEngine, OllamaProvider and Hermes/Language/Problem/Reasoning paths. CC01 projection is unchanged. V2 API supplies callback dependencies to V2Orchestrator; policy/trust, bounded context, stage timeout/fallback, memory and observability remain existing implementations.

ModelGateway wraps the existing ModelRouter. It normalizes sync/async provider invocation and adapts response text for the existing generate(prompt) callback. It does not register providers, discover capabilities, install models, define new fallback policy, or activate API wiring. Router reports provider.model rather than literal model labels and falls back to a registered provider for coding/reasoning when preferred providers are absent.

ExecutorInterface describes governed tool execution. NativeExecutor binds trusted actor role/permissions/requested_by in its constructor and delegates execution/approval decisions to GovernedToolRegistry. Tool payload cannot grant permissions. AgentExecutorInterface describes the existing HermesV2Adapter.run boundary; Hermes remains optional in the existing V2 callback architecture. No MCP remote executor capability is claimed.

Configuration snapshots remain opt-in; startup still uses existing Settings. Provider health, worker health, persisted index identity and live effective configuration are not verified by developer.py health/validate. Local tests use isolated fixtures, MockTransport, TestClient and temporary storage.

Static graph/import maps are navigation evidence, not whole-program execution proof. The approved current source build is recorded in .dev/PROJECT_STATE.json. Earlier configuration reports remain historical, associated with their original build.
