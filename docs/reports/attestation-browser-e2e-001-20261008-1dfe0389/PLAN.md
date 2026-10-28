# Authorized execution plan — E2E-001 v1.0

Authorization comes from the current explicit human message; the governing contract and existing gate records remain unchanged.

Static inspection found no missing acceptance case in the existing 12-test ATTESTATION specification. Preserve its digest and avoid test/application edits. Historical 12-pass evidence is reference only. One new run is necessary to produce results under the newly approved contract and newly validated prelaunch boundary; do not repeat previous diagnostic attempts or existing live/NORMAL suites.

Minimum harness gap: historical config rejects mode/guard but relies on the browser-dependent test fixture for other configuration checks. It lacks a prelaunch executable-existence check. Fresh report-owned validate_config.cjs validates all relevant settings and unchanged reviewed specification before Playwright loads its config. Fresh preflight.cjs exercises safe configuration mutations without launching a browser, starting any server, or dispatching requests. Reuse the historical Node guard byte-for-byte; all historical files remain immutable.

Scope of created files is this new report directory only. Shared config, UI/backend/application source, test specification, R2-A11, dependencies and existing evidence remain unchanged. No graph update is needed because existing test code is unchanged.

Execution from C:\Users\dmaza\mcp-starter\control-plane:

```powershell
$env:CPLANE_ATTESTATION_E2E='MOCK_ONLY'
$env:NODE_OPTIONS='--require=C:\Users\dmaza\mcp-starter\docs\reports\attestation-browser-e2e-001-20261008-1dfe0389\node_guard.cjs'
& 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' ../docs/reports/attestation-browser-e2e-001-20261008-1dfe0389/preflight.cjs
# Only if preflight succeeds:
& 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' node_modules/@playwright/test/cli.js test --config ../docs/reports/attestation-browser-e2e-001-20261008-1dfe0389/playwright.mock.config.cjs
```

The 12 cases are the smallest existing complete acceptance selection. A separate repeated browser smoke test is unnecessary after proven historical behavior and successful new prelaunch validation. Retries remain zero. Record failures and STOP on a boundary violation or application defect. Finish evidence/diff/report then STOP.
