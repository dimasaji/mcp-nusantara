# NUSANTARA V1 — CC-01 Response Projection Proposal

Date: 2026-10-06. Scope: `/v1/chat` public response boundary. Risk: HIGH / BLOCKING.

**Mode: ANALYSIS + PROPOSAL ONLY. Change authorization: NONE. Runtime modification: FORBIDDEN.**

Commit: `0adccd9d9e847b8329457879ae0aae394ca13ca7`; build: `sha256:1f6298a5c04d9a751cf3f16b461ba376429970669758a77cdd595f61d6d91b8d`. This identifies the inspected dirty working tree; it is not a clean-HEAD assumption or new runtime deployment.

## 1. Recommendation and scope

Recommend **Option C — explicit compatibility projection**, preserving existing `response` and approved public subfields. Drop complete raw `gate_pipeline` and `developer_core`; do not rename response to answer, add another endpoint, introduce a ModelRouter, or change an engine.

The proposal includes success and local error boundaries, citation disclosure review, compatibility impact, designed tests, and a safe rollback plan. It is concrete for owner review but not approved for implementation. CC-01 remains OPEN / BLOCKING, contract freeze remains BLOCKED, V1 acceptance remains FAIL / HOLD.

Only the two requested proposal artifacts are created. Progress and preservation evidence are embedded in the new JSON so existing checkpoints remain unchanged. No source, tests, DB, configuration, contracts, historical reports or Docker state are modified.

## 2. Governance and reference resolution

The eight existing contracts, GATES, compliance evidence and actual addendum govern this analysis. The command's opening reference to `reports/NUSANTARA-V1-CONTRACT-COMPLIANCE-ADDENDUM-2026-10-06.md` is absent. The existing document is `docs/audit/NUSANTARA-V1-CONTRACT-COMPLIANCE-ADDENDUM-2026-10-06.md`; it was read, without creating a duplicate.

Git status was recorded before work. Pre-existing user modifications and untracked files remain legitimate workspace state; no reset/checkout/clean/restore was performed. No environment contents or credentials were read/dumped. `.env` preservation is checked using file size/mtime only.

## 3. Exact source proof

Source and AST prove structural exposure; no live HTTP call, model invocation or secret-value probe was made.

| Source location | Observation |
|---|---|
| `app/api/routes.py:91` | ChatRequest: caller session_id(default web), user_input, optional model, stream; session labels are not authorization. |
| `app/api/routes.py:752` | POST /v1/chat without response_model; shared final success dict is serialized without public projection. |
| `app/api/routes.py:803` | Hermes constructed; route invokes language/problem members directly, not Hermes.run. |
| `app/api/routes.py:812` | Language stage via bounded sync runner. |
| `app/api/routes.py:820` | Problem stage via bounded sync runner. |
| `app/api/routes.py:829` | Knowledge retrieval then score >=0.50 gate. |
| `app/api/routes.py:889` | Canonical scores mapped to Trust relevance; approved six-field trust object later serialized. |
| `app/api/routes.py:965` | GateIntegration.process produces shadow context. |
| `app/core/gate_integration.py:90` | Gate return includes reasoning, policy, memory and orchestration. |
| `app/reasoning/schemas.py:51` | Reasoning serializer includes facts/inferences/explanation, not only a public score. |
| `app/policy/engine.py:12` | Policy serializer includes decision,allowed,reason,risk. |
| `app/memory/engine.py:24` | Memory entries include session_id,role,content,timestamp,metadata; context returns recent turns. |
| `app/orchestration/engine.py:34` | Orchestration.data duplicates reasoning/policy/memory; carries current user_input. |
| `app/developer_core/runtime.py:82` | Developer snapshot exposes same orchestration object. |
| `app/developer_core/runtime.py:91` | observability.policy_decision and gates.9 decision/allowed/risk expose policy state. |
| `app/api/routes.py:1201` | developer_core snapshot assigned directly to public response. |
| `app/api/routes.py:1203` | trust has exact six fields; issues/details excluded. |
| `app/api/routes.py:1213` | gate_pipeline assigned raw gate_context. |
| `app/api/routes.py:1218` | grounding contains enabled,grounded,reason,unsupported_sentences. |
| `app/api/routes.py:1245` | understanding/problem full dumps assigned; evidence contains document_id,title,source,chunk,score. |
| `app/api/routes.py:498` | Deterministic helper always returns None in current source; local-rule final branch exists but unreachable through helper today. |
| `app/api/routes.py:1046` | Evidence fast path and Ollama generation validate applicable grounding; offline branch still uses same final response. |
| `app/api/routes.py:1287` | Generic exception interpolated into HTTP500 detail; success-only projector would not sanitize this. |
| `app/exceptions.py:106` | Provider handler returns error,message,details,path; generic HTTPException and validation use framework boundaries. |
| `app/ui/index.html:2083` | Chat bubble reads data.response; no existing answer field required. |
| `app/ui/index.html:2218` | Activity consumes evidence length, understanding.intent, problem.goal, model,latency_ms. |
| `app/ui/index.html:2072` | state.lastResponse stores complete payload. |
| `app/ui/index.html:2685` | openRaw/pretty serializes complete state.lastResponse, including internal fields present in payload. |
| `app/ui/index.html:1835` | UI injects request_id from existing X-Request-ID header; body request_id absent in route success. |
| `scripts/run_eval.py:61` | Evaluator consumes response,evidence.chunk/document_id,model/provider/grounding/session/timestamp. |
| `scripts/test_api_contract.py:11` | Standalone contract checks require current top-level fields and understanding.input/output; reduced nested projection has impact. |
| `scripts/validate_gate16_7_pdf_to_answer.py:72` | Diagnostic script inspects developer_core if present; removal changes diagnostic output, not a demonstrated mandatory app dependency. |

The success response has these root keys:

`developer_core`, `session_id`, `trust`, `response`, `gate_pipeline`, `model`, `provider_status`, `latency_ms`, `grounding`, `understanding`, `problem`, `evidence`, `timestamp`.

`answer` and `content` are not existing success keys. Request correlation is provided by existing `X-Request-ID`; the UI adds it to its local data object. No new body identifier is needed for this proposal.

### Exposure structure

- `gate_pipeline.reasoning`: status, facts, inferences, confidence, explanation, blocked_reason.
- `gate_pipeline.policy`: decision, allowed, reason, risk.
- `gate_pipeline.memory[]`: session_id, role, content, timestamp, metadata; includes recent previous turns and current user turn, with limit eight in MemoryEngine.context.
- `gate_pipeline.orchestration.data`: duplicated reasoning, policy and memory, plus language/problem; orchestration also includes current user_input/session/stages.
- `developer_core.observability`: reasoning status/confidence, policy_decision, memory_items.
- `developer_core.gates.9`: decision/allowed/risk; other gates expose engine state.
- `developer_core.orchestration.data`: the same duplicated reasoning/policy/memory context.

Therefore removing only `gate_pipeline.reasoning` or even only the `gate_pipeline` root is insufficient: developer snapshot duplicates remain. This is deterministic internal diagnostic data, not an assertion that model hidden chain-of-thought or actual credentials were leaked.

GateIntegration remembers the current user turn before constructing context; the assistant response is remembered later. Prior context can still appear without redesigning the engine. Projection must exclude it at every public path.

## 4. Branch and error coverage

All success branches converge on the same response dictionary: local-rule, evidence fast path, Ollama generated output and offline message. The deterministic helper currently returns None on every path, so local-rule is a dormant branch; future designed coverage must use a synthetic fixture rather than enabling production behavior.

Evidence fast path applies to the controlled document-status branch when provider availability/evidence conditions hold. Guard failures replace text with existing abstention. Projection must preserve these decisions and trust assessment values; it must not certify a new factual answer or bypass grounding.

Generic route exceptions become `HTTPException(500, detail=exception text)` at `app/api/routes.py:1287`. Success-only projection does not prevent this raw error path. Proposed primary scope includes generic safe local 500 detail. Existing HTTPException/provider re-raise, validation 422, timeout/busy 503/504 and shared handlers need explicit boundary review. Shared provider errors contain message/details/path; a URL/query can include caller content even without an environment secret.

Do not claim that route-only success changes sanitize every framework error. If this requires `app/exceptions.py`, request separate path-limited approval for `/v1/chat`; shared `/v2` behavior must remain identical. No such change is implemented here.

## 5. Proposed classification

Categories are exactly PUBLIC, INTERNAL, ADMIN/DIAGNOSTIC and REMOVE_FROM_PUBLIC_RESPONSE. PUBLIC means a proposed reviewed disclosure, not approval merely because a key exists today. Raw object classification is distinct from its allowed reconstructed scalar subset.

| Field/path | Category | Proposed condition |
|---|---|---|
| `response` | PUBLIC | Existing answer text, unchanged semantics after existing safety decisions; preserve key, do not rename to answer. |
| `answer/content` | PUBLIC | Conceptual answer alias only; absent from current root success shape; DO NOT add or rename. |
| `trust` | PUBLIC | Exact six existing fields; shallow projection alone is insufficient for other root fields. |
| `trust.supports_claim` | PUBLIC | Preserve current assessment value/type; not authorization or factual certification. |
| `trust.confidence` | PUBLIC | Preserve current assessment value/type; not authorization or factual certification. |
| `trust.risk_level` | PUBLIC | Preserve current assessment value/type; not authorization or factual certification. |
| `trust.requires_human` | PUBLIC | Preserve current assessment value/type; not authorization or factual certification. |
| `trust.evidence_count` | PUBLIC | Preserve current assessment value/type; not authorization or factual certification. |
| `trust.evidence_available` | PUBLIC | Preserve current assessment value/type; not authorization or factual certification. |
| `trust.issues/trust.details` | INTERNAL | Remain excluded; never move reasoning into trust. |
| `evidence` | PUBLIC | Only scope-authorized/public-approved citations; item allowlist document_id,title,chunk,score. No raw source/metadata. |
| `evidence[].source` | REMOVE_FROM_PUBLIC_RESPONSE | May hold full text/file path or unreviewed provenance, not guaranteed safe URL. |
| `gate_pipeline` | REMOVE_FROM_PUBLIC_RESPONSE | Remove entire raw object; no empty wrapper or recursive pass-through. |
| `reasoning/facts/inferences/explanation` | INTERNAL | All instances, including nested orchestration duplicates, retained only existing server execution. |
| `policy` | INTERNAL | Decision/allowed/reason/risk may not be copied outside approved public trust. |
| `memory/history/session state/internal memory metadata` | INTERNAL | No public prior turns or state; echo current session label only is separately allowed. |
| `developer_core` | REMOVE_FROM_PUBLIC_RESPONSE | Remove complete snapshot including orchestration, gates and observability. |
| `developer_core.runtime/request/gates/orchestration/observability` | ADMIN/DIAGNOSTIC | Potential future scoped/redacted authenticated diagnostics only, no endpoint or new retention now. |
| `developer_core.observability.policy_decision` | ADMIN/DIAGNOSTIC | Never ordinary chat; separate authorization/audit required, not public metadata. |
| `grounding.enabled/grounding.grounded` | PUBLIC | Preserve boolean outcome; not a new claim of official validity. |
| `grounding.reason` | PUBLIC | Approved finite public reason code set; unknown codes mapped to reviewed generic fallback, not raw internal text. |
| `grounding.unsupported_sentences` | REMOVE_FROM_PUBLIC_RESPONSE | Raw rejected text may retain confidential context or unsupported claims. |
| `understanding` | REMOVE_FROM_PUBLIC_RESPONSE | Reject raw dump; only reviewed current-request intent scalar may be reconstructed under same key. |
| `understanding.intent` | PUBLIC | Approved intent label only; no raw input/output/entities/confidence/metadata/other nested fields. |
| `problem` | REMOVE_FROM_PUBLIC_RESPONSE | Reject raw dump; current-request display goal only if approved and type-bounded, no steps/solutions/risk/context. |
| `problem.goal` | PUBLIC | Reviewed display scalar for current request only; no historical memory or internal explanation. |
| `latency_ms/timestamp` | PUBLIC | Existing bounded timing and response timestamp; not operational trace dumps. |
| `session_id/X-Request-ID` | PUBLIC | Existing current-request identifiers only; neither establishes identity/ownership/authorization. Keep request ID header, no new body field. |
| `model/provider_status` | PUBLIC | Reviewed display model name and existing finite status labels only; no base_url/API key/configuration. |
| `provider endpoint/configuration/secret material` | INTERNAL | Never included in public metadata or diagnostics without approved redaction. |
| `error HTTP status and reviewed generic detail/message` | PUBLIC | No exception string, raw validation input, full request URL/query or internal details. |
| `error traceback/raw details/request URL` | ADMIN/DIAGNOSTIC | Scoped server diagnostics only; no new logging of secret/user content proposed. |

## 6. Trust contract

Keep exactly supports_claim, confidence, risk_level, requires_human, evidence_count and evidence_available. Source/AST confirm `trust.issues` and `trust.details` are excluded. Do not extend trust, copy reasoning into it, recompute its values, or use confidence/requires_human as authorization.

If public citation disclosure filters an internal assessed item, trust.evidence_count remains the assessment count. It is not necessarily visible citation count; owner must approve/document this distinction. Do not silently redefine the existing trust schema or promote unapproved evidence to reconcile counts.

## 7. Options and tradeoffs

| Option | Target | Security/architecture | Compatibility | Recommendation |
|---|---|---|---|---|
| A — Strict Public Projection | response, six-field trust, approved citations and minimal identifiers/timing | Small public surface; explicit nested allowlists | UI goal/intent/model display and existing contract tooling may lose fields | Valid alternative if owner accepts migration |
| B — Public + Diagnostic | Safe public schema and a separately authorized diagnostic boundary | Requires authenticated principal, explicit scope, audit and redaction; added auth/API scope | Can later serve approved diagnostic workflows; no automatic compatibility | Defer; no diagnostic endpoint in initial CC-01 scope |
| C — Compatibility Projection | Preserve demonstrated safe display/evaluation keys with explicit scalar/nested projection | Remove complete internal roots and raw dumps; future unknown fields stay private | UI main flow retains existing key names; raw drawer and legacy nested checks change; NOT_PROVEN for unknown clients | Recommended for owner review |

No option may preserve raw internal output behind client-controlled debug, role or session flags. A compatibility version cannot retain the unsafe legacy payload for ordinary clients.

## 8. Concrete proposed target

Internal execution remains existing: reasoning, policy, memory, gate_context and developer observability are calculated server-side. The outbound boundary builds a new dictionary from approved fields without mutating the original context or enabling additional storage/logging.

Proposed root keys, all existing:

`session_id`, `response`, `trust`, `model`, `provider_status`, `latency_ms`, `grounding`, `understanding`, `problem`, `evidence`, `timestamp`.

| Object | Allowed keys |
|---|---|
| trust | supports_claim, confidence, risk_level, requires_human, evidence_count, evidence_available |
| grounding | enabled, grounded, reason |
| understanding | intent |
| problem | goal |
| evidence item | document_id, title, chunk, score |

Drop `gate_pipeline`, `developer_core`, raw understanding/problem members, evidence.source and grounding.unsupported_sentences. Reconstruct only reviewed intent/goal scalars for current-request display; never copy arbitrary dicts or use generic model_dump/stringify fallbacks. Null/absent/unknown/malformed values need reviewed safe defaults/omission and bounded types. Never expose future keys automatically.

Grounding reason candidates found in source: empty_answer, no_evidence, grounded_abstention, requirement_evidence_missing, possible_unsupported_content, grounded, deterministic_response and not_evaluated. Provider display statuses found: local_rule, evidence_fast_path, ollama and offline. These are approval candidates, not an implemented public schema. Unknown internal codes require an approved generic fallback rather than raw text.

Citations require owner-reviewed public/scope authorization. Existing source may be full document text/path rather than a safe URL. Retaining chunk supports the evaluator, but only for approved disclosure; fixture/snapshot authority must not be promoted. If safe disclosure is unproven, omit that item. A response projector does not solve production provenance or grounding quality by itself.

Keep existing X-Request-ID header/current session echo; neither is caller authentication. Keep answer content/endpoint request semantics and current trust/grounding decisions unchanged.

## 9. Security, memory and developer privacy

Raw internal object -> public response exposes present fields and automatically exposes future fields. A blacklist of current forbidden names has the same expansion hazard; arbitrary unknown nested fields can carry internal content. Positive allowlists at root and each nested object constrain that expansion.

Remove every memory/history/session-state/internal-metadata path and both orchestration mirrors. Excluding memory from response mitigates CC-01 exposure but does not establish MemoryEngine owner binding, TTL or total-session caps (CC-05). Do not redesign those controls in this scope. Do not move raw memory into new logs for debugging.

DeveloperRuntime.runtime and request counters are not automatically PUBLIC merely because they appear harmless. Full snapshot has engine versions, gate status and policy observability. Primary proposal excludes the complete snapshot; potentially useful metrics require separate diagnostic authorization review. No developer endpoint is changed by this proposal; exposure through existing other endpoints is separate scope and cannot be declared fixed by `/v1/chat` work.

## 10. Compatibility evidence

| Consumer | Observed usage | Impact/status |
|---|---|---|
| app/ui/index.html | response; latency; model; evidence length/title/score; understanding.intent; problem.goal | Source-proven; Option C retains proposed display keys. Runtime/UI compatibility is not tested here. |
| UI state.lastResponse and Runtime JSON drawer | Stores and serializes the full response generically | Source-proven diagnostic exposure. Drawer must show reduced public schema; internal visibility deliberately disappears. |
| UI feedback | Existing request ID header copied locally plus session_id | Preserve header/current session echo; no `/v2` change proposed. |
| scripts/run_eval.py | response; evidence.chunk/document_id; metadata model/provider/session/grounding/timestamp | Source-proven; approved citations and key names retained. |
| scripts/test_api_contract.py | Required top-level fields and understanding.input/output | Source-proven predicted break: nested input/output are removed. Owner must approve migration; do not weaken the script during proposal. |
| scripts/validate_gate16_7_pdf_to_answer.py | Optional printing of developer_core | Diagnostic output changes; not proof of required application behavior. |
| tests/test_gate_integration.py | Direct internal engine object assertions | Internal structures must remain unchanged; these are not public consumer contracts. |
| Other/external clients | Usage not established by inspected repository | NOT_PROVEN; no claim of global compatibility. |

No named ordinary UI logic consuming gate_pipeline was found in inspected app/ui files. This does not mean the UI cannot expose it: the generic raw drawer displays all keys. Unknown clients may depend on the old response; do not invent them or claim compatibility.

Versioned response projection necessity is an owner decision after client inventory. Endpoint path, request and answer semantics may stay V1, but deleting nested fields is a response-schema change. Require documented release/migration impact. If versioning is chosen, only safe approved schemas may be served; do not create a new body field/route unnecessarily or restore private fields for compatibility.

## 11. Designed leakage/security test plan

All scenarios below are **DESIGNED_NOT_IMPLEMENTED_NOT_RUN**. No test file was created, no runtime tests or regression were executed.

Shared future assertions: exact approved root and nested keys; exact six trust keys and values on successful responses; legitimate response/citations preserved; no forbidden root or duplicated internal path; controlled sentinels absent from serialized public payload; original input structures unmutated. Do not blanket-ban ordinary answer words such as “policy”: test object paths and deliberately internal sentinels, with separate approved-current-request fixtures.

| ID | Scenario | Proposed fixture/verification | Status |
|---|---|---|---|
| T01 | Deterministic/local-rule | Synthetic helper-return fixture only: current _deterministic_response returns None. Do not enable feature in production just to test it. | DESIGNED / NOT_RUN |
| T02 | Evidence fast path | Mock controlled applicable intent/evidence and available provider; verify unchanged answer and guard result. | DESIGNED / NOT_RUN |
| T03 | Ollama generation | Mock provider output with supported public answer; verify trust values unchanged. | DESIGNED / NOT_RUN |
| T04 | Offline response | Provider unavailable, preserve bounded message/status; same projection. | DESIGNED / NOT_RUN |
| T05 | Unsupported claim | Guard rejects unsupported answer; abstention preserved; rejected sentences not serialized. | DESIGNED / NOT_RUN |
| T06 | Missing evidence | No citations -> existing abstention/missing-evidence behavior; no invented answer or facts. | DESIGNED / NOT_RUN |
| T07 | requires_human | Controlled trust flag true; flag preserved, no false claim of completed approval. | DESIGNED / NOT_RUN |
| T08 | Policy-sensitive request | Inject controlled policy result via test double; endpoint itself uses action=answer. Verify no policy object/sensitive state leaked; do not claim action authorization tested. | DESIGNED / NOT_RUN |
| T09 | Empty/partial gate context | Missing/null/partial context and malformed nested members; unknown fields cannot become public; validate safe defaults/no passthrough. | DESIGNED / NOT_RUN |
| T10 | Generic route error | Injected internal sentinel exception text -> reviewed generic500 detail, no sentinel/traceback/context. | DESIGNED / NOT_RUN |
| T11 | Provider/timeout/validation errors | 503/504/provider503/framework422 with controlled sentinels; verify bounded error projection and preserved status; validation sentinel input not echoed if rejected by approved policy. | DESIGNED / NOT_RUN |
| T12 | Duplicate orchestration and developer snapshot | Inject different sentinels under gate_pipeline.orchestration.data and developer_core.orchestration.data/gates/observability; absent in output. | DESIGNED / NOT_RUN |
| T13 | Future unknown field expansion | Add deeply nested fake internal fields including innocuous unknown names; output equals explicit root and nested allowlist. | DESIGNED / NOT_RUN |
| T14 | History privacy and current-session identity | Preload synthetic previous-turn/metadata markers under both memory paths; no history visible, current session echo only; does not prove owner binding. | DESIGNED / NOT_RUN |
| T15 | Public data and consumers | Preserve response text, exact six trust fields and approved citation content/IDs, UI intent/goal/model/latency and X-Request-ID; inspect reduced raw JSON and explicitly document legacy script impact. | DESIGNED / NOT_RUN |
| T16 | Nonmutation/citation/error bounds | Assert original context/evidence/trust assessment unmutated; unapproved citations excluded; reviewed types/bounds; malformed input does not trigger raw stringify fallback. | DESIGNED / NOT_RUN |

Required negative paths include gate_pipeline.reasoning/policy/memory, developer_core.observability.policy_decision, reasoning.facts/inferences/explanation and both orchestration mirrors. Whole serialization checks must catch renamed/unknown nested internal markers as well as named paths.

No production DB/model is needed for designed projection tests: use synthetic context and controlled provider/engine fixtures. A future authorized change requires targeted tests first, then appropriate regression because actual source would change. This command has no source change and cannot claim those results.

## 12. Optional diagnostic authorization boundary

If Option B is later selected: authenticate a server-verified principal; explicitly authorize role/scope and session ownership; minimize/redact payload; audit access/denial with retention rules; reject caller-supplied roles; never authorize using confidence, requires_human or session labels. No raw internal state returns from ordinary chat. Any diagnostic endpoint/auth design is a separate approved work item, not implemented here.

## 13. Expected implementation scope, subject to explicit authorization

| Proposed file | Reason | Approval scope |
|---|---|---|
| app/api/routes.py | Local explicit root/nested response projection and safe generic local500 detail; preserve engine/provider/request path | Primary proposed change; NOT GRANTED |
| tests/test_v1_response_projection.py | New directly required security/response branch tests | Planned filename only; file not created; NOT GRANTED |
| app/exceptions.py | Only if shared/framework error review cannot be contained in route; strictly conditional `/v1/chat` handling | Optional separate explicit approval; prove other endpoints including `/v2` unchanged |

No other code location is necessary for the primary success projection based on current evidence. Standalone legacy script migration/diagnostic UI changes require a separate owner impact decision; not part of silent primary implementation scope. Do not add a second configuration source or projection engine.

Forbidden: engine rewrite/replacement, ModelRouter introduction, MemoryEngine owner-binding/TTL redesign, TrustEngine/schema change, PolicyEngine merge, Agent/registry/LangGraph/Graphify runtime, KB promotion/migration, config authority, `.env`, Docker, `/v2`, test weakening, existing contract/checkpoint/history rewrite, global reset or production deployment.

## 14. Risk ratings

| Dimension | Rating | Reason and proposed mitigation |
|---|---|---|
| Security | BLOCKING | Raw reasoning/policy and duplicate snapshots remain exposed today; exact root/nested allowlist with branch/error/sentinel checks needed. |
| API compatibility | HIGH | Legacy nested script assertions/raw diagnostic drawer change; unknown clients NOT_PROVEN. Require owner-reviewed schema/release impact. |
| Privacy | HIGH | Previous turns/unreviewed citations and raw rejected text can be exposed. Exclude all mirrors and approve citation/identifier disclosure. |
| Architecture | LOW | Proposed outbound boundary remains within route and preserves engine truth; optional shared error scope raises separate review need. |
| Regression | MEDIUM | Branch/context/error/type handling can differ. Designed targeted tests plus future authorized regression are needed. |
| Rollback | HIGH | Previous route is already leaky; restoring it publicly reopens CC-01. Hold isolated candidate/release rather than insecure compatibility rollback. |

## 15. Safe rollback proposal

No rollback is executed. Before a future authorized patch, record exact working-tree backup/hash for only approved files, including pre-existing edits. On candidate failure, restore only approved changed hunks/files after comparison with later edits; preserve DB, config, contracts, test/history evidence and backups. Never reset the whole working tree.

The baseline route is not a safe public privacy rollback. If restoring it is needed to investigate a candidate, keep that investigation isolated and hold release; obtain a reviewed safe response recovery before public exposure. No service shutdown, deployment or emergency production change is authorized by this proposal.

## 16. Preservation and validation

Git status before/after, protected file hashes, creation inventory and `.env` metadata checks are recorded in the JSON. Expected new files are only the two proposal artifacts. Original eight contracts, historical reports/XML/checkpoints and all protected source/test/database/Docker files are preserved. Unreadable historical temp paths are listed; they were not modified or treated as fully audited.

Read-only checks validate source AST shapes, six trust fields, file references, classification/risk enum values, test-plan coverage, JSON schema requirements and artifact-only changes. No runtime compliance, new test PASS, acceptance improvement or remediation completion is claimed.

Progress/resume rule lives in the new JSON; if interrupted, resume only unfinished proposal steps and do not touch existing checkpoints. Stop after these artifacts; CC-01 remains HIGH / BLOCKING.

## 17. Approval gate

Approve exact public/citation fields and compatibility/versioning impact first. Any optional error-handler work needs its own path-limited authorization. Running this command grants analysis/proposal permission only.

IMPLEMENTATION AUTHORIZATION = NOT GRANTED

NEXT STEP =
Owner review
→ Impact approval
→ Explicit implementation authorization
