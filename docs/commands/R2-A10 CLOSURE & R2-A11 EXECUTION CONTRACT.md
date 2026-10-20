# NUSANTARA MASTER DEVELOPER ENGINE

# R2-A10 CLOSURE & R2-A11 EXECUTION CONTRACT

**Document ID:** `NUSANTARA-MDE-R2-A10-CLOSURE-R2-A11-20261008`
**Date:** 2026-10-08
**Repository:** `C:\Users\dmaza\mcp-starter`
**Branch:** `codex/fullroot-control-20261007`
**Baseline HEAD:** `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`
**Engineering Mode:** Evidence-First, Full-Root Inspection, Scoped Execution
**Governance Mode:** Human Decision Gate
**R2-A10 Status:** `PASS_SCOPED` — reported isolated import-isolation fix and regression verification
**R2-A11 Initial Status:** `PHASE_A_AUTHORIZED_READ_ONLY_DISCOVERY_ONLY`
**Human Decision:** `HOLD`
**Production Activation:** `NOT_AUTHORIZED`

---

# PART I — MASTER ENGINE DIRECTIVE

## 1. Purpose

This contract establishes the authoritative engineering handoff from R2-A10 to R2-A11.

The AI Developer Engine shall continue the existing Nusantara repository and architecture. It shall not rebuild Nusantara, repeat completed work, silently change prior decisions, or infer operational authorization from successful isolated tests.

The engineering objectives are:

1. Preserve the verified scope of R2-A10.
2. Preserve R2-A9 Control Plane acceptance and the human `HOLD` decision.
3. Establish the exact remaining evidence gaps for actual runtime identity and provider/model correlation.
4. Conduct read-only discovery before proposing implementation.
5. Require explicit human authorization for implementation and live-service actions.
6. Preserve existing application behavior and governance boundaries.
7. Produce reproducible evidence and a clear closure report for every phase.

**Primary principle:**

> Evidence before authorization. Verification before activation. Human decision before higher-risk execution.

## 2. Authority and Interpretation

This contract records the user's existing authorization for the completed R2-A10 scope. It does not extend that authorization to new implementation or live-service operations.

The AI Developer Engine must distinguish:

* Historical authorization.
* Current human decision.
* Source-derived evidence.
* Isolated test results.
* Current process observations.
* Live-service observations.
* Provider-confirmed invocation receipts.
* Operational authorization.

These are separate concepts and must not be conflated.

The report supplied for R2-A10 is the predecessor evidence. The engine must inspect the actual repository and available evidence before claiming independent verification.

## 3. Repository Identity

Expected repository:

`C:\Users\dmaza\mcp-starter`

Expected branch:

`codex/fullroot-control-20261007`

Reported baseline HEAD:

`8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`

Before continuing, the engine must independently inspect:

* Repository root.
* Current branch and HEAD.
* Working-tree status.
* Staged and unstaged changes.
* The R2-A10 contract.
* The R2-A10 implementation diff.
* The R2-A10 test evidence and reports.
* The existing R2-A11 contract, if already present.

If the actual repository differs from the expected baseline, report the discrepancy before proceeding. Never reset the repository to match this contract.

---

# PART II — R2-A10 FINAL CLOSURE RECORD

## 4. Final Outcome

**R2-A10: `PASS_SCOPED`**

Scope of the outcome:

Minimum import-isolation correction and isolated regression verification.

This status does not prove:

* A live service is running the expected code.
* The complete application build is verified.
* The actual provider/model identity is verified.
* A real provider invocation occurred.
* Production authorization is granted.
* ARM, EXECUTE, or IPC is active.

The result is scoped to the reported implementation and test evidence.

## 5. Original Failure

Original failing test:

`tests/test_runtime_attestation.py::test_new_processes_have_distinct_instances_and_actual_main_integration`

Original failure:

A strict isolation assertion detected forbidden application modules after importing `app.main`.

The forbidden module groups included:

* `app.knowledge`
* `app.models`
* `app.language`
* `app.approval`
* `app.api.routes`
* `app.api.v2_routes`

The assertion was retained unchanged.

## 6. Root Cause

The reported import chain was:

`app.main` under evidence-only configuration

→ `app.api.control_plane`

→ eager module-level import of `app.approval.runtime_authorization`

→ `app.approval` package initialization and authorization-related dependencies

This caused the shared Control Plane router to load modules that the evidence-only composition was expected to avoid.

## 7. Minimum Implementation Change

Reported changed source file:

`app/api/control_plane.py`

The `AuthorizationError` and `SCOPE` import was moved into the intention handler, after its ATTESTATION-only profile check.

Reported effect:

* Evidence-only boot no longer eagerly imports the private authorization foundation through the shared router.
* NORMAL composition no longer loads that foundation merely by importing the Control Plane router.
* ATTESTATION continues to install the authorization foundation through the existing authorized composition path.
* The existing intention validation and authority boundaries remain unchanged.
* No test assertion was weakened.
* No application test file was modified.

These statements are predecessor-report claims. The next engine must inspect the actual diff rather than reapply the same patch.

## 8. Interpreter and Test Results

Reported interpreter:

`C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe`

Reported Python version:

`3.13.15`

Reported virtual environment prefix:

`C:\Users\dmaza\mcp-starter\.venv`

### 8.1 Targeted and regression results

| Test file                                         | Reported passed |
| ------------------------------------------------- | --------------: |
| `tests/test_runtime_attestation.py`               |              16 |
| `tests/test_runtime_identity.py`                  |               2 |
| `tests/test_runtime_correlation.py`               |              16 |
| `tests/test_runtime_verification.py`              |              24 |
| `tests/test_control_plane_attestation_binding.py` |              31 |
| **Total**                                         |          **89** |

The four required runtime test files contributed 58 passes. The Control Plane regression contributed 31 passes.

Reported totals:

* Passed: 89
* Failed: 0
* Errors: 0
* Skipped: 0
* Warnings: 1 inherited Starlette/httpx deprecation warning

The warning was retained without installing or upgrading dependencies.

### 8.2 Reported execution commands

The predecessor report identifies the following commands as the test procedure:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'

& .venv/Scripts/python.exe -B -m pytest `
  tests/test_runtime_attestation.py::test_new_processes_have_distinct_instances_and_actual_main_integration `
  -p pytest_asyncio.plugin `
  -p no:cacheprovider `
  --basetemp=docs/reports/r2-a10-isolation-fix-20261008/baseline-tmp `
  --junitxml=docs/reports/r2-a10-isolation-fix-20261008/BASELINE.xml `
  -q

$env:R2_A7_TEST_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a10-isolation-fix-20261008\READ_ONLY_PROCESS_EVIDENCE.json'

& .venv/Scripts/python.exe -B `
  docs/reports/r2-a10-isolation-fix-20261008/isolated_test_runner.py
```

The report states that the report-owned runner executed the four required test files plus Control Plane regression.

The AI Developer Engine must not rerun these commands blindly. First inspect the runner, its guards, the generated reports, and the current working tree. Do not overwrite historical evidence.

## 9. Isolated NORMAL Test Limitations

The predecessor report describes a special isolated test setup for a NORMAL health-response test.

The setup substitutes the two eager API owner modules for that test and compiles the unchanged `HealthResponse` and decorated `health_check` AST from `app/api/routes.py`.

Its stated purpose is to exercise the actual `app.main` `/health` path against the unchanged `/v1/health` handler without initializing persistent knowledge/RAG state.

The report explicitly limits this evidence to isolated composition/handler verification. It is not a full production NORMAL startup verification or OS-level monitoring of all loaded libraries.

The next engine must preserve this distinction.

## 10. Source and Diff Evidence

The predecessor report states:

* 380 monitored source/test paths.
* One expected changed source file.
* 379 unchanged.
* `IMPLEMENTATION.diff` compares the pre-task `control_plane.py` snapshot.
* Git HEAD and branch remained unchanged.
* No staged paths were created.
* No dependency, configuration, RAG, database, WAL/SHM, or gate file was modified.
* No reset, clean, destructive revert, or unrelated overwrite occurred.

These claims must be retained as reported evidence until independently inspected.

Do not regenerate or overwrite the original evidence files merely to produce a new report.

## 11. Remaining R2-A10 Limitations

The following remain unverified:

* Full application build identity.
* Complete loaded-code coverage, including native libraries, globals, and closures.
* Direct proof that the active service process is serving the identified build.
* Live provider/model correlation.
* Actual Ollama/model invocation.
* Durable recovery guarantees for memory-only audit state.
* Live-service verification.

The existing deprecation warning remains unresolved because dependency changes were outside scope.

---

# PART III — GOVERNANCE AND CURRENT STATUS

## 12. Authoritative Gate Table

| Gate or capability                  | Status                   |
| ----------------------------------- | ------------------------ |
| R2-A9 Control Plane                 | `PASS_SCOPED`            |
| R2-A9 human decision                | `HOLD`                   |
| R2-A10 import isolation             | `PASS_SCOPED`            |
| R2-A8                               | `BLOCKED / NOT_VERIFIED` |
| Full Runtime Identity               | `NOT_VERIFIED`           |
| ACTIVE_PROCESS_BUILD                | `NOT_DIRECTLY_VERIFIED`  |
| Live provider/model correlation     | `NOT_VERIFIED`           |
| Full application build verification | `NOT_VERIFIED`           |
| ARM                                 | `LOCKED`                 |
| EXECUTE                             | `LOCKED`                 |
| IPC                                 | `NOT_ACTIVE`             |
| Production activation               | `NOT_AUTHORIZED`         |

The engine must not promote any status without new, appropriate evidence and the required human decision.

## 13. Human Decision Gate

The following phases apply:

### Phase A — Read-only discovery

Authorized under the R2-A11 handoff.

Permitted:

* Source inspection.
* Git inspection.
* Review of historical reports.
* Safe inspection of current process metadata.
* Review of existing runtime evidence.
* Read-only evidence collection where permitted.
* Existing tests that do not cross prohibited boundaries.
* Preparation of an evidence matrix and proposed implementation plan.

Not permitted:

* Source modification.
* Service restart or reload.
* Configuration changes.
* Real provider/model invocation.
* Authorization activation.

### Phase B — Minimum implementation

Requires a new explicit human decision after Phase A.

The engine must first identify the exact change, affected files, risks, test plan, and rollback boundary.

### Phase C — Live runtime verification

Requires a separate explicit human decision before actions with live operational effects, including real provider invocation, service restart, reload, or deployment interaction.

### Phase D — Authorization and activation

Outside this contract. Requires its own authorization process and contract.

---

# PART IV — R2-A11 LIVE RUNTIME EVIDENCE VERIFICATION

## 14. Mission

R2-A11 is the next proposed engineering phase.

Its purpose is to determine what can be proved about the actual running Nusantara service, while preserving the current human `HOLD` decision and all authorization boundaries.

R2-A11 must not be represented as completed until the required evidence has actually been collected and evaluated.

## 15. Required Evidence Domains

### 15.1 Actual process identity

Determine, where safely available:

* PID.
* Parent PID.
* Process start time.
* Executable path.
* Interpreter path.
* Working directory.
* Entrypoint.
* Runtime instance ID.
* Observation timestamp.
* Observation source and limitations.

A PID alone is insufficient because operating systems can reuse process identifiers.

Unavailable metadata must remain unavailable. It must never be fabricated from settings or expected values.

### 15.2 Active-process build identity

Distinguish clearly between:

* Source-build hash.
* Import-time source snapshot.
* Registered handler code hash.
* Loaded-code coverage.
* Full application build identity.
* Identity of the process actually serving a request.

A matching source snapshot is not sufficient proof of a complete application build.

`ACTIVE_PROCESS_BUILD` must remain `NOT_DIRECTLY_VERIFIED` unless a documented method directly establishes the relationship between the actual serving process and the identified build.

### 15.3 Provider/model correlation

Where an existing provider receipt boundary supports it, inspect the correlation of:

* Request ID.
* Invocation ID.
* Runtime instance ID.
* Process identity.
* Build identity.
* Provider ID.
* Configured model identifier.
* Actual provider-reported model identifier.
* Invocation timestamp.
* Response observation.
* Receipt outcome.

A configured model name is not proof of the actual model used.

Mock responses, synthetic receipts, historical fixtures, and isolated test PIDs cannot be represented as live provider evidence.

### 15.4 Freshness and stale-evidence rejection

Inspect the existing safeguards for:

* Expired evidence.
* Old process instances.
* PID mismatch.
* Runtime-instance mismatch.
* Build mismatch.
* Duplicate or conflicting receipts.
* Incomplete provider responses.
* Missing correlation identifiers.

Stale or ambiguous evidence must be rejected or downgraded to `NOT_VERIFIED`.

### 15.5 Control Plane governance

Preserve the existing flow:

`SYSTEM → EVIDENCE → TEST → REVIEW → DECISION`

Keep separate:

* Source-derived evidence.
* Isolated test evidence.
* Process observations.
* Live-service observations.
* Provider-confirmed receipts.
* Browser intentions.
* Human decisions.

A browser intention must not become an authorization grant or authenticated native peer.

---

# PART V — PROTECTED BOUNDARIES

## 16. Explicit Restrictions

Unless a later contract expressly authorizes a specific operation, the engine must not:

* Read, modify, repair, recreate, hash for verification, or delete protected knowledge-database files, including SQLite WAL/SHM sidecars.
* Change RAG, knowledge, embeddings, indexes, or protected-data migrations.
* Install, remove, or upgrade dependencies.
* Reset, clean, destructively revert, or overwrite unrelated repository work.
* Delete historical evidence or falsify reports.
* Fabricate runtime identity, timestamps, provider receipts, model identifiers, or PASS results.
* Promote R2 authorization or modify gate records.
* Provision policies or durable permits.
* Activate ARM, EXECUTE, IPC, or production deployment.
* Restart or reload the live service without explicit authorization.
* Invoke a real provider merely to manufacture a successful receipt.
* Weaken correct assertions to force a green test suite.
* Treat a successful isolated test as live runtime verification.

If a requested action crosses any of these boundaries, stop and request a separate human decision.

## 17. Existing Work Preservation

The repository may contain unrelated uncommitted changes and historical reports.

The engine must:

1. Record the initial Git status.
2. Avoid resetting or cleaning the repository.
3. Avoid staging or committing unless separately authorized.
4. Modify only files explicitly covered by the approved implementation phase.
5. Review the final diff.
6. Record unexpected modifications.
7. Preserve original evidence artifacts.

---

# PART VI — EVIDENCE CLASSIFICATION AND ACCEPTANCE

## 18. Evidence Classes

| Class                | Meaning                                                                |
| -------------------- | ---------------------------------------------------------------------- |
| `SOURCE`             | Source inspection or source-derived snapshot                           |
| `TEST_ISOLATED`      | Isolated test execution                                                |
| `PROCESS_OBSERVED`   | Direct operating-system process observation                            |
| `LIVE_SERVICE`       | Observation from the actual running service, correlated to the process |
| `PROVIDER_CONFIRMED` | Real provider receipt tied to the same invocation                      |
| `HUMAN_DECISION`     | Explicit decision through the authorized governance process            |

These classes are not interchangeable.

The engine must identify the evidence class supporting every material claim.

## 19. R2-A11 Acceptance Criteria

R2-A11 may be closed only at the scope supported by evidence.

Required criteria:

1. The actual service process is identified or explicitly remains unverified.
2. Process identity and runtime instance binding are documented.
3. Build evidence limitations are explicit.
4. Provider/model correlation is proven through appropriate real evidence or remains `NOT_VERIFIED`.
5. Stale and conflicting evidence cannot be silently reused.
6. R2-A9 human-decision semantics remain intact.
7. NORMAL behavior has appropriate regression evidence.
8. No prohibited boundary has been crossed.
9. The report distinguishes source, isolated tests, process observations, live service observations, provider receipts, and human decisions.
10. Remaining limitations are explicit.
11. The next human decision is requested before implementation or live operational actions.

Allowed closure statuses:

* `PASS_SCOPED`
* `PARTIAL`
* `NOT_VERIFIED`
* `BLOCKED`

A passing test suite alone cannot establish live runtime identity.

---

# PART VII — REQUIRED DELIVERABLES

## 20. Phase A Discovery Report

The engine must produce a report containing:

1. Repository root, branch, HEAD, and working-tree baseline.
2. R2-A10 contract and report references.
3. Independent review of the R2-A10 implementation diff.
4. Verification of the reported test evidence.
5. Current process observations, if safely obtainable.
6. Evidence classification matrix.
7. Exact gaps for Runtime Identity, ACTIVE_PROCESS_BUILD, provider/model correlation, and freshness.
8. Relevant existing source and tests.
9. Proposed minimum implementation, if necessary.
10. Exact candidate files to change.
11. Security and regression risks.
12. Test and rollback plan.
13. Explicit statement that no implementation or activation occurred.
14. A request for the next human decision.

Do not claim that a report, command, test, process observation, or live request was performed unless actual execution evidence exists.

## 21. Subsequent Phase Deliverables

After each separately authorized phase, provide:

* Exact actions performed.
* Exact commands and results.
* Changed files and concise diff summary.
* Test totals, failures, errors, skips, and warnings.
* Regression evidence.
* Protected-boundary confirmation.
* Remaining limitations.
* Updated gate table.
* Required next human decision.

The report must distinguish completed work from proposed work.

---

# PART VIII — EXECUTION INSTRUCTIONS TO THE AI DEVELOPER ENGINE

## 22. Mandatory First Actions

Upon receiving this contract:

1. Confirm the repository identity.
2. Inspect current Git status without modifying it.
3. Read the existing R2-A10 contract and reports.
4. Inspect the exact `app/api/control_plane.py` diff.
5. Inspect the report-owned isolated test runner and its evidence files.
6. Determine whether the reported R2-A10 evidence is present and internally consistent.
7. Inspect existing runtime-attestation and correlation implementations.
8. Produce the Phase A discovery report.

Do not repeat the R2-A10 fix if it is already present.

Do not rerun tests in a way that overwrites historical evidence or crosses the protected-data boundary.

If any necessary evidence is missing, report the limitation and stop at the discovery boundary.

## 23. Explicit Stop Conditions

Stop and request a human decision if:

* The repository identity or baseline differs unexpectedly.
* The existing implementation does not match the reported diff.
* The evidence is incomplete or contradictory.
* A test requires access to protected data.
* A live provider invocation is necessary.
* A service restart or reload is proposed.
* Any source change outside the authorized scope appears necessary.
* A proposed action could change authorization, ARM, EXECUTE, IPC, or production state.

Never resolve these conditions by guessing or silently expanding scope.

## 24. Final Directive

R2-A10 remains the predecessor closure record:

`PASS_SCOPED — import isolation and isolated regression verification`

R2-A11 begins with:

`PHASE A — AUTHORIZED READ-ONLY DISCOVERY ONLY`

Current human decision:

`HOLD`

Implementation authorization:

`NOT_GRANTED`

Live operational authorization:

`NOT_GRANTED`

Production activation:

`NOT_AUTHORIZED`

ARM:

`LOCKED`

EXECUTE:

`LOCKED`

IPC:

`NOT_ACTIVE`

**The AI Developer Engine must stop after presenting evidence-based Phase A findings. No source changes or live operational actions may follow without the next explicit human decision.**

**END OF CONTRACT**
