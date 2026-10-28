# R2-A8 minimum remediation discovery

Date: 2026-10-08. Authorization: DISCOVERY AND DESIGN ONLY. No source modification or runtime execution is authorized. R2-A8 is not rerun.

## Current state and evidence

Repository `C:\Users\dmaza\mcp-starter`; branch `codex/fullroot-control-20261007`; HEAD `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. Extensive modified/untracked files predate this design. Git reports inherited inaccessible evidence directories and LF/CRLF warnings; no cleanup or permission repair is performed. `GIT_STATE.txt` records the current inspection. `INPUTS_BEFORE.json` and `DESIGN_VALIDATION.json` provide read-only source hash traceability.

R2-A7 is IMPLEMENTED_PARTIAL. R2-A8 pre-flight was BLOCKED / NOT_VERIFIED. Historical pre-flight OS evidence identified listener `127.0.0.1:8000`, PID 32796, parent 26952. Those facts are historical references in this task; the listener/process is not re-probed. No live identity is inferred from them.

Inspected sources include the R2-A7 observer/instance owner, main application composition, request context/middleware, provider types/implementation, Hermes, V1 projection, Knowledge/RAG/SQLite owners and lifecycle scripts. Read-only Graphify navigation found the relevant code relationships; truncated graph output was supplemented with scoped source reads. No graph update is necessary because source is unchanged.

## Observed execution trace

1. `app/main.py` constructs FastAPI and HTTP request middleware; in normal initialization it imports both API routers. Its existing evidence-only initialization excludes those owners and keeps `app.state.effective_configuration` null.
2. `request_id_middleware` accepts a sanitized optional client `X-Request-ID`, enters `request_context`, and returns `X-Request-ID`. IDs are contextvars; client-provided IDs alone are not unique authentication or correlation proof.
3. `app/api/routes.py:919` calls Ollama health before generation. It constructs a HermesAgent with the real provider and existing language owner, and at `:954–958` retrieves knowledge.
4. `KnowledgeEngine.search_knowledge` calls `RAG.query`; `_query` calls SQLite similarity/lexical search. Connections use WAL. Normal import also constructs `_knowledge`, which initializes SQLite schema before any request.
5. Multiple rule/evidence/offline branches exist. At `app/api/routes.py:1214`, only the generation branch calls the real provider. The response then passes through grounding/gate/session/developer processing and `_project_v1_chat_response`.
6. `OllamaProvider.generate` captures identity before the first await, posts `/api/generate`, validates the response, derives actual model from provider-reported `model` and completion from `done`, and returns `execution_identity` inside its typed response.
7. That internal receipt is not included in the public V1 projection. `_emit_identity` emits sanitized console telemetry, but logging errors are swallowed and success telemetry is deliberately not full verification. Lifecycle scripts can redirect console output to files; telemetry is not a protected-state-free receipt store.
8. `HermesAgent.run()` itself executes language/problem/reasoning and returns artifacts; it does not invoke generation. Calling it with no evidence would not reproduce `/v1/chat`'s provider execution path.
9. The R2-A7 GET observer exposes process metadata, runtime instance and non-transitive code manifest, but provider receipt is null and full build verification false.

## Root causes

- Observation and provider execution share process/context identifiers, but no application receipt preserves the complete joined tuple or records final response delivery.
- Source snapshot and limited registered-handler fingerprint cannot prove all loaded provider/dependency code.
- Current V1 generation is coupled to health/retrieval and protected-state owners; even a request that reaches no generation can touch those owners.
- Normal application initialization itself can touch SQLite. A DB-free endpoint alone cannot make a future restart protected-state-safe.
- Ollama's existing client uses `follow_redirects=True`. An application-level single generate call does not alone guarantee one outbound HTTP generation dispatch.
- Existing lifecycle convenience scripts perform broader actions than loading one observer.

## Discovery conclusion

Passive receipt exposure cannot by itself unblock protected generation. A new, explicitly authorized diagnostic boundary on the same application, plus a safe initialization/lifecycle decision, is the minimum scoped alternative proposed in the design. It proves only the declared diagnostic path, not normal `/v1/chat`, RAG, Hermes end-to-end behavior or a full application build. Without human acceptance of that narrower claim, the original verification remains blocked.
