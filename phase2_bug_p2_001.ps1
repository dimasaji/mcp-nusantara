$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA AI - PHASE 2 BUG-P2-001" -ForegroundColor Cyan
Write-Host " Claude Code Engineering Task" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$Prompt = @'
NUSANTARA AI — PHASE 2 CORE HARDENING
TASK: FIX BUG-P2-001 + REGRESSION TEST

ROLE:
Act as Principal Software Engineer / AI Systems Engineer.
Follow:
INSPECT → UNDERSTAND → MAP → RISK → PROPOSE → IMPLEMENT → TEST → SECURITY → REGRESSION → REPORT.

IMPORTANT:
Do not rewrite the project.
Do not create a second engine.
Do not change the V1 core architecture.

CURRENT ENVIRONMENT:

* FastAPI: available
* httpx: available
* pytest: available

ACTUAL HARDENING MODULES:

* app/core/hardening/validator.py
* app/core/hardening/timeout.py
* app/core/hardening/retry.py
* app/core/hardening/circuit_breaker.py
* app/core/hardening/safe_execution.py
* app/core/hardening/**init**.py

CURRENT FINDING:
BUG-P2-001 exists in safe_execution.py.

Current safe_acall() executes:

```
res = fn(*args, **kwargs)
```

This means a synchronous blocking function can block the asyncio event loop.

Example:

```
await safe_acall(time.sleep, 0.3, timeout_s=0.05)
```

The timeout must actually apply to synchronous functions too.

OBJECTIVE:
Fix ONLY BUG-P2-001.

Expected behavior:

1. Sync blocking function + timeout must return OperationTimeout.
2. Sync blocking function must not block the asyncio event loop.
3. contextvars must propagate to the worker thread.
4. Sync function returning an awaitable must still work correctly.
5. Async function + timeout must continue working.
6. timeout_s=None must preserve existing behavior.
7. SafeResult contract must remain unchanged.
8. CircuitBreaker integration must remain unchanged.
9. Error text must remain truncated to 500 characters.
10. Do not leak traceback/internal implementation details through SafeResult.

IMPLEMENTATION DIRECTION:
For synchronous function + timeout:

* use asyncio.to_thread()
* apply await_with_timeout()
* preserve contextvars
* do not break existing async behavior
* do not introduce unnecessary dependencies

IMPORTANT:
Before editing ANY file:

1. Inspect:

   * app/core/hardening/safe_execution.py
   * app/core/hardening/timeout.py
   * app/core/hardening/circuit_breaker.py
   * app/core/hardening/validator.py
   * app/core/hardening/**init**.py
   * existing tests
   * pyproject.toml test configuration

2. Determine the actual public contract.

3. Explain briefly:

   * root cause
   * affected behavior
   * minimal fix
   * files that will be changed

Do not edit until inspection is complete.

ALLOWED CHANGES:

* app/core/hardening/safe_execution.py
* a dedicated Phase 2 regression test file if one does not already exist

DO NOT CHANGE:

* app/api/routes.py
* app/api/v2_routes.py
* app/hermes/
* app/memory/
* app/rag/
* app/knowledge/
* app/mcp/
* app/security/
* app/policy/
* app/trust/
* app/tools/
* app/skills/
* Graphify
* database/schema
* pyproject.toml
* dependency installation
* unrelated production code

TEST REQUIREMENTS:
Create or update only the appropriate Phase 2 hardening regression test.

Minimum scenarios:

1. invalid input
2. sync timeout
3. async timeout
4. sync timeout through safe_acall
5. event loop remains responsive
6. contextvars propagation
7. sync function returning awaitable
8. retry success after transient failures
9. retry exhaustion
10. circuit opens after threshold
11. circuit half-open recovery
12. safe failure does not raise ordinary Exception
13. error is limited to 500 chars
14. no-timeout safe_acall path remains compatible

Do not weaken assertions merely to make tests pass.

Run:

```
pytest <relevant Phase 2 test file> -q
```

If another existing test is directly affected, run that test as regression verification.

DO NOT:

* install packages
* change dependency versions
* modify source unrelated to BUG-P2-001
* modify API contract
* modify database
* connect Graphify
* start Phase 3
* create dashboard
* implement /v1/chat changes

TIMEOUT TECHNICAL NOTE:
A Python worker thread that exceeds timeout cannot be forcibly killed.
The caller must return after timeout while the worker may continue in the background.
Do not incorrectly claim the underlying thread was terminated.

SECURITY CHECK:
Verify:

* no secret added
* no traceback exposed through SafeResult
* error remains <= 500 chars
* no arbitrary shell execution introduced
* no new network dependency

REGRESSION:
Verify existing behavior of:

* safe_call
* safe_acall
* retry
* aretry
* CircuitBreaker
* validator

FINAL REPORT FORMAT:

============================================================
PHASE 2 BUG-P2-001 REPORT
=========================

ROOT CAUSE:
...

FILES INSPECTED:
...

FILES CHANGED:
...

IMPLEMENTATION:
...

TESTS EXECUTED:
...

PASSED:
...

FAILED:
...

SECURITY:
...

REGRESSION:
...

REMAINING RISKS:
...

FINAL STATUS:
VERIFIED / PARTIALLY VERIFIED / UNVERIFIED

IMPORTANT:
Do not claim VERIFIED unless the relevant tests actually execute and pass.

STOP after the report.
'@

Write-Host "Starting Claude Code..." -ForegroundColor Green
Write-Host ""

claude $Prompt

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Claude Code task finished." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "STOP - Do not start Phase 3 yet." -ForegroundColor Yellow
