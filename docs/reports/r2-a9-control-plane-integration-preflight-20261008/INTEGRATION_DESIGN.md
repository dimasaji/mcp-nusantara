# Minimum integration design — proposed, not implemented

## Typed evidence and UI reuse

Keep NORMAL SystemHealth unchanged. Add an explicitly versioned ATTESTATION projection contract and discriminated frontend parser; reject malformed/unknown variants. Never pad scoped evidence with fabricated phases, R3 gates, protected hashes or PASS statuses. Missing evidence is unavailable, not healthy. Shared engineering pages must guard the variant before using SystemHealth fields.

Reuse System/Evidence/Test/Review/Decision routes. Show target, PID/start, runtime instance, SOURCE_SNAPSHOT, SCOPED_LOADED_CODE, ACTIVE_PROCESS_BUILD=NOT_DIRECTLY_VERIFIED, evidence version, scope, server expiry, live lock and operator-policy availability. Label data provenance. Client fetch time is not server evidence time; UI bundle build is not backend loaded-code proof.

Separate three records: historical automated isolated results, explicit human display observations, and verified server decisions. Existing UI acceptance decisions remain session-only in NORMAL. For ATTESTATION, acknowledgement/checklists prepare an intention; they must not approve authority. Clear preparation when server version/process/session/scope changes. Expiry and authoritative eligibility are server checks even if UI clocks are wrong.

The foundation version hashes runtime/scope material; it currently excludes receipt/review changes and capture time. Keep that binding meaning explicit. Use a separate server-generated presentation/receipt revision if needed to invalidate a human review after material evidence or decision changes; do not silently redefine existing binding semantics. Review expiry is per review, not the generic capture timestamp.

## Browser intention boundary

Proposed path: POST /v1/control-plane/intention, ATTESTATION only. This is a design candidate, not an existing endpoint. Accept only exact scope, reviewed server evidence version and a bounded presentation reference as needed; reject actor/reviewer/PID/token/model/provider/override/ARM/EXECUTE fields. TTL is server-owned. No prompt or arbitrary notes need enter authority/audit.

Validate expected evidence version and create intention inside one owner lock before queue/audit mutation; reject stale submissions instead of rebinding silently to newer evidence. Return only detached review_id, state=PENDING, evidence_version, exact scope and expiry. No permit, mutable queue, audit object or native capability crosses HTTP. Reuse existing owner/queue/audit, no secondary ledger.

Submission must be explicit, with no polling-driven POST, automatic retry or replay. Browser duplicate suppression alone is insufficient. Design bounded server deduplication tied to exact reviewed context, reject capacity exhaustion safely, and ensure unauthorized/flooded requests cannot poison a valid decision or consume all audit capacity. Define concurrency behavior before implementation.

Loopback and Origin restrictions prevent some cross-origin misuse; neither authenticates a Windows actor. Keep decisions on verified native IPC. Browser requests must never construct VerifiedPeer, choose the reviewer or cause the server to authenticate itself as the operator on their behalf.

Exact browser Origin/Host/port and proxy behavior must be exercised with isolated request fixtures. Existing snapshot checks only local hostnames; a future mutation requires stricter Origin handling, null/missing-Origin policy, bounded content types/body, and peer constraints. Source CORS allows 3000/8000, not 5173. Existing Vite same-origin proxy may avoid browser cross-origin CORS, but it does not erase the incoming Origin or establish authority. Do not broaden global CORS/configuration as a shortcut. Snapshot/attestation target semantics remain distinct.

## Decision visibility and operator lifecycle

Expose bounded authoritative summaries from frozen server records, correlated to review/version/scope/expiry and audit integrity. If a timestamp or audit reference is needed, use the existing ledger's data; do not invent a decision timestamp from the latest GET time. Existing projection exposes only review_id/state/expires_at; actor reference, reason and binding context require a reviewed projection addition. Never expose raw SID/logon identifiers, tokens, secrets, prompt/response content or mutable ledger entries. Audit reference encoding must preserve the established redaction-safe behavior.

The current install supplies no OperatorPolicy, channel creation or worker loop. Show NOT_PROVISIONED and server confirmation unavailable truthfully. A future native operator interface must present the exact review/scope/version and operation for explicit confirmation, pin server identity and use existing peer/nonce validation. That provisioning/helper/lifecycle work is a distinct design/authorization gate. No shared secret, browser-only actor, self-HTTP or automatic confirmation substitutes for it.

## Live and protected-state boundary

Do not introduce an ARM/EXECUTE UI or HTTP endpoint in minimum integration. Installed owner remains live-locked, including after APPROVED. A successful intention or verified decision never means Runtime Identity VERIFIED. Existing MockTransport-only execution cannot be converted into live execution by UI work.

ATTESTATION must never call NORMAL project(), protected digest, KnowledgeEngine, v2_routes, SQLite or production audit owner. Do not combine NORMAL and ATTESTATION snapshots by fetching both. NORMAL source behavior stays unchanged but must be tested with synthetic roots/stubs, avoiding protected real-root fixtures. No live service/profile change is required for isolated validation.
