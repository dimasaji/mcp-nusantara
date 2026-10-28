# Minimum implementation plan — NOT authorized to MODIFY

This plan is a reviewable proposal. No listed source/test file is created or changed by discovery/design. Before MODIFY the human must explicitly authorize the exact selected scope.

## Recommended minimum and acceptance boundary

Extend the existing observer to bind actual diagnostic/provider code objects and expose a bounded in-memory receipt. Add one conditional, local diagnostic generation route using the real existing provider with a one-dispatch transport and explicit operator permit. Use a reviewed protected-state-free initialization profile on the same `app.main:app` entrypoint. Keep normal API, Core/Hermes, provider/model selection, configuration files, RAG and database untouched.

This can enable a future **scoped** application/provider correlation. It does not establish full build provenance or normal `/v1/chat`/Hermes execution. No active-process-build or Runtime Identity promotion is proposed.

## Exact proposed file inventory

| File | Action after approval only | Current role / proposed minimum change | Main risk |
| --- | --- | --- | --- |
| `app/core/runtime_correlation.py` | NEW | Small immutable request/receipt types, process-owned single-use permit/slot, atomic dispatch transport and explicit loaded-object manifest bindings | Concurrency/arming errors; avoid a new governance owner or persistent ledger |
| `app/api/runtime_verification.py` | NEW | One conditional local `POST /v1/runtime/verification`; real provider call, identity join, receipt-only response and diagnostic response-send observation | New generation attack surface; disabled without reviewed permit, no unrestricted client input |
| `app/core/runtime_attestation.py` | MODIFY | Reuse process metadata; expose freshness nonce and diagnostic scoped-code bindings/final memory observation with honest build/receipt status | Must remain GET-only/read-only, no generation, no prompt/content leak |
| `app/main.py` | MODIFY | Install the conditional diagnostic capability and ASGI send hook; use existing evidence-only composition to avoid protected owners, privately obtain same snapshot only when explicitly approved | Diagnostic profile differs from normal composition; preserve normal handlers/middleware and Control Plane state |
| `app/models/ollama.py` | MODIFY, narrow exception requiring explicit approval | Add optional documented client injection and ownership handling; normal callers retain existing defaults and result schema | This is a provider transport extension, not a provider/model replacement; no existing generation/health semantics redesign |
| `tests/test_runtime_correlation.py` | NEW | Request/context/permit/receipt/process/code drift/concurrency unit tests | Test evidence only, not live runtime verification |
| `tests/test_runtime_verification.py` | NEW | Isolated ASGI/provider transport/response-send/safe boot integration and non-mutation tests | No real listener, DB or actual model calls |
| `tests/test_runtime_attestation.py` | MODIFY | Add new observer fields and scope compatibility assertions | Preserve original cases and statuses |

No changes proposed to `app/core/runtime_identity.py`, `app/models/base.py`, `app/observability/context.py`, `app/observability/logging.py`, `app/hermes/agent.py`, `app/api/routes.py`, `app/api/v2_routes.py`, RAG/SQLite/configuration/Control Plane owners, dependencies, service scripts or protected authorization records. Existing identity and request context are reused. If implementation reveals additional files or behavior changes are needed, STOP and revise the plan before editing them.

The client-injection exception and the new route are intentionally called out: they are not allowed now and require explicit approval. If either is rejected, receipt-only passive observation can be implemented under a smaller scope, but will not unblock protected generation.

## Proposed execution sequence after a new implementation approval

1. Record exact HEAD/worktree and owned-file backups/hashes; preserve all human changes. Confirm the approval selected all unresolved decisions below.
2. Write request-local correlation types and atomic one-use state first. No arming or network operation during initialization/tests unless fixture-owned.
3. Add narrow provider client injection with compatibility tests; install isolated new route/observer/send hook using actual object binding. Do not alter existing chat/dev handlers.
4. Prove diagnostic initialization never imports protected owners and uses the existing snapshot without replacing provider/model/config values. Missing snapshot, unknown provider/origin or missing permit fails closed.
5. Run isolated unit/integration/regression checks, review exact owned diffs and verify source/protected-state non-mutation. Keep live generation count zero.
6. Save implementation evidence, scoped limitations and rollback instructions. Run AST-only Graphify update under AGENTS.md only after authorized source changes.
7. STOP. A service load and R2-A8 live protocol require a separate explicit lifecycle/live authorization and enumerated HTTP request budget.

## Future test strategy

- Existing 135-case R2-A7 regression baseline plus declared new tests; run only after implementation authorization. No tests executed in this design task.
- In-process ASGI exercises actual `app.main` profile and separately mocked transport fixtures; label mocks as tests, never live provider proof.
- Non-mutation guards cover initialization, dispatch, middleware send, shutdown, file writes/DB connections/subprocess/model-health calls and unsafe imports. Test imports may read approved source/config fixtures only; no protected DB open/hash.
- Duplicate/concurrent request IDs, malicious caller IDs, stale PID/instance/nonce, code replacement, missing/malformed model/done/identity and forged request/receipt joins must fail before I/O where possible.
- Atomic permit exhaustion under concurrent POST, redirect refusal, zero retry, invalid origin/path/method, environment-proxy refusal, cancellation/timeout/malformed response and errors: at most one transport dispatch; no automatic re-arm.
- Response construction is not send proof; test failed/disconnected ASGI send and external client observation separately. No raw prompt/response/secrets in receipts/errors/log additions.
- Existing provider normal-client behavior remains unchanged with no injected diagnostic client. Client ownership/close must not affect another request.
- Verify no modified AST/semantics for protected V1/V2 endpoints and default composition. Diagnostic profile exclusions and honest full-build false are acceptance criteria.

## Rollback strategy

Design-only rollback requires no source reversal: retain these documentation artifacts. For future implementation, retain exact owned preimages/patches; reverse only reviewed owned edits, preserving inherited changes. Remove newly introduced owned files only under explicit authorization; no Git reset/clean/global restore. Do not rollback DB, sidecars, provider state or configuration. Restoring source does not restore running code; any process load/rollback is a separate human lifecycle decision, and normal boot can touch DB.

## Human Decision Gate before MODIFY

**Requested decision: AUTHORIZE MINIMUM REMEDIATION IMPLEMENTATION — not yet given.**

Required selections:

1. Accept the scoped diagnostic claim; full Runtime Identity/ACTIVE_PROCESS_BUILD and normal Hermes/RAG remain NOT_VERIFIED.
2. Approve the exact eight-file inventory, new local generation surface and narrow provider client-injection extension, with normal production paths unchanged.
3. Select a trusted process-local permit-injection/arming channel; do not authorize an arbitrary HTTP arm endpoint or persistent authorization mutation by implication.
4. Approve diagnostic initialization profile boundaries and external model-daemon filesystem scope. No lifecycle/environment/configuration change is part of implementation authorization unless explicitly added.
5. Keep restart/load/live HTTP/generation excluded until their own concrete authorization.

If these decisions are missing, ambiguous or rejected, remain WAITING_HUMAN. Do not move from DESIGN to MODIFY merely because a solution is described.
