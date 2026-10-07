# MDE-03 Provider Registry — discovery and contract closure

2026-10-07. Task MDE-03-20261007. Decision **KEEP existing provider structure**. Discovery and contract closure only; no implementation/startup change. Existing ModelRouter owns a sufficient conceptual local registry for its current consumers. No additional ProviderRegistry is necessary for this scope.

## Existing abstractions and consumers

`app/models/base.py::LLMProvider` defines name/model properties, generation/structured/health operations and optional streaming/model-info helpers. Its request/response types are TypedDicts. Concrete LLM adapters are OllamaProvider, OpenAICompatibleProvider and MockProvider. `ollama_provider.py` and `mock_provider.py` re-export the same classes, not additional providers.

`app/models/schemas.py` separately defines Pydantic request/response/health/ProviderConfig models and another ModelSelection class. `app/models/__init__.py` exports those schema names, while actual ModelRouter returns its own `app/models/router.py::ModelSelection`. ProviderConfig is a declaration: there is no loader/factory automatically translating it to router registration. `app/interfaces.py::LLMProviderProtocol` is a structural generate(request) boundary, not a registry.

HermesAgent registers the injected provider in its own ModelRouter; a falsey/omitted provider falls back to MockProvider. Its router is not a global discovery service. V1/V2 API handlers explicitly instantiate OllamaProvider and call it directly for generation. They pass it to HermesAgent; API generation itself does not route through ModelGateway. V2Orchestrator and DevCore consume injected generate(prompt) callbacks and cannot infer provider identity/capability from the callback alone.

Separate embedding abstractions exist: EmbeddingProvider, SentenceTransformerEmbedder, OpenAIEmbeddingProvider, MockEmbeddingProvider, EmbeddingService and create_embedder. They are not LLMProvider registrations and must not be migrated into the text-model router by name. IndoBERT RAG/worker remains separate and unchanged. LLMReranker has an optional legacy generate(prompt) client and simple fallback, not an active registered LLM provider.

Test-only FakeProvider, local Provider classes, AsyncMock/InvalidMock and other mock subclasses are fixture injections. No dedicated class named TestProvider was found in the inspected app/tests source. No separate native OpenAI or Anthropic LLM class was found; OpenAI-compatible API support does not establish a particular cloud deployment's availability.

## Provider matrix

| Provider | Provider ID | Model ID | Capability | Registration | Selection | Configuration source | Availability source | Fallback | Consumer | Runtime verified? | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OllamaProvider | ollama | Constructor/snapshot; default llama3.2:1b | Text/structured generation; inherited streaming/info declarations | Explicit router.register; Hermes registers supplied object | Existing router branches, or API direct provider | Constructor, opt-in snapshot; API Settings/request.model | Explicit health /api/tags exact name; registry does not probe | No alternative invocation on generate failure | V1/V2, Hermes, optional gateway | Fixture only; live NOT_RUN | ollama.py; 8 branch payload observations; baseline |
| OpenAICompatibleProvider | openai_compatible | Constructor; default gpt-4o-mini | Text/structured API adapter; JSON-schema support is assumed | Explicit register only; no default API activation | Registered fallback; not native openai preference ID | Constructor URL/model/timeout/credential parameter; no secret resolution added | Explicit health /models exact ID; not automatic | Structured prompt fallback when schema mode unavailable; no provider failover | Explicit injected router/gateway | Fixture only; live NOT_RUN | openai_compatible.py; compatible payload/health observations |
| MockProvider | mock | mock-model; attributes are mutable but response identity is hardcoded | Synthetic text/structured/health | Explicit register; default Hermes injection | Registered fallback; tests may alias identity | Constructor synthetic response/health/delay | Synthetic health; not real availability | No alternate provider invocation | Tests/evaluator/Hermes default | Local synthetic execution only | mock.py; identity counterexample |
| LLMProvider / protocol | base / structural | unknown / caller-owned | Interface and metadata declarations | No automatic concrete registration | No implementation discovery | Class/instance metadata | Abstract or absent | Base streaming adapter only | Concrete implementations and structural callers | Not a live provider | base.py; interfaces.py |
| ProviderConfig/schema aliases | name field / no provider instance | model declaration | Declared configuration, no adapter creation | None | None | Explicit schema/factory values | None | None | Declaration; no registration loader found | Not runtime provider | schemas.py; package exports |
| V2/DevCore callbacks | No intrinsic ID | No intrinsic attestation | generate(prompt) result contract | Constructor callback injection | Caller owns selected provider | Existing closure/injected function | Failure handled by existing safe_acall/stage controls | Degraded/static fallback; not model failover | V2Orchestrator / DevCore | Fixture behavior only | v2_routes.py; orchestrator.py; devcore/core.py |
| Embedding providers/service | Separate embedding identity | Their own model/dimension declarations | Embeddings; some optional external adapters | EmbeddingService constructor/set_provider, factory | Separate backend/model-name factory logic | Explicit constructor/config | Separate optional client/model loading | Deterministic/hash or mock fallback in some classes | Embedding/retriever clients | Static only in MDE-03 | knowledge/embeddings.py; no activation/index changes |

The source map records exact symbol locations. Provider IDs identify instances by registration name, not trusted capability, authentication or endpoint health. Model IDs are requested/configured labels unless actual service/model evidence proves execution identity. No API key or credential value is recorded in these artifacts.

## Registration and selection contract

ModelRouter starts with an empty instance dictionary. register(provider) stores the object under its current provider.name and returns the same router. It performs no protocol/capability/health/credential validation. Duplicate names replace the existing entry; one name therefore holds one provider instance/model at a time. Registration order influences first-entry fallback. No entrypoint discovery, environment scan, automatic default, multi-model registry, deregistration API, immutable identity or concurrent registry contract is implemented.

Changing provider.name after registration leaves the old dictionary key. Changing provider.model after obtaining ModelSelection can leave the selection's captured model_name stale. list_providers reports dictionary keys mapped to current provider.model; it is a registration view, not a health report. The conceptual registry must retain these semantics; do not normalize IDs or reject duplicates silently.

| Priority / existing condition | Selected provider |
| --- | --- |
| Empty dictionary | RuntimeError; no automatic discovery |
| Sensitive privacy and ollama registered | ollama before task selection; preference only, not a fail-closed security guarantee if absent |
| Latency-sensitive or budget-sensitive and ollama registered | ollama |
| Coding + prefer_faster and ollama registered | ollama |
| Other coding | openai, else ollama, else first registered |
| Reasoning + prefer_cheaper and ollama registered | ollama |
| Other reasoning | openai, else ollama, else first registered |
| General prefer_local and ollama registered | ollama |
| Other general | openai if present, else first registered |

complexity is accepted but does not change current branch decisions. Task strings and estimated latency/cost/reasons are heuristic metadata, not benchmarked capability or actual availability. get_model_info's inherited supported tasks/128000 context and OpenAI-compatible _supports_json_schema=True are declarations, not empirical negotiation. Actual openai_compatible is not the preferred openai ID; a lone compatible adapter works through registered fallback. No alias registration or changed preference is introduced.

## Configured, registered, runtime verified

**CONFIGURED:** Settings, snapshot, ProviderConfig or constructor values exist. Settings.llm_provider is not a provider factory switch; current API explicitly constructs Ollama. Snapshot provider is restricted to ollama. Configuration does not make a provider available.

**REGISTERED:** An actual provider object was explicitly inserted in a particular router. Registration is independent of health, capability and installation. The API's direct-generation object and a Hermes router registration are different ownership facts, even when they reference the same object.

**RUNTIME VERIFIED:** A specific running provider/model invocation, with timestamp/build/instance and response/payload identity evidence. Synthetic fixtures and MockTransport prove local adapter behavior only. MDE-03 makes zero live/provider-healthy claims; health fixtures are not live verification. No real failover was performed.

## Identity finding: not universally consistent

For stable unmodified MockProvider and injected Ollama/compatible fixtures, the selected object and configured model agree with submitted payload and adapter-returned model metadata. FULLROOT's coding/reasoning fallback and provider.model repair remain valid for those paths.

Universal consistency is **false/not enforced**:

- A MockProvider aliased to openai/cloud-fixture routes under those labels but generates a Pydantic response identifying mock/mock-model. The previous preference tests did not exercise generation for that aliased fixture.
- Provider identity is mutable; captured registry keys/selection metadata may diverge from later object identity.
- Ollama and OpenAI-compatible responses report self.model rather than reconcile the upstream response model. Equal adapter metadata does not attest the model actually run by a server. Dict responses omit provider ID.
- ModelGateway returns the selected provider's result without identity reconciliation; generate_text checks only a string content/text. It accepts a response reporting another model. Selection/result are not a combined immutable receipt.

ModelRouter.route_and_generate delegates directly and can return an awaitable for async providers. ModelGateway awaits as needed, preserving sync MockProvider and async HTTP adapters; it does not add response/schema/capability validation. MockProvider's structured method takes an extra response_model argument and its health response differs from the base TypedDict shape; inherited async streaming is not uniformly compatible with sync implementations. These are documented interface limits, not repaired by this discovery task.

Generation failure propagates through the gateway without invoking a second registered provider. V2 owns safe-call timeouts/circuit breaking and degraded fallback text, while DevCore can produce static analysis fallback. Those are response degradation, not live provider failover. Health methods/list-model calls are explicit and endpoint-specific; registering an unhealthy mock still permits routing.

## Decision, impact and rollback

KEEP: existing internal registry and injection paths are sufficient to describe/use today's approved architecture. ADD would duplicate ownership; REFACTOR/identity enforcement would change existing duplicate/alias/response behavior and is not necessary to close this discovery contract. Known limits remain explicit open work; no universal identity or capability guarantee is added. No Level C action is proposed or performed in this scope.

Dependency graph retained: API -> explicit Ollama -> generation; API -> HermesAgent -> instance ModelRouter -> registered provider; explicit ModelGateway -> existing ModelRouter -> selected provider; V2/DevCore -> injected generation callback. No new imports, public interface, startup, availability, preference, fallback or authentication behavior.

Implementation classification: **KEEP / DESIGN + DOCUMENTATION + STATE**, not PATCH/REFACTOR/MIGRATION/REPLACEMENT/REBUILD. No app/main.py, API, Trust/Policy/Security, Ollama installation, RAG/index/database, dependencies or public schemas are changed. No implementation code was added. Rollback restores only prior state files from .dev/checkpoints/mde03-20261007/ and removes the new task documents/evidence selectively; never reset the inherited working tree.

Evidence: reports/MDE03_BASELINE_20261007.xml (38 passed), reports/MDE03_FOCUSED_OBSERVATIONS_20261007.json (22 asserted observations including counterexamples), reports/MDE03_DISCOVERY_MAP_20261007.json, execution report and checkpoint. Full regression is the verified MDE-02 380/28/1 baseline, not a new MDE-03 full run; the command requires a fresh full regression if source changes, and none occurred. Byte integrity verifies reuse applicability.

Stop after MDE-03. No MDE-04 was started. Configuration Architecture stays NOT_COMPLETE and V1 stays FAIL/HOLD.
