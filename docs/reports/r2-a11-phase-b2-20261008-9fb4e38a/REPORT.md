# R2-A11 Phase B2 — isolated integration validation

**BLOCKED. 17 passed / 2 failed. An essential fail-closed implementation gap was reproduced. Application source was not changed. STOP for a separate human decision.**

## Baseline and inspected evidence

Root C:/Users/dmaza/mcp-starter, branch codex/fullroot-control-20261007, HEAD 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab match the expected repository. Staged paths empty before and after. The inherited 26 tracked modifications remain unchanged; do not interpret the worktree as clean. GIT_BEFORE/AFTER/COMPARISON.json record pre-test/final state. Five inherited inaccessible report directories limit untracked inventory; no permission repair was attempted.

Read Phase B REPORT.md, guarded runner, implementation diff, current ReceiptObservation/assess_receipt, VerificationController and its creation/storage/assessment path before acting. Existing graph queried read-only for ReceiptObservation/receipt_assessment/VerificationController; direct source supplied detailed evidence. Historical reports and tests were not overwritten. Source hashes recorded before tests and independently after: **380 paths unchanged**. No application or existing repository test file changed.

## Test boundary and actual exercised path

New report-owned test_b2_integration.py constructs only isolated controllers and immutable synthetic receipts. MockTransport has a responder which raises if called; it is never dispatched. A synthetic dispatch_count=1 is an input to receipt construction, not an authorization counter or generation result. Each fixture verifies the real controller remains DISARMED with dispatch_count=0 and zero transport calls.

The integration test executes exactly three unchanged AST statements extracted from VerificationController.invoke: transport provenance classification, CorrelationReceipt construction, and self._store. The full invoke method, authorization reserve/dispatch, client creation, provider construction/generation and all awaits are excluded. The AST shape is asserted, not replaced with a fabricated implementation. The mock route produces TEST_ISOLATED provenance, stored observation references the constructed receipt, and assessment rejects it as genuine evidence.

The synthetic trusted-context branch explicitly calls private _store with PROVIDER_RESPONSE provenance to test internal assessment semantics only. It is not a real provider receipt. Successful synthetic assessment still reports status NOT_VERIFIED and external_client_observed=false. Tests cover missing/unknown/fixture provenance, replacement conflict, PID/start/instance/source/scoped changes, timestamp failure redaction, missing process metadata and raising observer behavior. No fixture is promoted to live evidence.

## Exact command and results

From repository root, using the existing Python 3.13.15 venv/pytest infrastructure:

```powershell
& .venv/Scripts/python.exe -B docs/reports/r2-a11-phase-b2-20261008-9fb4e38a/isolated_test_runner.py
```

Runner executes report-owned test_b2_integration.py with existing pytest_asyncio, no cache provider, dedicated focused-tmp and FOCUSED.xml. PYTHONDONTWRITEBYTECODE=1 and plugin autoload disabled. Selected IDs are listed verbatim in SELECTED_TEST_IDS.json and TEST_RESULTS.json (19 parameter-expanded cases).

**Selected 19: passed 17, failed 2, errors 0, skipped 0, deselected 0, test warnings 0.** No assertion was removed or weakened. No retry/rerun followed the essential gap. A safe regression run was **NOT RUN** because Change Control section 4 requires recording the evidence and stopping before implementation; this is not a regression PASS claim. Phase B's 67 results and older R2-A10 results remain historical.

Failed IDs:

```text
test_b2_integration.py::test_incomplete_process_observer_fails_closed[result0]
test_b2_integration.py::test_incomplete_process_observer_fails_closed[None]
```

All other selected IDs are in the JSON list, including actual AST construction/classification/storage, synthetic trusted-context, four provenance variants, replacement conflict, five context changes, three timestamp variants, process_start_time=None and raising observer cases.

## Essential gap — no source fix authorized here

app/api/runtime_verification.py receipt_assessment() catches exceptions while calling _process_identity/current_runtime_instance/code observer. It subsequently evaluates process['process_start_time'] outside that try block.

When the process observer returns {}, a KeyError('process_start_time') escapes. When it returns None, TypeError("'NoneType' object is not subscriptable") escapes. The expected bounded NOT_VERIFIED assessment is not returned. An observer that raises directly is handled correctly, and {'process_start_time': None} yields a rejected assessment; returned malformed objects reveal the gap.

This is an isolated malformed-observer robustness failure, not evidence that the current production OS helper normally returns these shapes. It does not prove live provider failure, gate activation or protected-state access. FOCUSED.xml contains exact failures and source location (receipt_assessment argument evaluation, current line 97).

Minimum proposed correction for a new human decision: validate observer result/required fields and evaluate current binding arguments inside the fail-closed context boundary in app/api/runtime_verification.py. Retain these failing tests unchanged and add malformed runtime-instance coverage when authorized. This report does **not** implement that correction, widen scope, suppress failures or provision authority.

## Guard and diff review

Guards inherited/adapted from Phase B block database connections/protected file opens, knowledge/RAG imports, real HTTP transports, grants, reserve/dispatch, provider generate/structured/health/list-model operations and native channel entry. Selected cases invoke none of these operations. No guard violation was observed; test responder calls stayed zero and real authorization counters stayed zero. The two failures are malformed observer exceptions, not prohibited operation attempts. No standalone active-service or process probe was performed. Guards are Python-level, not exhaustive OS monitoring.

Final diff: **zero application source changes, zero existing repository test changes**. New files are report-owned test_b2_integration.py, isolated_test_runner.py, SOURCE_BEFORE/AFTER/STABILITY.json, GIT_BEFORE/AFTER/COMPARISON.json, SELECTED_TEST_IDS.json, TEST_RESULTS.json, FOCUSED.xml and this REPORT.md, plus pytest temporary directory artifacts. FILES_CREATED.json inventories delivered report artifacts. No graph rebuild or derived artifacts outside this directory were created in B2; existing graph was only queried. Application source need not be rolled back because none changed.

No public endpoint/UI/schema/configuration/policy/gate/authorization record change; no protected database/WAL/SHM/knowledge read/hash, RAG, provider/model invocation, generation, permit/grant, ARM/EXECUTE, IPC, reload/restart/deploy/dependency operation or Git reset/clean/checkout/staging/commit. Existing imported code remains inherited Phase B implementation; test AST execution is an isolated seam, not service loading.

## Remaining limitations and mandatory state

No end-to-end invoke/generation or real transport path ran. AST seam tests three actual statements while replacing surrounding context, so it cannot establish the behavior of the omitted authorization/provider invocation lifecycle. No full NORMAL/Control Plane regression was rerun after the block. A copied fixture can be relabelled by arbitrary in-process code; private provenance is not cryptographic authentication. Clock, full-build/native coverage and independent client delivery limitations remain.

Phase C0's historical process/disk source mismatch remains untouched and unresolved; no second attestation request was made. Full Runtime Identity **NOT_VERIFIED**; ACTIVE_PROCESS_BUILD **NOT_DIRECTLY_VERIFIED**; live provider/model correlation **NOT_VERIFIED**; R2-A8 **BLOCKED / NOT_VERIFIED**; R2-A9 **HOLD**. No gate or authorization promotion.

**STOP. A separate human decision is required before the proposed minimal fail-closed source correction or any further phase.**
