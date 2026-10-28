# R2-A10 — Runtime attestation isolation fix

Date: 2026-10-08. **Outcome: PASS_SCOPED — minimum import-isolation fix and isolated regression verification.** This outcome does not verify a live service, full application build or actual provider/model invocation, and does not change authorization state.

Repository: C:\Users\dmaza\mcp-starter. HEAD: 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab. Branch: codex/fullroot-control-20261007. Exact contract: .dev/R2_A10_AUTHORIZATION_CONTRACT_20261008_134113.md, SHA-256 98a1b740aeda3db528d4f7ad24157a6b707b790606489b06ef2dcca0c349d994. The explicit user directive AUTHORIZE R2-A10 IMPLEMENTATION supplies the human decision required by that contract; the contract's historical NOT_GRANTED text was not edited.

## Diagnosis and minimum change

The original failing test was reproduced: BASELINE.xml records one failure in test_new_processes_have_distinct_instances_and_actual_main_integration. Its strict forbidden-module assertion was correct and remains unchanged.

Actual source import path:

```text
app.main (NUSANTARA_CONTROL_PLANE_READ_ONLY=1)
  -> app.api.control_plane (unconditional router import)
     -> app.approval.runtime_authorization (new eager module-level import)
        -> app.approval.__init__
           -> AuditTrail / ApprovalQueue modules
        -> native operator module and authorization foundation dependencies
```

Even though evidence-only boot avoided production routes and ATTESTATION owner installation, importing the shared Control Plane router loaded approval modules. The R2-A9 adapter had introduced this regression.

**Only app/api/control_plane.py changed:** move AuthorizationError/SCOPE import into the intention handler, after its ATTESTATION-only profile check. Evidence-only and NORMAL composition no longer eagerly import the private foundation through the shared router. ATTESTATION still installs its private foundation through the already-authorized app.main branch. Snapshot behavior, intention validation/result, native authority, audit ownership and permit/transport semantics are unchanged. No failing assertion or production composition policy was weakened.

## Interpreter and tests

Interpreter confirmed before tests: C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe, Python 3.13.15, venv prefix C:\Users\dmaza\mcp-starter\.venv.

**89 PASS, zero failures/errors/skips, one inherited Starlette/httpx deprecation warning.**

| Test file | Passed |
|---|---:|
| tests/test_runtime_attestation.py | 16 |
| tests/test_runtime_identity.py | 2 |
| tests/test_runtime_correlation.py | 16 |
| tests/test_runtime_verification.py | 24 |
| tests/test_control_plane_attestation_binding.py | 31 |
| Required four-file subtotal | 58 |
| All targeted + relevant regression | 89 |

Exact commands from repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
& .venv/Scripts/python.exe -B -m pytest tests/test_runtime_attestation.py::test_new_processes_have_distinct_instances_and_actual_main_integration -p pytest_asyncio.plugin -p no:cacheprovider --basetemp=docs/reports/r2-a10-isolation-fix-20261008/baseline-tmp --junitxml=docs/reports/r2-a10-isolation-fix-20261008/BASELINE.xml -q
$env:R2_A7_TEST_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a10-isolation-fix-20261008\READ_ONLY_PROCESS_EVIDENCE.json'
& .venv/Scripts/python.exe -B docs/reports/r2-a10-isolation-fix-20261008/isolated_test_runner.py
```

The report-owned runner executes all four required files plus Control Plane regression with pytest_asyncio, no cache provider, report-owned basetemp and TARGETED_AND_REGRESSION.xml. Its full argument list and guards are reviewable in isolated_test_runner.py. No application test file was edited, skipped, xfailed or filtered out.

## Necessary isolated NORMAL test setup

The existing test_health_reports_same_loaded_build imports NORMAL app.main, whose production API owners initialize KnowledgeEngine and persistent state. Running it directly against the repository would violate this directive's DB/RAG boundary.

The report-owned pytest setup substitutes only the two eager API owner modules for that one test, following the pre-existing isolated NORMAL composition test's architecture. It compiles the actual unchanged HealthResponse and decorated health_check AST from app/api/routes.py, preserving their source, defaults, response model and BUILD_ID binding. It tests the real app.main /health against that unchanged /v1/health handler; no fabricated health result replaces the assertion. The NORMAL configuration fixture is memory-only and production settings/source remain unchanged.

SQLite/protected-file reads and real HTTP transports are blocked in the runner; knowledge/RAG/language imports are rejected. Existing subprocess tests use their own protected-state guards or synthetic NORMAL API owners. This is isolated composition/handler evidence, not a full production NORMAL startup verification or OS-level monitoring of every library.

## Evidence meaning and preserved boundaries

The formerly failing test now passes unchanged across two isolated evidence-only app processes: distinct PID/runtime instance, stable registered scoped code hash, process/cwd binding, and NOT_VERIFIED runtime status. READ_ONLY_PROCESS_EVIDENCE.json explicitly labels those processes isolated and existing_live_service_verified=false.

Runtime tests retain scoped build limitations, unavailable OS metadata behavior, loaded-code drift rejection, freshness/expiry and stale instance rejection. Existing provider-correlation tests exercise genuine provider code only behind mocked transports/synthetic responses; fixture model receipts are not actual Ollama/model proof. No real provider/model invocation or generation was performed. No live permit/grant, ARM/EXECUTE, IPC, HTTP verification, policy provisioning, restart/loading/deployment or authorization promotion occurred. Existing positive permit/dispatch states were exercised only inside the expressly required isolated unit tests, never against a service.

Control Plane regression verifies PENDING-only intention, stale/forged context rejection, duplicate/concurrent bounds, actor and ARM/EXECUTE rejection, absent policy/permit, guarded ATTESTATION app composition and unchanged NORMAL mutation denial. Frontend source is unchanged; its previously accepted isolated UI result is not reclassified as live success.

## Diff and source review

SOURCE_COMPARISON.json: 380 monitored source/test paths, **one expected changed source file**, 379 unchanged. IMPLEMENTATION.diff compares the exact pre-task control_plane.py snapshot. app.main, authorization foundation, native IPC, runtime identity/attestation/correlation/verification, provider code, public chat/dev paths, NORMAL projection and tests are unchanged. No configuration/dependency/RAG/database/WAL/SHM/gate file was modified or hashed for protected-state verification.

Git HEAD/branch unchanged; staged paths empty. No reset, clean, overwrite/revert of unrelated work, staging or commit. Reports, test temporary artifacts and AST-only graph outputs are derived evidence. Graph scan retains inherited inaccessible-report-directory warnings; no permission repair or LLM/API labeling was performed.

## Remaining limitations and final state

This fix establishes scoped import isolation, not deployment/loading. Current user-supplied localhost evidence and HOLD decision were not re-probed or altered. Full application build and native library/global/closure coverage remain unproven. Provider/model live correlation remains unavailable, and mock test PIDs/models cannot replace live receipts. Memory-only audit has no durable recovery guarantee. The inherited dependency deprecation warning remains without installation/upgrade.

R2-A8 remains **BLOCKED / NOT_VERIFIED**. Full Runtime Identity remains **NOT_VERIFIED**. ACTIVE_PROCESS_BUILD remains **NOT_DIRECTLY_VERIFIED**. R2-A9's accepted scoped status and human HOLD remain unchanged; no policy/authorization record was promoted.

**STOP. Evidence before authorization; verification before activation; human decision before any higher-risk action.**
