# NUSANTARA Control Plane V1

Status: IMPLEMENTED_SCOPED / V1 HOLD — 2026-10-09. The implementation addendum below supersedes the 2026-10-08 discovery statements where explicitly stated. It does not grant production authority or certify V1 acceptance.

## Existing authority and implementation

Hermes remains the V1 core. `Settings.effective_configuration` owns the immutable, compose-once `NusantaraConfig`. V1 creates `OllamaProvider` from that snapshot; the existing `ChatRequest.model` can override the technical model for one request. This is not a Control Plane profile selector. No second engine, configuration owner, V2 insertion, dependency change, automatic `.env` write, deployment or production restart is authorized here.

The existing Control Plane supplies evidence, review and authenticated inspection preview. It has no effective settings selection consumed by `/v1/chat`. Its governance evidence must remain distinct from executable runtime authority.

## Human-facing capability contract

The assistant home and chat should use Indonesian labels, show answers and available citations, and explain when a response needs verification. Technical provider IDs, grounding, retrieval and runtime identity belong in developer details.

| User choice | Required runtime meaning | Current disposition |
| --- | --- | --- |
| Model AI: Cepat, Pintar, Hemat | Approved profile resolves to an available actual model; chat generation consumes that identity | Not enabled: profile mapping and selection owner undecided |
| Cara bekerja: Otomatis | Existing V1 branch selection, with its mandatory safety checks | Existing internal behavior; no selectable Control Plane control |
| Cara bekerja: Langsung, Teliti | Approved direct/evidence behavior consumed by chat, preserving required checks | Not enabled: selectable modes do not exist |
| Dokumen Nusantara | Retrieval restricted by the approved document/source policy | Not selectable: search filter currently ignored |
| Informasi resmi | Approved source authority, jurisdiction and validity, with sufficient official oracle | Not enabled: official oracle remains incomplete |
| Internet | Existing authorized search capability actually consumed by V1 | Not enabled: V1 chat integration not established |
| Tingkat jawaban: Cepat, Seimbang, Sangat teliti | Explicit supported runtime parameter behavior and tests | Not enabled: mapping not established |
| Membaca, mencari, merangkum | Actual supported capability with source and access boundaries | No blanket new permission granted |
| Mengirim pesan, mengubah data, menjalankan tindakan | Explicit approval tied to the exact operation and enforced before its side effect | No enabled risky control until enforcement is proven |

No selector may store preferences only in the browser while presenting them as runtime settings. Unsupported options must not be enabled. A missing policy, unavailable model, invalid selection or insufficient authority must not silently fall back to a different promised capability.

## Required mapping and receipts

Human intent must map through a controlled API to the existing runtime authority and actual provider/execution path. The API must report selected profile, effective provider/model, availability, validation and configuration provenance. Availability must be marked unverified until observed; fixture results cannot establish installed model availability.

Changes require defined selection scope, ownership, authentication, lifetime, concurrency and reset behavior. A receipt must describe what the current chat request actually consumed, without leaking private gate, memory, policy or orchestration objects through the existing public chat response.

## Memory boundary requiring review

V1 currently captures user and assistant content under client-selected session identifiers, including the shared default `web`. Answer policy is evaluated after the user write. The V2 `SessionMemory` adapter is not a V1 substitute.

Before enabling memory, define authorized READ and WRITE, rejected operations, consent, session ownership, retention, provenance and NO-MEMORY behavior. The safe desired boundary is no access or capture where authorization is absent. Existing V1 capture cannot be described as satisfying that boundary. A change to existing conversation behavior requires a reviewed V1 policy rather than an invented replacement memory owner.

## Decisions needed before implementation

1. Define profile mappings using supported model identities and specify request/session/operator-wide selection. Define how the existing compose-once owner handles these selections without a second source of truth.
2. Define Langsung and Teliti behavior, mandatory safety stages, and missing-evidence handling within Hermes/V1.
3. Define V1 memory consent, ownership and retention, including whether existing automatic capture is disabled.
4. Define source-filter grammar, approved metadata authority fields and enforcement before scoring/top-k. Supply approved official snapshots for unresolved oracle cases.

These are blockers, not assumed implementation choices. Implementation stops on these blockers under the user directive. No cosmetic UI controls or duplicate settings API are added pending resolution.

## Acceptance boundary

Required proof includes UI selection → API receipt → effective runtime selection → actual chat consumption for two model profiles and supported modes, source-policy enforcement, and approval enforcement for risky operations. Tests must preserve existing work and block uncontrolled external effects. Controlled fixture tests and live integration are reported separately.

V1 remains HOLD while any mandatory memory, source/oracle, security, deployment/runtime, Control Plane or E2E gate is unresolved. Hermes freeze is permitted only after V1 acceptance PASS. This document does not authorize V2 work.

## Implementation addendum — approved decisions, 2026-10-09

Approved model control is OPERATOR_GLOBAL_MODEL_SELECTION. Approved memory disposition is LEGACY_BEHAVIOR_PRESERVED_TEMPORARILY. Hermes remains the core and V2 remains deferred.

### Model lifecycle and authority

The existing Settings owner retains immutable snapshots. Bootstrap composition remains once-only. Its locked model-selection operation validates and replaces only the LLM model leaf and records an operator revision. All other configuration leaves remain unchanged. Legacy model readers on the same owner are aligned. There is no new registry, configuration owner, configuration file or `.env` write.

The authenticated local NORMAL API uses the existing Ollama adapter's actual inventory. Invalid/unavailable choices, stale revisions, inventory failures and non-single-worker declarations are rejected. CAS rechecks the validated snapshot and revision after inventory I/O. No optimistic Console state is promoted as applied before the API succeeds.

Selections are volatile and authoritative for subsequent V1 requests **in this process**. An in-flight request retains its captured snapshot. There is no claim of cross-process consistency or restart persistence; multiple declared workers reject selection. Operator-global deployment requires a verified single worker. An external launch configuration could differ from the declared worker count and must be verified independently.

The existing technical `ChatRequest.model` field is retained for compatibility only when it matches the active model; a conflicting per-request override returns 409. The user UI sends no model override. No Cepat/Pintar/Hemat profiles or selectable execution modes are invented.

Endpoints in the existing Control Plane:

- GET `/v1/control-plane/model-status`: safe local status, owner revision, process/source diagnostic and last successful V1 request metadata. Availability is NOT_VERIFIED unless explicitly observed; source fingerprint is not a full loaded-build or weight attestation.
- GET `/v1/control-plane/models`: authenticated provider inventory; no generation or model installation.
- POST `/v1/control-plane/model-selection`: authenticated selection with `model` and `expected_revision`; returns APPLIED only after inventory validation and owner commit.

### Execution and UI

`POST /v1/chat` captures the existing owner snapshot, constructs its provider, invokes `HermesAgent.execute_v1`, projects `V1CoreResult` through the existing public projector, and closes the provider. Hermes owns the relocated existing V1 pipeline and uses its existing `run` entry point for language/problem/reasoning. Knowledge, trust, gates, legacy memory, safety branches and grounding use the existing owners. The route does not call provider generation directly. Internal gate/memory/reasoning objects remain outside the public response.

The existing React application serves user chat at `/` and the separate operator panel at `/console`; existing acceptance/evidence views remain available. The backend serves the existing compiled bundle and assets in NORMAL mode. Rebuild the frontend after changes using installed project tooling, without deployment or dependency changes. Missing bundle returns 503 rather than a fake ready UI. The previous legacy HTML is retained; ATTESTATION/evidence behavior is preserved.

Chat history is transient browser component state and existing server memory; there is no new persistence mechanism. The existing memory write-before-answer-policy behavior, client session ownership and retention remain open CC-05 risks. No history is deleted or migrated.

### Knowledge boundary and evidence limits

Nonempty filters are now rejected at facade and HTTP boundaries; empty/default search retains canonical retrieval. This prevents silent unrestricted search, but does not implement an unapproved authority/filter grammar. Official oracle cases remain REVIEW_REQUIRED/MISSING until issuer, jurisdiction, validity and ingest authorization evidence exists.

Evidence under `docs/reports/v1-user-hermes-implementation/` separates guarded unit/HTTP regression and localhost browser flow from complete semantic-worker, official knowledge and production verification. The first browser candidate uses explicit provider transport, semantic and retrieval fixtures with actual V1 handlers/Hermes. A second candidate uses the existing local Ollama provider and its installed `llama3.2:1b`, with semantic/retrieval fixtures still explicit. Its selected, payload and provider-reported model identities match, and the user receives the projected grounding abstention. Only one actual model is installed; switching between distinct real models remains unverified. The initial second-candidate failure was a test receipt-observer calling-convention error; its evidence is retained separately. These observations do not establish full runtime readiness, official source authority, production deployment or V1 acceptance. V1 remains HOLD.
