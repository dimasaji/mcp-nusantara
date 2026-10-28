# Architecture review

Graphify query for decision/approval/audit/control-plane relationships was used first, followed by scoped source inspection. Existing graph was not regenerated because no code changed.

`app/api/control_plane.py` exposes a local GET-only snapshot. `app/core/control_plane_projection.py` reads historical engineering artifacts and Git metadata; it also hashes production SQLite/WAL/SHM paths. It was inspected as text, never invoked. Current R2-A8 profile evidence is not projected through that schema.

`app/security/auth.py::require_admin` fails closed when the configured shared secret is absent or wrong. That authenticates possession of a shared secret, not a server-established individual reviewer/session. `app/api/v2_routes.py` passes body.reviewer into ApprovalQueue.decide. Queue prevents requester/reviewer string equality, but those strings do not establish human identity.

`app/approval/audit_trail.py` is an existing append-only, redacted, hash-chain JSONL/in-memory primitive; it is not a SQLite audit implementation. `ApprovalQueue` supplies payload hashes, expiry, snapshots and one-use consumption. Reuse candidates exist. The gap is trusted actor attribution and ownership/integration for R2-A9 in the protected ATTESTATION composition, not absence of an audit class.

The existing durable instance is constructed inside v2_routes together with KnowledgeEngine and other NORMAL owners. Importing that module from ATTESTATION conflicts with its protected-state boundary. Creating a second audit subsystem or arbitrary new production audit file is not a permitted workaround. Existing standalone developer approval_controller writes change_plan/approval_result and labels HUMAN without authenticated session; it is not runtime arming and was not executed.

R2-A8 provides one-use, PID/runtime-bound permit and a fixed provider request. grant() is trusted programmatic only. No inspected Control Plane path binds a human decision and evidence version to that permit. A server-owned bridge is required, but actor/audit prerequisites are unresolved. STOP under contract §27; do not load v2 or expose permit to browser.
