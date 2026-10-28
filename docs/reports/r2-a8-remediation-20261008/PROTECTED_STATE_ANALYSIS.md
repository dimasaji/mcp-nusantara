# Protected-state safety analysis

## Existing V1 path

```text
app.main normal import
  -> app.api.routes module construction
  -> KnowledgeEngine
  -> create_rag / RAG
  -> SQLiteVectorStore.__init__
  -> mkdir + _initialize + SQLite CREATE statements

/v1/chat
  -> provider.health_check
  -> Hermes/language/problem processing
  -> KnowledgeEngine.search_knowledge
  -> RAG.query / _query
  -> SQLiteVectorStore.search_similarity + search_lexical
  -> _connect: sqlite3.connect + PRAGMA journal_mode=WAL
  -> branch selection -> possible provider.generate
  -> grounding/session/gate/developer/public response
```

Source anchors: `app/api/routes.py:43`, `:919`, `:954–958`, `:1214`, `:1307`; `app/knowledge/engine.py:32`; `app/knowledge/rag.py:241`, `:523`, `:592`, `:602`; `app/knowledge/store.py:17–47`, `:266`, `:298`.

Query intent, empty retrieval or eventual offline outcome cannot guarantee no SQLite connection. A SELECT through the ordinary connection may still affect journal/shared-memory state. Normal import can initialize schema before HTTP. Skipping a single retrieval after import is insufficient. Opening DB immutable/read-only, deleting sidecars, changing WAL mode, copying DB, toggling RAG configuration or monkeypatching the live store is not proposed.

**Conclusion: controlled generation through current `/v1/chat` cannot be guaranteed safe under no DB/WAL/SHM/RAG access/mutation. It remains blocked.** `/v2/chat` and `/v2/dev` are not alternatives.

## Conditional minimum alternative

Keep default V1 composition/semantics unchanged. Propose a diagnostic capability on the existing `app.main:app` using its existing evidence-only composition boundary, which already excludes full API/knowledge/language/approval owners. It would lazily acquire the existing immutable configuration snapshot for only the real provider and avoid creating those other owners. Do not install a second FastAPI/Core/Hermes or fake gateway.

This requires explicit human approval of a **diagnostic initialization profile** and its interpretation. Reusing the existing evidence-only flag is not permission to change the running process environment/configuration. No flag is changed now. The current evidence-only profile has no effective app configuration/provider and must not silently use defaults; missing snapshot/permit means fail closed. Do not publish its private provider snapshot through Control Plane state or modify Control Plane code.

A future diagnostic boot is the same application entrypoint with reduced composition, not proof that the original normal process loaded it, and not proof of normal V1/Hermes behavior. Loading it on port 8000 replaces the live process and needs a separate bounded lifecycle authorization. If the human requires the unchanged normal composition, the safe alternative cannot be adopted under this plan; additional initialization engineering or revised protected-state scope is required.

## Safety boundary requirements

- Full initialization/import closure, route execution, response instrumentation and shutdown must never import/construct Knowledge/RAG/SQLite/approval/audit/session owners.
- Only the existing configuration may be read for constructing the same provider/model; no dotenv/YAML/environment writes, reconfiguration or model pull/probe.
- The new route stores receipt/permit data only in process memory, bounded and inaccessible to general public/Control Plane projections.
- Protect the entire initialization/dispatch/send/shutdown path, not merely the endpoint function. Required future isolated tests guard sqlite connect, file mutation, child process creation and outbound calls; input files may be read for startup, but protected DB paths may not be opened even read-only.
- Redirect/retry/proxy behavior must be bounded as described in CORRELATION_DESIGN.md. An unknown connection target fails closed.
- Existing provider console identity logging and middleware metrics must be evaluated as part of the boundary. Console output must not be redirected to protected audit/data files. No claim that all provider runtime filesystem behavior is globally mutation-free is made.
- The actual model daemon may load model/cache state internally. This design excludes application-driven model changes/pulls/reconfiguration; it cannot guarantee zero filesystem activity in the existing external daemon. If the contract forbids even internal daemon activity, actual generation remains blocked and human must clarify the boundary.

## Rejected alternatives

Changing `/v1/chat`, early-return flags in its RAG path, opening DB to verify safety, WAL/SHM repair, fake provider, mocking a live request, independent harness, changing provider/model registry, hotpatching PID 32796, broad audit middleware or using `/v2` are rejected for this scope.

## Residual blockers

Safe startup profile, trusted arming channel, external daemon activity boundary and scoped acceptance must be explicitly accepted before implementation. The design does not claim these decisions have already been made or that a live request is now safe.
