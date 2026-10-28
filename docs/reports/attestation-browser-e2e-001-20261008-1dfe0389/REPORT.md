# NUSANTARA-MDE-ATTESTATION-BROWSER-E2E-001 v1.0 — Execution Report

Date: 2026-10-08. **Technical result: PASS_SCOPED** for isolated mock-only browser validation. **Human acceptance: pending separate human review.** No runtime or gate promotion.

## Authorization, audit and historical evidence

The human explicitly granted execution of E2E-001 v1.0 for isolated test implementation and validation only. The contract was reread; its preparation-time NOT_GRANTED label was preserved as historical document text, not edited into an authorization/gate record. Authority for this bounded task is the human message.

The UI Completion Audit `ui-completion-audit-20261008-a14ec92f` reported UI PARTIAL and 53 isolated tests; it had not run real-browser ATTESTATION cases. The subsequent historical report `attestation-browser-e2e-20261008-6c913a2d` recorded 12 browser passes and earlier failed attempts. Those results were inspected but were **not counted as this execution's results** or overwritten. Historical mobile overflow and browser-revision mismatch remain limitations.

New results below come from this new report directory. Synthetic browser clicks are automated tests, not actual human acceptance, provider evidence, or authenticated server decisions.

## Revalidated baseline

- Root: `C:/Users/dmaza/mcp-starter`.
- Branch: `codex/fullroot-control-20261007`.
- HEAD: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`.
- Staging empty; 26 inherited tracked modifications preserved.
- Full accessible tracked/untracked Git status captured before/after. No differences outside this fresh report directory.
- All five digest references in the approved contract matched current files; `CONTRACT_DIGEST_COMPARISON.json` records them.
- `FILES_BEFORE.json` / `FILES_COMPARISON.json`: **387 existing source/test/configuration/contract/historical-evidence files unchanged**. No database/knowledge-store digest was read.
- Existing Chromium headless revision 1234 executable was inspected before launch. `BROWSER_STATIC.json` records its path and file length; Windows product-version metadata was unavailable (null). Read-only installed-browser registration maps revision 1234 to **151.0.7922.34**, preserved in `BROWSER_VERSION_MAPPING.json`. This is static installation metadata, not a newly observed browser runtime version receipt; no extra browser was launched to obtain it.

Git warns that five inherited report directories are inaccessible. They were not opened/repaired, and preservation claims apply to accessible observed state. Git is metadata evidence, not a content digest of every untracked repository file. No reset, cleanup, checkout, staging or commit occurred.

## Proven minimum gap and actual implementation

Static inspection found no missing requested case in `control-plane/e2e/attestation.spec.ts`; its digest remained `27292c741acad5186cea4b856d172fcb090d387b004c77ee2385c7318e6f508d`. No test/specification or application source change was needed.

The historical harness checked mode/guard at config evaluation, but several safety checks depended on a fixture that receives an already-created browser context/page. Executable availability also was not checked by configuration. Contract section 4 requires these checks **before launch**.

Minimum remediation was confined to the new report directory:

- `validate_config.cjs`: checks mode/live flag/Node guard, rejects remote browser hooks, servers/global setup/alternate projects, verifies exact virtual baseURL, selected spec, output directory, worker/retry/timeouts, service-worker blocking, browser executable existence, DNS/proxy/background settings, and reviewed specification digest.
- `playwright.mock.config.cjs`: builds the scoped configuration and calls that validator during configuration evaluation, before Playwright browser/server launch; output goes only to this new directory.
- `preflight.cjs`: exercises valid and invalid configuration objects/environment without launching Chromium or dispatching any request.
- `node_guard.cjs`: byte-for-byte copy of the historical guard. Historical guard itself is unchanged.
- `PLAN.md`: records the gap, authorized scope and exact planned commands before execution.

No existing files were edited. Shared Playwright/Vite/configuration, frontend/backend source, R2-A11, NORMAL E2E, contract/gate/authorization records, dependency manifests and historical artifacts remain unchanged. Only new report-owned files were created. No existing test code changed, so no graph update was needed or performed.

## Prelaunch isolation evidence — new

`PREFLIGHT.json` and `PREFLIGHT.log`: **14 configuration checks passed**, exit 0. One valid config was accepted; 13 negative cases were rejected as expected: server, live baseURL, wrong test selection, service-worker allowance, missing DNS boundary, proxy bypass, wrong executable, remote connect options, retry, missing mode, live flag, remote environment, missing guard. These mutations were test objects, not attempts to run unsafe services or requests.

Preflight records `browser_launched:false`, `network_dispatched:false`, `READY_MOCK_ONLY`. The same validation ran again when loading the actual Playwright config. No missing/mismatched prerequisite or rejected real execution needed a workaround.

Boundary during browser tests:

- Virtual origin `http://attestation-e2e.invalid`; documents, bundle/CSS and both UI APIs fulfilled in memory.
- Existing frontend bundled with `write:false`, synthetic build metadata; no deployment/UI production build.
- Exact route/method/body allowlist; no request continuation/forwarding/real fetch.
- Service workers blocked, context-wide WebSockets closed, Node socket/listener/fetch/protected reads blocked.
- Browser deny proxy, no loopback bypass, DNS deny, disabled background network features.
- No backend/health/provider/model/database/RAG/native modules or live service request involved. Fixture endpoint/PID strings are display data only.
- Unexpected routed activity or browser runtime/console errors fail the test. Expected mocked 503/409 diagnostics and the one virtual-route abort are recorded explicitly per case.

The existing spec's unlisted-route negative case was not broadened. It attempted only `/unlisted-boundary-test` at the virtual origin, was blocked, and preserved that abort. No production address was probed. These are scoped application/harness guards, not an exhaustive OS firewall/browser-internals audit.

## Commands and actual results — new

Environment for both commands:

```powershell
$env:CPLANE_ATTESTATION_E2E='MOCK_ONLY'
$env:NODE_OPTIONS='--require=C:\Users\dmaza\mcp-starter\docs\reports\attestation-browser-e2e-001-20261008-1dfe0389\node_guard.cjs'
```

Preflight, from repository root:

```powershell
& 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' docs/reports/attestation-browser-e2e-001-20261008-1dfe0389/preflight.cjs
```

Browser run, from `control-plane`:

```powershell
& 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' node_modules/@playwright/test/cli.js test --config ../docs/reports/attestation-browser-e2e-001-20261008-1dfe0389/playwright.mock.config.cjs
```

Both commands' stdout/stderr were captured with `Tee-Object` to PREFLIGHT.log and BROWSER_RUN.log. Results: **12 passed; 0 failed/errors/skipped/flaky; zero retries; 11.6 seconds; browser run exit 0**. One browser acceptance run only; no repeated smoke/diagnostic browser run. Existing full ATTESTATION spec is the smallest complete acceptance selection. Historical tests were not rerun as additional regression; live/NORMAL E2E files were excluded entirely by exact testMatch, not executed. No grep deselections within the selected spec (0); this is not a full-suite PASS claim.

Selected IDs, all `control-plane/e2e/attestation.spec.ts`:

| Line | Test title | Result |
| --- | --- | --- |
| 94 | five stages render, scroll and submit only explicit PENDING intention | PASS |
| 107 | direct /evidence cannot bypass review | PASS |
| 107 | direct /test cannot bypass review | PASS |
| 107 | direct /review cannot bypass review | PASS |
| 107 | direct /decision cannot bypass review | PASS |
| 111 | API failure remains unavailable | PASS |
| 111 | malformed snapshot remains unavailable | PASS |
| 118 | API rejection intention fails closed without automatic retry | PASS |
| 118 | invented authority intention fails closed without automatic retry | PASS |
| 118 | wrong evidence intention fails closed without automatic retry | PASS |
| 130 | material context change clears pending and relocks the session | PASS |
| 141 | network boundary aborts an unlisted virtual-origin request | PASS |

`RESULTS.json` records exact argv, timestamps, selected IDs and attachments. `EVIDENCE_SUMMARY.json` decodes per-case network evidence and rendering metrics. There were no failed browser attempts in this execution. The historical failures remain only in the old report.

One state-capture helper diagnostic occurred after tests: PowerShell Set-Content with empty Git cached-diff output did not materialize the empty STAGED_AFTER.txt; reading it emitted FileNotFound. Empty staging had already been observed from Git, and both empty evidence files were explicitly created afterward. `STATE_CAPTURE_DIAGNOSTIC.txt` preserves the cause/correction. This did not change Git state, browser results or test assertions. Node also emitted NO_COLOR/FORCE_COLOR precedence warning; five Git permission warnings are preserved. No warning was suppressed or turned into a PASS result.

## Acceptance and residual limitations

New browser evidence supports all bounded criteria: explicit five-stage navigation and prerequisite locks; separate PASS/FAIL/BLOCKED human observations; no authority controls; only explicit one-shot synthetic PENDING with “untrusted/no authorization” text; error/malformed/claimed-authority/wrong-version rejection; pending/context reset; blocked unknown virtual route; no unexpected routed activity; preserved repository state. Provider receipt remains null and runtime verification NOT_VERIFIED.

Real mobile screenshot and metrics are preserved in `browser-results/` and result attachments. **Viewport 390 px; document width 602 px; vertical scrollY 1193; document height 1988 px.** Horizontal overflow is reproduced and remains a UI gap. Responsive layout is not marked PASS and no CSS fix was performed.

Installed browser revision 1234 was used explicitly although the runner's default expects 1243; successful execution establishes this scoped run, not general version portability. In-memory bundle bypasses Vite/proxy/production hosting. Synthetic timestamps, process identity and build metadata cannot establish actual freshness, runtime process/build correlation, provider/model invocation or persisted/native decisions. No human accepted these new results yet.

No dependency/browser installation, service start/restart/reload, provider invocation, HTTP to production/live service, database/protected-state access, permit/ARM/EXECUTE/native IPC, policy provisioning, production decision mutation or R2-A11 correction occurred.

## Diff review and final authority

`GIT_COMPARISON.json` confirms unchanged branch/HEAD, empty staging, 26 tracked modifications before/after, and zero accessible inherited-status differences outside this report directory. `FILES_COMPARISON.json` shows 387 monitored files unchanged, including the contract, spec, application/test/config paths and historical evidence. New helpers/evidence/report are inventoried in `ARTIFACT_MANIFEST.json`; no inherited files were removed/replaced.

- Full Runtime Identity: **NOT_VERIFIED**.
- ACTIVE_PROCESS_BUILD: **NOT_DIRECTLY_VERIFIED**.
- Live provider/model correlation: **NOT_VERIFIED**.
- R2-A8: **BLOCKED / NOT_VERIFIED**.
- R2-A9: **HOLD**.

Technical PASS_SCOPED is limited to the mock-only browser/harness evidence above. It is not authorization activation or human acceptance. **STOP after this report and diff review; wait for the next human decision.**
