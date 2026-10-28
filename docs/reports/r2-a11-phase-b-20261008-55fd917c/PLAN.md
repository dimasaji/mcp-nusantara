# Phase B pre-modification plan

Scope: isolated receipt assessment only. Keep existing public CorrelationReceipt schema, authority, configuration and send semantics unchanged. Preserve Phase C0 source mismatch and all historical artifacts.

Prove missing assessment API with new pure receipt tests before changing application source. Minimum files: app/core/runtime_correlation.py (immutable server observation and fail-closed assessment); app/api/runtime_verification.py (capture internal process-start/time/provenance alongside stored receipt, assess against current process/instance/code, include helpers in scoped code coverage); tests/test_runtime_correlation.py and tests/test_runtime_verification.py (synthetic validation and no-dispatch controller tests). No other application/test files proposed.

Required cases: PID reuse/start mismatch, instance/source/scoped/provider/endpoint conflict, missing/fixture receipts, expired/future/insufficient observation, send versus provider evidence. Synthetic valid cases test logic only and do not constitute provider-confirmed evidence. No permit, ARM, IPC, policy, provider invocation or generation, even through mocks, will run. Existing tests needing these operations are outside this runner's selected subset; retain their assertions unchanged.

Runner adapted from existing report-owned guarded pytest runner: new output destinations, same health AST isolation, add explicit guards against grant/native/provider operations, only select inspected safe cases. No active service HTTP. New report directory only. Historical results remain historical, not rerun claims. Rollback only approved file edits against saved exact copies; never reset inherited work or touch live service.
