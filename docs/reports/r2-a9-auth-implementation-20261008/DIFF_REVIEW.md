# Owned diff and limitations

New executable artifacts: app/security/local_operator.py and tests/test_local_operator_identity.py only. Existing app/UI/NORMAL/configuration/public endpoint/audit/queue/provider files remain unchanged across 375-file comparison. New report directory contains the standalone token feasibility probe and evidence; it does not become a startup script or authorization record.

Adapter is unintegrated and unvalidated. It has no auto-listener, HTTP route or permit issuance. It requires explicit construction/policy. Synchronous IPC I/O and trusted policy provisioning would need full isolated validation and bounded lifecycle handling before integration; that work was stopped, not waived. No UI objects or reviewer JSON currently acquire authority through it.

The failed PID association prevents a claim of complete server/peer/process binding. Ownership/audit/decision/permit integration has not begun. Do not deploy or use the adapter for live authority. No cleanup or rollback of inherited state was performed; these new files are retained for human review.

Graphify AST-only update is required by AGENTS.md after code additions. Its output is a derived graph change, not application configuration or runtime promotion. No graph/provider model API was used.
