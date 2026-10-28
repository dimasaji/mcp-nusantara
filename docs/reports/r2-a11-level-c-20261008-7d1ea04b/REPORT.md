# R2-A11 Level C — minimum fail-closed correction

**PASS_SCOPED: minimum receipt-assessment correction, unchanged B2 acceptance tests and safe isolated regression. STOP.** This is the user's scoped engineering Level C authorization, not permission for live Phase C operations.

## Baseline and exact change

Read B2 findings/runner and current receipt_assessment before modification. Root C:/Users/dmaza/mcp-starter, branch codex/fullroot-control-20261007, HEAD 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab independently confirmed. Staged paths empty. Same 26 inherited tracked modifications before/after; no assumption of a clean worktree. GIT_BEFORE.json/GIT_AFTER.json preserve actual state. Existing venv interpreter Python 3.13.15 confirmed.

**Only app/api/runtime_verification.py changed.** Move the existing assess_receipt return and all its context argument evaluation inside the existing try/except Exception boundary. No algorithm, receipt field, public endpoint/schema, UI, configuration or authority mechanism was added. Missing process keys, None process objects and malformed runtime instances now produce the existing bounded CURRENT_CONTEXT_UNAVAILABLE assessment with status NOT_VERIFIED, correlation_valid=false and false send/client flags. Exception text is not exposed.

The original defect was argument evaluation outside the handler: B2's {} observer caused KeyError and None caused TypeError. B2 FOCUSED.xml remains historical evidence of that failure; its acceptance test file is used directly, not edited/copied into a weakened assertion. This patch also handles failed current-context property access inside that same boundary. Invalid receipt data still uses the existing assess_receipt validation/reasons; success stays NOT_VERIFIED at full identity scope.

## Verification

Focused run: **23 passed, 0 failed/errors/skips/deselected, 0 warnings**. Includes all 19 unchanged B2 tests plus four report-owned context-failure cases (runtime instance None/dict/object, raising process observer). Both previously failed IDs now pass unchanged:

```text
docs/reports/r2-a11-phase-b2-20261008-9fb4e38a/test_b2_integration.py::test_incomplete_process_observer_fails_closed[result0]
docs/reports/r2-a11-phase-b2-20261008-9fb4e38a/test_b2_integration.py::test_incomplete_process_observer_fails_closed[None]
```

Safe regression: **39 passed, 0 failed/errors/skips, 81 deselected, 1 inherited Starlette/httpx deprecation warning**. Runtime correlation assessment 29; runtime verification assessment/composition/public-route source preservation 6; attestation code-drift/protected-boundary/process integration 3; guarded Control Plane composition 1. Combined new execution totals: **62 passed**, no failures. Full regression and live provider integration are not claimed.

The 81 deselections cover cases outside the selected path, including permit/provider/policy operations prohibited here and unaffected tests already verified in Phase B. No assertions were altered, no dependency installed/upgraded and no warning suppressed. Complete parameter-expanded selected IDs are in focused_IDS.json and regression_IDS.json; XML files independently record executions. No prior report/evidence file was overwritten.

Commands from repository root:

```powershell
& .venv/Scripts/python.exe -B docs/reports/r2-a11-level-c-20261008-7d1ea04b/isolated_test_runner.py focused
$env:R2_A7_TEST_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a11-level-c-20261008-7d1ea04b\ISOLATED_ATTESTATION.json'
$env:R2_CPLANE_ISOLATED_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a11-level-c-20261008-7d1ea04b\ISOLATED_CONTROL_PLANE.json'
& .venv/Scripts/python.exe -B docs/reports/r2-a11-level-c-20261008-7d1ea04b/isolated_test_runner.py regression
```

Runner reuses B2 guarded infrastructure, existing pytest/pytest_asyncio, bytecode disabled, plugin autoload disabled and no cache provider. Each attempt has its own temporary directory/XML. Existing NORMAL composition uses synthetic API owners; guarded Control Plane composition is in-process ASGI only, with policy None, no permit, zero dispatch and LOCKED actions. It is a regression test, not new Control Plane integration or runtime activation.

Guard results: no prohibited operation violation observed. Grant/reserve/dispatch, provider generate/structured/health/list-model, native channel entry, real HTTP transport, SQLite and protected-file paths are blocked in runner. B2 fixture teardown verifies real DISARMED/zero-dispatch state and no MockTransport responder calls. Synthetic AST receipt creation/classification/storage excludes the full invoke lifecycle. Subprocess composition has its additional inherited protected-state/network guards. Guard evidence is Python-level, not exhaustive OS monitoring.

## Diff, historical integrity and security

SOURCE_COMPARISON.json: 380 monitored source/test/script/service paths, **one expected changed application file, 379 unchanged**. Existing repository tests and all inherited changes preserved. IMPLEMENTATION.diff compares the exact saved pre-task source, not a clean HEAD. HISTORICAL_STABILITY.json verifies unchanged B2 acceptance source, B2 failure XML and C0 raw response. No protected database/WAL/SHM file read/hash was used in this comparison.

Before source hash: 2451b55b8f39671de9c45f97733666ddbd889474ff2649feb82ebbbe6f36c770.

After source hash: e2dec6bc0ae0e8b6eaa2ab247834f0920a2014c083180a50de2f4a0484737069.

The small relocation reuses the already-scoped receipt_assessment helper, so no second authority, actor/model assertion, schema extension or audit owner appears. Its code object changes and future loaded-code evidence must reflect that change; the running service was not loaded/restarted. Registered/scoped coverage remains non-transitive, with the previously documented full-build/native/global/closure limitations.

Graph query used the existing graph before editing. AST-only graph update performed afterward per AGENTS.md; derived graph artifacts are separate from runtime state. Five inherited inaccessible report directories remain coverage warnings. No LLM/API/provider extraction or dependency operation performed.

Created artifacts in this fresh directory include runner, test_context_failure.py, pre-change source copy, source/Git manifests, historical checksums, selected IDs, focused/regression XML, isolated composition evidence, diff, test summary and report. FILES_CREATED.json inventories report files; pytest temp files are derived test artifacts. No existing repository test or historical evidence was modified.

## Limits and final state

No HTTP to an active service, active-process attestation, provider/model invocation/generation, permit/grant, ARM/EXECUTE, IPC/policy provisioning, source loading, restart/reload/deployment, dependency installation, protected-data operation, configuration change or Git reset/clean/staging/commit. No automatic remediation beyond this authorized function correction.

Synthetic trusted-context validation is logic evidence only; it does not prove a real provider receipt. AST integration excludes authorization/client/provider invocation. Safe NORMAL/Control Plane composition does not prove full production behavior. Private provenance is not cryptographic protection against arbitrary in-process modification. Timestamp/full-build/client-delivery limitations remain.

Phase C0's historical process SOURCE_SNAPSHOT and disk snapshot mismatch remains unresolved and preserved; source correction does not reconcile it. No second attestation request was made.

Mandatory statuses remain: Full Runtime Identity **NOT_VERIFIED**; ACTIVE_PROCESS_BUILD **NOT_DIRECTLY_VERIFIED**; live provider/model correlation **NOT_VERIFIED**; R2-A8 **BLOCKED / NOT_VERIFIED**; R2-A9 **HOLD**. No gate or authorization record was promoted.

**STOP after this implementation/test report. Human review is the next step; no Control Plane integration or runtime activation is authorized.**
