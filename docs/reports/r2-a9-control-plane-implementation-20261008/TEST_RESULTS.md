# Exact isolated validation

Final: **31 backend tests PASS + 52 frontend tests PASS = 83 PASS**, zero test failures/errors/skips. TypeScript static check exit 0. No live generation or application HTTP request; guarded composition dispatch_count=0.

## Backend command (repository root)

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:R2_CPLANE_ISOLATED_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a9-control-plane-implementation-20261008/COMPOSITION_EVIDENCE.json'
& .venv/Scripts/python.exe -B docs/reports/r2-a9-control-plane-implementation-20261008/make_synthetic_fixture.py
& .venv/Scripts/python.exe -B -m pytest tests/test_control_plane_attestation_binding.py -p pytest_asyncio.plugin -p no:cacheprovider --basetemp=docs/reports/r2-a9-control-plane-implementation-20261008/isolated-pass-tmp --junitxml=docs/reports/r2-a9-control-plane-implementation-20261008/BACKEND_PASS.xml -q
```

31 PASS. PENDING-only creation, deduplication/concurrency, stale binding before mutation (including between validation/creation), actor/operation overrides, Origin/Host/peer/body bounds, absent owner, NORMAL mutation denial, capacity/expiry, detached state, queue failure, live-lock rejection and guarded actual ATTESTATION composition.

## Frontend command (control-plane directory)

```powershell
$env:CPLANE_SNAPSHOT_FILE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a9-control-plane-implementation-20261008\SYNTHETIC_NORMAL.json'
$env:R2_CPLANE_ISOLATED_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a9-control-plane-implementation-20261008\COMPOSITION_EVIDENCE.json'
& 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' node_modules/vitest/vitest.mjs run --config vitest.config.ts --reporter=default --reporter=junit --outputFile.junit=../docs/reports/r2-a9-control-plane-implementation-20261008/FRONTEND_COMPLETE.xml
& 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' node_modules/typescript/bin/tsc --noEmit
```

52 PASS across 5 files: existing API 3, acceptance 11, UI 4, human workflow 19; new ATTESTATION integration 15. Actual guarded backend snapshot accepted by parser, separate NORMAL synthetic schema, mixed/unknown contract rejection, five invented status rejection cases, explicit bounded payload and rejection/no retry, context invalidation, identity presentation, five-stage intention flow, existing router/query/navigation in jsdom and locked-stage enforcement. Existing NORMAL tests use synthetic fixture data rather than protected projection setup.

## Contract matrix

| Requirement | Evidence |
|---|---|
| T1 ATTESTATION schema | Separate parser plus actual guarded backend snapshot test |
| T2 NORMAL schema | Existing 37 frontend tests with synthetic NORMAL fixture; old schema definition unchanged |
| T3 No masquerading | Cross-parser and mixed/unknown discriminator rejection |
| T4 Evidence presentation | Scoped identity component + router/engineering/human views |
| T5 NOT_VERIFIED | Visible status and rejection of invented promotion |
| T6 Human separation | Browser observations stay session state; no APPROVE control in ATTESTATION |
| T7 Intention | Explicit click; strict response and backend PENDING-only result |
| T8 Stale evidence | Atomic reject with empty queue/audit; second material capture tested |
| T9 Actor assertion | Extra actor/reviewer/PID/token fields rejected; no VerifiedPeer construction |
| T10 ARM rejection | No route; invalid actor rejected; post-peer unit seam still live-locked |
| T11 EXECUTE rejection | Same independent EXECUTE cases, zero dispatch |
| T12 Live transport | Real app guarded imports/transport/provider/IPC activation, policy=None, permit=None |

## Retained earlier attempts and warnings

BACKEND_FIRST.xml: 26 PASS / 1 FAIL because an overly broad socket guard blocked Windows asyncio's internal stdlib socketpair. Corrected to allow only that exact stdlib function while rejecting application connects. BACKEND_SECOND.xml: 27 PASS. BACKEND_FINAL.xml and BACKEND_PASS.xml: 31 PASS after added atomic/capacity/live-lock checks and composition export.

FRONTEND_FIRST.xml: 48 PASS / 2 FAIL from synthetic fixture causing duplicate text matches in unchanged NORMAL assertions. FRONTEND_FINAL.xml: 49 PASS / 1 FAIL; remaining synthetic absent runtime fields also rendered repeated NOT_VERIFIED. Fixture data was corrected without changing those tests or NORMAL production behavior. FRONTEND_PASS.xml: 51 PASS. FRONTEND_COMPLETE.xml: 52 PASS after adding the existing-router integration test.

Inherited Starlette/httpx deprecation warning remains; no dependency was installed. The jsdom router test emits window.scrollTo-not-implemented diagnostics; navigation assertions pass, but real browser scrolling is not tested. No Vite build/dev/preview, Playwright server or live HTTP was run. Historical 119 native/foundation tests are accepted prior evidence, not rerun or counted here.
