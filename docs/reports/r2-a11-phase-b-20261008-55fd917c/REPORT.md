# R2-A11 Phase B — isolated implementation and regression

**PASS_SCOPED: internal receipt assessment and bounded safe regression only. STOP.** Full live correlation and full regression are not claimed.

## Baseline and authorization

Human authorized minimum isolated implementation/testing, with no provider invocation/generation, permit, ARM/EXECUTE, IPC, policy provisioning, live HTTP, service action or gate promotion. Governing R2-A11 contract, Phase A report and Phase C0 report were inspected before edits. PLAN.md records the intended changes and exclusions before application modification.

Root C:/Users/dmaza/mcp-starter; branch codex/fullroot-control-20261007; HEAD 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab independently confirmed. Interpreter .venv/Scripts/python.exe, Python 3.13.15, venv prefix matching repository. Initial tracked dirty state contained the same 26 inherited tracked modifications as prior phases; staging empty. Exact copies of the four candidate files and hashes of 380 monitored source/test/script/service paths were saved before editing. No assumption of a clean worktree, reset, cleanup, staging or commit.

## Proven gap and minimum correction

Source showed CorrelationReceipt lacked a private process-start observation/freshness boundary and VerificationController exposed stored receipts without a separate current-context assessment. One-use permit expiry governs dispatch, not the later age of a stored receipt. A matching PID/instance/code alone cannot exclude PID reuse or stale/replaced evidence. Public projections already state NOT_VERIFIED; the issue was missing assessment capability, not a claim that those projections previously promoted a gate.

Before changing application source, added 29 pure assessment tests and ran them under guards. red.xml records **29 failures, zero errors/skips, 16 deselected**: ReceiptObservation/assessment API did not exist. This is a reproducible missing validation contract, not a live failure or reproduction of the source-snapshot mismatch. New implementation closes that isolated gap.

Only four files changed:

| File | Minimum purpose |
|---|---|
| app/core/runtime_correlation.py | Frozen private ReceiptObservation holding the original immutable receipt, process start, server observed/expiry timestamps and provenance; pure fail-closed assess_receipt and timezone-aware timestamp parser |
| app/api/runtime_verification.py | Store internal observation separately from public receipt, reject conflicting replacement, classify isolated transports separately, assess current OS/instance/source/scoped-code binding, include assessment helpers in scoped code coverage |
| tests/test_runtime_correlation.py | 29 synthetic pure validation cases, no dispatch/permit/provider |
| tests/test_runtime_verification.py | Four no-dispatch controller/storage/context/send tests |

Assessment checks PID and process-start (including same PID with changed start), runtime instance, source/scoped code, provider/endpoint, immutable original receipt consistency, invocation/request/model completeness, one actual-dispatch count, bounded timezone-aware chronology and expiry. Invalid ages, future observations, expired/overlong windows, missing context, fixture/unknown provenance and unavailable current observers fail closed with bounded non-sensitive reason codes.

Successful assessment returns correlation_valid=true only for matching trusted server context. **Its status remains NOT_VERIFIED in every result.** It does not authenticate arbitrary externally supplied objects, independently prove model weights, authorize action or promote Runtime Identity. Provenance is attached by the private controller's transport path; a pure function cannot authenticate a fixture that malicious in-process code relabels as genuine. Synthetic PROVIDER_RESPONSE-labelled tests exercise the trusted-context branch only and are not provider evidence.

The original public CorrelationReceipt schema is unchanged, preserving strict Control Plane parsing. Observation stays internal, not a new HTTP endpoint, token, audit owner, queue, authorization or client evidence object. receipt_assessment() is an internal assessment seam; no live/UI activation or new projection integration was performed. Existing raw receipt projections still expose observations under NOT_VERIFIED; do not assume they now automatically incorporate the new assessment.

ASGI send remains separate from provider evidence: only a successful final send changes application_response_sent; failed send does not, external_client_observed stays false, and sending a fixture receipt never makes its assessment genuine. Existing send/middleware/authority semantics are preserved.

## New verification results

Final isolated run: **67 passed, zero failures/errors/skips, 55 deselected, one inherited Starlette/httpx deprecation warning.**

| File | Final passed |
|---|---:|
| test_runtime_correlation.py | 41 (29 new + 12 safe existing) |
| test_runtime_verification.py | 7 (4 new + 3 safe existing) |
| test_runtime_attestation.py | 16 existing |
| test_runtime_identity.py | 2 existing |
| test_control_plane_attestation_binding.py | 1 existing guarded composition |
| Total | 67 (33 new + 34 safe regressions) |

red.xml retains the missing-API baseline. regression.xml retains the first corrected run of 66 passes; final.xml records 67 after adding fail-closed observer-error coverage. No historical artifacts or prior attempt results were overwritten. The new XML totals are independently parsed in TEST_RESULTS.json.

The 55 deselected existing tests were deliberately not run: positive permit/dispatch/provider cases and policy-bearing Control Plane fixtures conflict with this phase's stricter prohibitions. Their assertions remain unchanged. Historical R2-A10 89-pass evidence remains historical and cannot replace rerun coverage of altered invocation paths. No claim of the full 89-test regression suite or positive provider-path regression is made.

Existing safe Control Plane guarded composition uses in-process ASGI and no operator policy/permit: PENDING intention remains untrusted, owner policy None, live_actions LOCKED, dispatch zero. Existing NORMAL composition and health AST setup avoid eager persistent owners. This supports bounded composition/handler regression, not complete production NORMAL startup. No frontend file or public chat/dev route changed.

Report-owned runner adapted from the existing guarded pytest runner. Guards block sqlite3.connect, protected file reads, real HTTP transports, knowledge/RAG imports, OneUseAuthorization.grant, provider generate/generate_structured/health/list-models and LocalOperatorChannel entry. Guarded subprocess composition has its existing additional socket/protected-state protections. No service HTTP, provider/model function invocation, grant, IPC or policy provisioning was performed by the selected cases. Synthetic receipt objects and failed/successful ASGI send callbacks test logic only.

Commands from repository root:

```powershell
& .venv/Scripts/python.exe -B docs/reports/r2-a11-phase-b-20261008-55fd917c/isolated_test_runner.py red
$env:R2_A7_TEST_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a11-phase-b-20261008-55fd917c\ISOLATED_ATTESTATION.json'
$env:R2_CPLANE_ISOLATED_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a11-phase-b-20261008-55fd917c\ISOLATED_CONTROL_PLANE.json'
& .venv/Scripts/python.exe -B docs/reports/r2-a11-phase-b-20261008-55fd917c/isolated_test_runner.py regression
$env:R2_A7_TEST_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a11-phase-b-20261008-55fd917c\ISOLATED_ATTESTATION_FINAL.json'
$env:R2_CPLANE_ISOLATED_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a11-phase-b-20261008-55fd917c\ISOLATED_CONTROL_PLANE_FINAL.json'
& .venv/Scripts/python.exe -B docs/reports/r2-a11-phase-b-20261008-55fd917c/isolated_test_runner.py final
```

Runner sets PYTHONDONTWRITEBYTECODE=1, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, uses existing pytest/pytest_asyncio, no cache provider, report-owned per-attempt basetemp/XML, inspected -k selection and existing isolated NORMAL health AST plugin. Full argument list and safety guards are in isolated_test_runner.py. No dependency installation or warning suppression.

## State/diff review and limitations

SOURCE_COMPARISON.json verifies 380 monitored paths: the four expected files changed, **376 unchanged**. IMPLEMENTATION.diff compares exact saved pre-phase contents, so inherited modifications are not erased or confused with this patch. Git root/HEAD/branch unchanged and staged paths empty (GIT_FINAL.json). Protected files were not read/hashed for verification; the source manifest is not OS-wide side-effect monitoring.

Security review: observation and receipt objects frozen; original receipt held privately for conflict checks; fresh context queried at assessment time; unknown/fixture provenance rejected; parse/observer failures redacted and fail closed. No browser/actor/model assertion becomes authority. No new audit or authorization subsystem. Source/helper coverage is scoped and still excludes native/globals/closure dependencies. Expiry is bounded server wall-clock evidence; no durable/tamper-resistant clock or independent remote attestation claim. Arbitrary in-process code can modify private state; this mechanism is not a defense against a compromised interpreter. Process-start unavailable means NOT_VERIFIED.

No activation/loading was performed. The new internal invocation/storage/provenance path was inspected and covered by direct no-dispatch tests, but its positive generation integration was not executed because the human decision forbids it. Future isolated mock invocation regression needs a decision expressly permitting that operation. No automatic bypass, retry, arming or substitute model is proposed.

Existing graph queried before implementation and AST-only update launched after code changes per AGENTS.md. Graph artifacts are derived documentation, not application configuration; inaccessible historical directories remain a graph coverage limitation. No external provider/API or LLM extraction authorized or used.

Phase C0 mismatch remains untouched:

Process SOURCE_SNAPSHOT: sha256:9789c2760ba7e78a4e6c5f6c7b1a5dec775c76f362cb40bb09d39e7d377a44df.

C0 disk snapshot: sha256:fdc9a1e219ce55ab5957a58a31aef67a7a9a12277dabb03a1bad9b62871821ad.

These are historical C0 observations, not newly captured current hashes. Source edits cannot resolve a running-process mismatch. C0 response checksum preserved in HISTORICAL_REFERENCES.json. No second attestation request or current service/process probe occurred in Phase B.

## Human decision and stop

Full Runtime Identity remains NOT_VERIFIED. ACTIVE_PROCESS_BUILD remains NOT_DIRECTLY_VERIFIED. Live provider/model correlation remains NOT_VERIFIED. R2-A8 remains BLOCKED / NOT_VERIFIED. R2-A9 HOLD and all policy/gate records unchanged.

No service/config/database/WAL/SHM/RAG/provider selection/authorization record modified; no restart/reload/deployment, HTTP to live service, generation, grant, ARM, EXECUTE, IPC, policy provisioning, Git reset/clean/staging/commit. Evidence was written only to the new directory; derived AST graph artifacts updated as repository instructions require.

Rollback plan for a separately authorized correction: restore only approved changed hunks against saved pre-phase copies, preserving inherited work; never reset the whole repository, alter protected data or load a service automatically. This phase performs no rollback or service action.

Recommended next decision: HOLD pending review of this diff and the explicit regression exclusions; optionally authorize isolated mock-only positive receipt/invocation-path regression under a separate contract. Any live loading/attestation/provider observation requires its own later decision and safety preflight. **STOP. No next phase begins automatically.**
