# HDG-R2-A9-AUTH-001 — Discovery/design report

**Task status: DISCOVERY/DESIGN COMPLETE. Implementation: NOT AUTHORIZED / NOT PERFORMED.**
**R2-A8 = BLOCKED / NOT_VERIFIED. Full Runtime Identity = NOT_VERIFIED.**

The minimum proposed design has five parts:

1. Trusted actor/session: a Windows OS-authenticated local operator confirmation adapter; browser decisions remain intentions. Reviewer is derived from the authenticated peer account/session, not client JSON. Existing shared admin token alone is insufficient for individual attribution.
2. Audit reuse: one private ATTESTATION process-memory owner of the existing AuditTrail and ApprovalQueue classes. NORMAL audit and v2 owners remain unchanged. No new audit implementation, persistence subsystem or production sink.
3. Binding: immutable server-generated evidence version joined to exact scope, actor/session, PID/start time/runtime instance, SOURCE_SNAPSHOT, SCOPED_LOADED_CODE and server expiry. ACTIVE_PROCESS_BUILD remains NOT_DIRECTLY_VERIFIED. Current model is only an immutable execution constraint; actual_model comes from genuine provider evidence later.
4. Permit bridge: separately explicit decision/arm/execute confirmations, existing queue consumption, server-only token holder, direct controller invocation and existing single dispatch. No token in UI or self-HTTP. Add a future terminal abort operation because current finish() cannot revoke ARMED. Include new helpers in scoped loaded-code coverage and preserve final-send distinctions.
5. Protected-state boundary: ATTESTATION-only adapter/owner, no v2 import/KnowledgeEngine/production audit/database/sidecars, and a scoped evidence projection that avoids the existing protected-file digest path.

Source findings also require redaction-safe audit identifiers/digests and semantic validation: AuditTrail redaction may modify 16-digit runs or sensitive/deep fields. Queue and audit expose mutable references internally, so the private owner must not expose them as authoritative client objects. Existing queue/permit transitions are not a joint transaction; failure ordering must be fail-closed.

This recommendation is concrete but conditional. Human approval must select the permitted OS actor/session policy, accept memory-only audit limitations and explicitly authorize the candidate implementation files. OS adapter feasibility is not verified; it must pass isolated Windows tests before any live use. If browser-only authority or durable audit is required, the proposed minimum does not meet that requirement and must be revised.

Detailed outputs: DISCOVERY.md, ACTOR_SESSION_DESIGN.md, AUDIT_OWNERSHIP_DESIGN.md, BINDING_AND_PERMIT_DESIGN.md, PROTECTED_STATE_AND_SECURITY.md, IMPLEMENTATION_PLAN.md and DESIGN_VALIDATION.md. SOURCE_BEFORE/SOURCE_AFTER/SOURCE_COMPARISON and Git discovery provide disk/Git evidence. No executable code was created, no UI/backend/configuration was edited, no IPC channel was opened, no runtime probe/live HTTP/arming/restart/generation was performed, and no protected data or authorization/gate record was changed.

STOP for the user's required separate decision: **AUTHORIZE MINIMUM R2-A9-AUTH IMPLEMENTATION**. This report is a design artifact, not an authorization or status promotion.
