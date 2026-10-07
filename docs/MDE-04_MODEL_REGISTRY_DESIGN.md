# MDE-04 Model Registry — identity and selection contract

2026-10-07. Task MDE-04-20261007. Decision: **KEEP**. Existing provider properties, ModelRouter selections and request/response structures are sufficient for the current discovery/design scope. No independent ModelRegistry is required. This contract clarifies observations; it does not implement identity enforcement or certify actual model execution.

## Identity vocabulary and canonical interpretation

| Concept | Meaning in this contract |
| --- | --- |
| PROVIDER ID | Literal provider.name for a particular adapter instance; registration captures that string as dictionary key. Endpoint/instance identity is additional context, not inferred from this ID. |
| MODEL ID | Opaque model selector scoped to provider/endpoint/instance. Same text across endpoints is not proof of the same model weights/version. Preserve existing strings without alias normalization. |
| DISPLAY NAME | Human-readable presentation label only. No dedicated canonical display_name/catalog was found. Reason text, class names and UI/API labels cannot select or attest a model. |
| ROUTING MODEL | ModelSelection.model_name captured from the chosen provider's current model property. Not an execution receipt. |
| CONFIGURED MODEL | Resolved constructor/snapshot/Settings value associated with the provider; may differ from class default. |
| DEFAULT MODEL | A declaration used if no overriding input applies; Ollama llama3.2:1b, compatible gpt-4o-mini, Mock mock-model. Defaults do not establish installation/availability. |
| ACTUAL RESPONSE MODEL | A model label reported in a response. Existing HTTP adapters synthesize self.model; raw upstream model is ignored. Public V1 model may be only a configured label. Neither is automatically actual-model proof. |

Canonical model identity is a provider-scoped selector observation, not a new global catalog. Preserve registration_key, adapter provider_id, instance/request/build identity and their captured times separately so mutable drift is visible. Never rewrite openai_compatible as openai merely because a router preference uses openai. Reuse the existing router; do not introduce new startup/default selection semantics.

The minimal internal evidence contract (design only; not new API fields or an implemented class) is:

| Field | Canonical interpretation |
| --- | --- |
| provider_id | Captured selected adapter name, with registration key and endpoint/instance context separately; any divergence is recorded, not normalized. |
| model_id | Provider-scoped configured/selected selector. Not a weights digest or guaranteed actual model. |
| capability | Named operation plus declared versus observed support and evidence; inherited metadata alone remains DECLARED. |
| requested_model | Original API request.model or explicitly supplied selector, otherwise absent. Do not replace absence with a default or silently treat arbitrary GenerateRequest dict keys as selection. |
| selected_model | Model label captured when choosing/constructing the provider. Selection records cannot be mutated by later execution. |
| actual_model | Unknown/null until model-execution identity is evidenced for the same invocation. No-generation, failure, callback-only or unverified server claims cannot populate a verified actual model. |
| identity_status | DECLARED, CONFIGURED, SELECTED, EXECUTED or VERIFIED as justified below, with explicit scope and evidence. |

Retain raw_response_model, adapter_response_model, execution outcome and mismatch details as separate evidence where available. A raw server claim remains an unverified claim. An immutable observation/receipt is an evidence design, not another loader/registry or a currently implemented validation layer. No credentials, raw environment, internal context or arbitrary object repr belongs in it. Nothing in identity metadata grants Trust/Policy authority.

## Lifecycle and evidence

| Status | Evidence required |
| --- | --- |
| DECLARED | Default/schema/config/catalog label exists. No dependency selection implied. |
| CONFIGURED | Resolution/constructor selected a value for an instance. No registration or model installation implied. |
| SELECTED | Router chose a specific object/model, or direct API constructor chose the provider/model. No generate invocation implied. |
| EXECUTED | The generation operation completed with an observed result for that invocation; fixture/provider-method execution must be scoped as such and does not establish live neural model identity. Record failed/attempted calls separately; a failure is not a completed execution. |
| VERIFIED | Same-invocation/build/instance evidence reconciles requested/submitted/selected/reported and actual model identity with relevant service/model proof. Fixture observations cannot become live verification. Health/model listing alone cannot supply this status. |

These are evidence levels for a specific observation, not a universal monotonic state on a mutable provider. SELECTED is not EXECUTED. A text reply or a model_called event does not prove the selected model ran: V2 emits that event for a failed generate stage too. Callback text loses identity metadata. On mismatch, retain the observation and uncertainty; do not promote identity to VERIFIED, relabel one model as another, retry an alternative provider, change public error behavior or alter selection in this documentation task.

Local adapters lazily construct HTTP clients, generate payloads, return metadata and close clients. Close does not uninstall/unload a model. list_models/health_check query model labels explicitly; there is no installation/download lifecycle or model inventory registry in ModelRouter. Registration replaces a same-name entry, so one provider ID currently holds one instance/model per router. No multi-model catalog or content fingerprint is claimed. Embedding/reranker model identities are separate domains and remain unchanged.

## Model Identity Matrix

| Field | Owner | Producer | Consumer | Source | Mutable? | Runtime verified? | Canonical? | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| provider_name / name | LLMProvider and adapters | Class/instance metadata | register, route, model info | Adapter/default or mutation | Yes, underlying attribute | Synthetic fixture only | Adapter ID observation, not health | base.py properties; MDE03 key drift |
| _providers dictionary key | ModelRouter | register(provider.name) | Routing preference/lookup | Name at registration | Entries replace; key not updated on object mutation | Fixture only | Captured registration key, distinct from current name | router.py register/list_providers |
| model_name / model | LLMProvider and concrete adapters | Default/constructor/snapshot | Route, payload, response metadata | Resolved configuration | Yes | Fixture payload only | Current configured selector | base.py; ollama.py; openai_compatible.py |
| ModelSelection.provider | router.ModelSelection | ModelRouter.route | route_and_generate/gateway | Registered object choice | Selection/object mutable | Fixture selection only | Selected object, not execution | router.py |
| ModelSelection.model_name | router.ModelSelection | route snapshots provider.model | Caller/routing metadata | Current model at selection | Yes; stale if provider changes | Fixture counterexample | Routing model observation only | MDE04 captured-selection probe |
| ModelSelection schema type | models.schemas/package exports | Independent compatibility class | Importing callers | Separate class/default unknown | Yes | Type distinction proved | Not actual router result type | schemas.py; __init__.py |
| ChatRequest.model / ChatV2Request.model | V1/V2 API | Request input | Provider constructor | Optional caller label | Request object mutable | Patched test/source scope | Requested selector | routes.py; v2_routes.py |
| Settings.llm_model | Settings singleton | Defaults/dotenv/ENV/init | API provider; DevCore label | Existing Settings precedence | Yes | Isolated precedence evidence | Configured/default selector | MDE02 resolution report |
| NusantaraConfig.llm.model | Immutable snapshot | Explicit loader | Opt-in provider constructor | DEFAULT < FILE < supplied ENV < EXPLICIT | Frozen | Isolated integration evidence | Resolved opt-in selector | MDE02 and configuration tests |
| GenerateRequest model selector | Base TypedDict / Pydantic schema | No declared model field | Provider generation options | Not present | Input dict may carry extra keys | Fixture proves no new selection | Not a selector contract | base.py; schemas.py; MDE04 probe |
| HTTP payload model | Ollama/compatible adapters | self.model | /api/generate or /chat/completions | Provider at generation time | New payload per call | Prior MockTransport fixtures | Submitted selector | MDE03 eight branches/compatible observations |
| HTTP adapter response.model | Concrete adapters | self.model, not raw server model | Direct API/caller/gateway | Configured object metadata | Returned dict mutable | Fixture metadata only | Adapter report, not actual identity | MDE03 ignored upstream label |
| Raw upstream response model | Remote response | Server claim | Currently ignored | Not reconciled by adapter | External/untrusted | Live NOT_RUN | Unverified claim if collected | MDE03 deliberately different fixture label |
| Mock response.model/provider | MockProvider/Pydantic response | Hardcoded mock-model/mock | Caller/gateway | Synthetic defaults | Output model mutable | Synthetic only | Synthetic response report; can mismatch alias | MDE03 aliased mock counterexample |
| Public V1 model | _PublicChatResponse/projection | model_used = provider.model | /v1/chat consumer | Configured provider label on all four branches | Payload/model mutable | Patched branch tests | Legacy report, not execution proof | routes.py local/fast/ollama/offline assignments |
| Pydantic GenerateResponse / StructuredOutput / HealthStatus.model | models.schemas | Caller/adapter/schema default | Schema consumers | Explicit/default strings | Mutable by default | Validation/fixture only | A declared or reported field; not attestation | schemas.py |
| V2 chat response identity | V2Result/API dictionary | Orchestrator return projection | /v2/chat client | No dedicated model/provider field | Result mutable | Callback tests only | Identity absent, not inferable | v2_routes.py return; orchestrator.py |
| Gateway generate / generate_text | ModelGateway | Selected provider / extracted text | Explicit callers/V2 callback | Reuses router; may select again | Returned result mutable | Sync/async fixtures | Result passes through; text has no identity | gateway.py; MDE04 callback probe |
| DevCore.model_name / audit model | DevCore and V2 dev handler | Constructor label / Settings | dev.request audit | Independent from generate callback | Yes | Isolated no-generate fixture | Configured audit label, not execution | devcore/core.py; MDE04 audit observation |
| ToolOutcome | GovernedToolRegistry/NativeExecutor | Existing governed handler | Tool caller | Tool name/status/output | Output mutable | Calculator/denial fixtures | Tool receipt; no LLM model identity | governance/tools.py; FULLROOT boundary tests |
| UI modelSelect value/display text | ui/index.html | Hardcoded llama3.2:1b, qwen3:4b, qwen3:8b options | /v1/chat request.model | Browser selection | Yes | Static only | Requested selector/display option, not installed-model catalog | index.html select and request body |
| UI model badges / health llm.model | UI and V1 health/detail | Public response.model or configured provider health model | Side panel/display | Legacy API model reports | Yes | Static only; no live health call | Display/configured model, not execution receipt | index.html data.model and data.llm.model |
| display name / actual_model / identity_status | Proposed evidence contract | No current unified producer | Future internal diagnostics only | This design | Proposed immutable receipt | NOT_IMPLEMENTED | Contract vocabulary only | No new registry/class/API claim |

The machine-readable source map records locations and scope. Matrix canonical status means interpretation of a field, not a certificate that every producer obeys it. Dynamic aliases/forwarding are not proved by AST navigation alone.

The UI's hardcoded options do not discover installed models; displayed response labels can remain present on no-generation paths. Its fixed Ollama display text is presentation, not an authoritative execution record. Health/detail constructs a provider from Settings and lists availability for that configured label; it does not attest a model generation. No UI behavior or labels are changed.

## Path audit

| Path | Actual model flow and identity limit |
| --- | --- |
| FAST local rule | V1 branch sets model_used=provider.model without generate. Current _deterministic_response always returns None, so local-rule coverage is dormant/test-double only, not an active live path. Configured model is not executed model. |
| FAST evidence / KNOWLEDGE evidence | V1 healthy-provider branch may return direct evidence for ask_document_status with score >=0.50 and nonempty source; no generate, but public model remains provider.model. Health checked earlier is not model execution. |
| KNOWLEDGE generation | V1 reads evidence, invokes provider.generate when no direct evidence response, takes content and labels public model from provider.model rather than result.model. Grounding may replace answer. Embedding retrieval execution is not LLM generation identity. |
| TOOL | NativeExecutor/ToolOutcome do not carry model identity. DevCore file tools can run with generate=None; its audit still records configured model_name. Generated developer analysis is optional and separate from the tool execution. No unified default TOOL-to-ModelGateway runtime is claimed. |
| OFFLINE | V1 unavailable health branch emits explanatory text and configured model label with no generate. V2 generate failure emits degraded fallback text; DevCore failure/no callback uses static facts. None proves actual LLM model. |
| V2 generation | request.model or Settings.llm_model -> explicit Ollama constructor -> generation callback returns content only -> V2Result/API response. Identity metadata is dropped; Hermes receives same provider but default API does not activate gateway. |
| ModelRouter | Registration/preferences choose provider object and capture current model; route alone makes no generation call. route_and_generate returns native provider result or awaitable; no retry/failover or identity reconciliation. |
| ModelGateway | generate chooses via existing router then awaits sync/async as needed; generate_text extracts string. Separate select then generate is not a single immutable selection/execution receipt. No identity validator. |

These are source/fixture path observations, not verification of a deployed unified FAST/KNOWLEDGE/TOOL/OFFLINE dispatcher. Historical integration/routes_with_devcore.py tests do not establish current app/api/routes.py behavior.

## MDE-03 mismatch closure and compatibility

All six prior mismatches are accounted for: aliased MockProvider hardcoded report; mutable provider identity; captured registration key drift; HTTP adapters reporting self.model rather than validating server identity; gateway accepting foreign model metadata; and native openai_compatible versus preferred openai naming. They remain implementation limits. This task closes their interpretation/discovery ambiguity, not the runtime defects or a universal consistency guarantee.

registered-provider fallback is selection of an already registered object when preferred keys are absent. It is not a retry after invocation failure and is not provider failover. No new retry/alias normalization/model switch is introduced. Default priorities, literal model selectors and constructor default-valued snapshot semantics remain unchanged.

Keep current ModelGateway signatures, sync MockProvider response, async HTTP response and V2 generate(prompt)->text adapter. Keep both selection classes/public imports; do not silently replace one. No new public schema/status/model field, app/main.py change, gateway activation, security/Trust/Policy change, RAG/index/embedding change, model install/download, dependency, live call or Core Agent.

## Decision and verification

Exactly one decision: **KEEP**. Required discovery and canonical evidence semantics do not need another metadata store. A registry would duplicate captured provider/selection values and would not independently prove execution. Identity enforcement or immutable receipts could be separate compatible work, with their own behavioral tests; neither is implemented here. No Level C action performed.

Fresh focused verification: 71 existing router/gateway/V1 projection/V2 tests passed; eight additional isolated observations passed. MDE-03's 22 observations are reused for its six mismatches, with unchanged source and evidence hashes. No test was added or weakened. Previous full regression is MDE-02 380 passed + 28 subtests + one Windows skip; not a fresh MDE-04 full run. Source remains unchanged, so the command's source-change full-regression condition is not triggered. No live runtime/model verification is claimed.

State/task/decision/report/checkpoint record source and database integrity, exact Git ownership and rollback. Restore only prior state files from .dev/checkpoints/mde04-20261007/ and selectively remove new task artifacts; do not reset inherited dirty work. No runtime/index rollback is required. Configuration Architecture remains NOT_COMPLETE; V1 remains FAIL/HOLD. Stop after MDE-04; do not start MDE-05.
