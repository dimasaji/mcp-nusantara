# ATTESTATION Browser E2E — isolated implementation report

Date: 2026-10-08. Outcome: **PASS_SCOPED** for the requested mock-only browser behavior. This is not UI production completion or runtime verification.

## Repository and preserved state

Repository: `C:\Users\dmaza\mcp-starter`.
Branch: `codex/fullroot-control-20261007`.
HEAD: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`.
The 26 inherited tracked modifications remain present; initial and final tracked status match. Staging remained empty. No reset, cleanup, checkout, staging or commit was performed. The new specification did not exist before this task. No inherited evidence was overwritten.

`GIT_BEFORE.txt`, `GIT_AFTER.txt`, `STAGED_BEFORE.txt`, `STAGED_AFTER.txt` record state. `PRIOR_AUDIT_SOURCE_COMPARISON.json` compares existing source hashes against the prior UI audit; this is historical comparison, not a newly captured pre-test content baseline.

## Implementation and explicit isolated mode

Added only `control-plane/e2e/attestation.spec.ts` outside the fresh report directory. No application/backend/UI source, shared Playwright configuration, Vite configuration, package manifest or dependency was changed.

The specification uses existing Playwright and installed esbuild. It bundles the existing `src/main.tsx` and imported UI/CSS into memory (`write:false`), and fulfills documents/assets through browser context interception at `http://attestation-e2e.invalid`. There is **no listening test host**, no Vite server, no production backend, and no request forwarding. The Vite build constant is supplied as explicitly synthetic test metadata, never as runtime build evidence.

Report-owned infrastructure:

- `playwright.mock.config.cjs`: separate configuration, exactly this spec, one worker, zero retries, Chromium headless, service workers blocked, no webServer. Requires mock-only mode, rejects the live flag and missing Node guard.
- `node_guard.cjs`: rejects Node socket connections, listening servers, fetch, and protected SQLite/knowledge file reads through covered filesystem methods.
- Synthetic snapshot/intention fixtures live in the specification. Provider receipt is null, status NOT_VERIFIED, live actions LOCKED, operator NOT_PROVISIONED. Fixture PIDs/model endpoint strings are display data only.

Browser HTTP routing permits only the virtual origin, exact document/asset paths, GET snapshot, and POST intention with exactly scope/evidence-version JSON. Everything else is aborted and recorded. No `route.continue()` or real network fetch exists. Context-wide WebSocket routing closes connections. Unexpected blocked requests fail fixture teardown. One explicit negative case expects exactly its own virtual-origin unlisted request to be blocked; that evidence remains recorded, not discarded.

Chromium uses a deny proxy at `127.0.0.1:9`, loopback bypass disabled, wildcard DNS resolution denied, and background network features disabled. Node guard is inherited by test workers. These are harness/application traffic protections, not a claim of an audited OS firewall or comprehensive browser internals attestation.

## Exact execution

Working directory: `C:\Users\dmaza\mcp-starter\control-plane`.

```powershell
$env:CPLANE_ATTESTATION_E2E='MOCK_ONLY'
$env:NODE_OPTIONS='--require=C:\Users\dmaza\mcp-starter\docs\reports\attestation-browser-e2e-20261008-6c913a2d\node_guard.cjs'
& 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' node_modules/@playwright/test/cli.js test --config ../docs/reports/attestation-browser-e2e-20261008-6c913a2d/playwright.mock.config.cjs
```

Final command: **12 passed, 0 failed, 0 errors, 0 skipped, 0 flaky; zero retries; 12.4 seconds**. Only this new specification was selected; existing NORMAL/live E2E files were excluded by exact `testMatch`, not executed. This command is intentionally required; the spec rejects collection outside MOCK_ONLY rather than silently using shared live/default hosting.

`RESULTS_ACCEPTED.json` includes command argv, test IDs, timings and per-test attachments. `EVIDENCE_SUMMARY.json` decodes the mock network and layout evidence for review. `browser-results-accepted/` includes a real Chromium full-page mobile screenshot.

| Selected case | Result |
| --- | --- |
| Five stages render, scroll and submit only explicit PENDING intention | PASS |
| Direct /evidence cannot bypass review | PASS |
| Direct /test cannot bypass review | PASS |
| Direct /review cannot bypass review | PASS |
| Direct /decision cannot bypass review | PASS |
| API failure remains unavailable | PASS |
| Malformed snapshot remains unavailable | PASS |
| API rejection intention fails closed without automatic retry | PASS |
| Invented authority intention fails closed without automatic retry | PASS |
| Wrong evidence intention fails closed without automatic retry | PASS |
| Material context change clears pending and relocks the session | PASS |
| Network boundary aborts an unlisted virtual-origin request | PASS |

Explicit clicks select mixed PASS/FAIL/BLOCKED **human observations**, with FAIL/BLOCKED still visible at Review. They do not alter engineering verification status. Every stage lacks APPROVE/ARM/EXECUTE/CONFIRM APPROVAL buttons. Traversal produces zero intention posts until the explicit Create PENDING intention click. Successful submission displays “untrusted intention; no authorization granted,” and disables duplicate submission. Failure responses never render a PENDING success or authenticated authority. Changed evidence version/runtime instance clears pending and upstream acknowledgements and relocks Decision.

An additional collection-only negative command removed `CPLANE_ATTESTATION_E2E` and ran the same command with `--list`: exit **1**, `UNSAFE_TEST_MODE`, before any browser/server launch. Evidence: `UNSAFE_MODE_REJECTION.txt`.

## Preserved diagnostic runs and warnings

No initial failure is represented as a pass:

- `RESULTS.json`: 11 failures before browser startup; Playwright expected absent Chromium headless revision 1243.
- `RESULTS_INSTALLED.json`: one smoke failure with installed revision 1234; synthetic in-memory bundle lacked Vite's `__CPLANE_BUILD__` constant.
- `RESULTS_DIAGNOSTIC.json`: one diagnostic failure, console evidence identified the missing constant. Only the test bundle definition was corrected.
- `RESULTS_SMOKE.json`: one smoke pass after correction.
- `RESULTS_FINAL.json`: initial full run, 12 passes.
- `RESULTS_REVIEWED.json`: 10 passes/2 failures after adding overly strict console checks. Expected mocked HTTP 503/409 browser resource diagnostics caused these test-harness failures, while UI rejection assertions passed. Final harness expects those exact diagnostics per relevant negative case; unrelated console/runtime errors still fail. The blocked-route diagnostic is also explicitly expected in its single negative case.
- `RESULTS_ACCEPTED.json`: final specification, 12 passes.

Existing Chromium headless revision 1234 was selected explicitly; no browser/dependency installation was performed. The runner expects revision 1243 by default, so browser/runner version alignment remains a portability limitation despite successful scoped execution. Node reported NO_COLOR/FORCE_COLOR precedence warnings. No unexpected browser runtime error or unexpected routed network request occurred in the final run.

## Residual gaps and visual evidence

Actual browser rendering and vertical scrolling were exercised. Mobile layout evidence shows **390 px viewport, 602 px document width**: long evidence identifiers overflow horizontally. This is a visible residual UI issue, not a responsive-layout PASS. No CSS/UI correction was authorized or performed. Screenshot and rendering-metrics attachment preserve it.

This mode bypasses Vite serving/proxy and uses synthetic build metadata. It does not verify production hosting, localhost proxy behavior, live snapshot freshness, server/native actor attribution, persisted decisions, real receipts, provider/model invocation, runtime process binding or full build identity. Fixture timestamps and identity values are intentionally synthetic. No backend modules or database were imported/executed. No real API, health, generation, IPC, permit, ARM, EXECUTE, service loading, restart or deployment occurred.

Only new browser cases were executed; the broader historic UI/API tests were not rerun because application source was unchanged and the contract requested only isolated E2E. New bundle harness does not establish every browser engine, accessibility conformance or deployment equivalence.

Graphify query supported discovery. Repository instruction requires `graphify update .` after code changes; the update was AST-only with no LLM/API use. Derived graph files are separate from application/configuration changes. Existing inaccessible historical report directories remain untouched and may be absent from graph enumeration; graph labels are not verification evidence.

## Final authority and stop

- Full Runtime Identity: **NOT_VERIFIED**
- ACTIVE_PROCESS_BUILD: **NOT_DIRECTLY_VERIFIED**
- Live provider/model correlation: **NOT_VERIFIED**
- R2-A8: **BLOCKED / NOT_VERIFIED**
- R2-A9: **HOLD**

No gate or authorization record was modified or promoted. The immediate mock-only browser behavior gap is covered; operational and visual gaps remain explicitly bounded. **STOP**. Any UI overflow fix, production verification, native integration or activation requires a separate human decision.
