# Control Plane UI completion audit — 2026-10-08

**Audit conclusion: PARTIAL. Existing scoped UI is implemented and passes isolated tests; deployed UI completion remains NOT_VERIFIED.** This is an audit finding, not a gate promotion. No source/configuration modification, service start or R2-A11 correction performed.

## Repository and evidence classes

Observed root C:/Users/dmaza/mcp-starter; branch codex/fullroot-control-20261007; HEAD 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab. GIT_BEFORE/AFTER/COMPARISON.json show unchanged tracked state/HEAD/branch and empty staging. The 26 inherited tracked modifications are preserved. SOURCE_STABILITY.json verifies **380 monitored source/test/script/service paths unchanged**. No protected-data hash/read used to establish this.

SOURCE = inspected implementation; TEST_ISOLATED = tests actually executed below; HISTORICAL = previous reports, not current service evidence. No new LIVE_SERVICE observation, provider evidence or human acceptance was collected. Existing graph query was read-only (367 nodes, truncated to 21); detailed claims below come from direct source/tests. No graph rebuild.

## Actual frontend/backend inventory

Frontend: control-plane/src/main.tsx (React, QueryClient retry:false/refetchOnWindowFocus:false); router.tsx (actual registered routes); human.tsx (two projection-specific five-stage consoles); acceptance.ts (session, prerequisites, evidence fingerprints); api.ts (typed fetch/intention); schemas.ts (separate strict ATTESTATION schema and NORMAL schema); ui.tsx (engineering views); graph.tsx/styles.css (engineering graph/presentation). Existing package/Vite/Vitest/Playwright configurations inspected; no build/install/server executed.

Registered pages: /, /overview and /system lead to SYSTEM; /evidence, /test, /review, /decision map the remaining human stages. Engineering views: /engineering-overview, /roadmap, /architecture, /engineering, /governance, /verification, /runtime, /knowledge. Existence of these routes alone is not operational proof; rendering/navigation tests provide the scoped evidence.

Backend UI endpoints in app/api/control_plane.py:

| Endpoint | Actual source behavior | Current audit evidence |
|---|---|---|
| GET /v1/control-plane/snapshot | Loopback guard; ATTESTATION owner.evidence(), otherwise NORMAL project() | Guarded in-process ATTESTATION snapshot produced and parsed by current UI tests; no deployed call |
| POST /v1/control-plane/intention | ATTESTATION-only, strict peer/Host/Origin/JSON, scope/version only, bounded body; returns PENDING or rejects | Guarded in-process PENDING; mocked browser client success/rejection/context mismatch; no live POST |
| GET /v1/runtime/attestation | Existing separate runtime observation surface in runtime_attestation; not fetched by UI api.ts | Historical C0 only, no new request; not evidence that UI has direct runtime integration |
| POST /v1/runtime/verification | Separate diagnostic surface, not a UI API call | Not run/used in this audit; generation/authority outside scope |

Vite source proxies /v1/control-plane to port 8000 with changeOrigin:true. Host/Origin/proxy compatibility in a real browser is unverified here. Missing ATTESTATION owner produces 503; intention returns 404 for other profiles, rejects boundary/format/stale context rather than granting authority.

NORMAL project() in app/core/control_plane_projection.py reads historical engineering artifacts and digests protected database/WAL/SHM files (source lines 122–126). **It was not called or imported as a running projection.** Tests use a saved synthetic NORMAL fixture. A deployed browser automatically fetching snapshot cannot be assumed safe while serving profile/build is unknown; this audit did not start that browser/service path.

## Required matrix

| Area | Implementasi ditemukan | Bukti tes baru | Gap | Status |
|---|---|---|---|---|
| SYSTEM | Current summary/limitations, explicit acknowledgement and prerequisite locks; scoped ATTESTATION identity panel | human.test.tsx acknowledgement and locked-stage cases; attestation rendering/router cases | Live profile/build/UI availability unobserved; no actual human session | TEST_ISOLATED supported; live NOT_VERIFIED |
| EVIDENCE | NORMAL gate sources/hashes; ATTESTATION version/PID/source/scoped fields and receipt availability | UI source/historical presentation; acceptance incomplete/hash-invalid rejection; current guarded backend projection parsed | ATTESTATION explicitly has no attached automated-test evidence; full build/provider absent | PARTIAL |
| TEST | NORMAL eight human cases; ATTESTATION three observations; starts NOT TESTED, explicit PASS/FAIL/BLOCKED | acceptance separates engineering PASS from human results; human workflow and ATTESTATION observations | Tests are simulated clicks, not human acceptance; browser layout/mobile/accessibility not newly verified | TEST_ISOLATED supported; human NOT_VERIFIED |
| REVIEW | Required acknowledgement; failed/blocked observations remain visible; result/evidence changes invalidate review | human FAIL/BLOCKED/HOLD flow, withdrawn acknowledgement and fingerprint drift; attestation context reset | Review is memory/session scoped; no durable review history | PARTIAL |
| DECISION | NORMAL APPROVE/REJECT/HOLD with second confirmation/reason and session receipt; ATTESTATION PENDING-only action | human confirmation/reason tests; explicit ATTESTATION click, no automatic submit, strict PENDING/context/error tests; backend no permit/policy | NORMAL receipt is browser-local; ATTESTATION native confirmation not activated; PENDING is not authenticated decision | PARTIAL; runtime authority remains HOLD/LOCKED |
| Error/NOT_VERIFIED | API failure/malformed schema rejection, UNKNOWN/error views, missing-source fallback and explicit limitations | api.test.ts three cases; invented status rejection; no unknown-to-PASS promotion; locked bypass cases | Real server timeout/CORS/proxy/refetch error presentation and real scrolling not verified | TEST_ISOLATED supported; deployed NOT_VERIFIED |

The workflow is genuinely sequential in tested scope: SYSTEM acknowledgement → source/version review → explicit human results → REVIEW acknowledgement → session decision/PENDING intention. Automatic engineering results do not set human PASS. Human results do not change backend identity/gates. A NORMAL UI APPROVE is acceptance of that browser session only; it is not R2 authorization. ATTESTATION has no APPROVE/ARM/EXECUTE authority path in UI.

## Tests actually executed

**52 frontend tests passed**, 0 failures/errors/skips, 0 deselected: api 3, acceptance 11, ui 4, human 19, attestation 15. API fetches are mocked. NORMAL fixture is the existing SYNTHETIC_NORMAL.json from the R2-A9 implementation report, not current NORMAL production data. ATTESTATION parser test consumes this audit's fresh BACKEND_PROJECTION.json.

**1 backend test passed**, 0 failures/errors/skips, **30 deselected**: tests/test_control_plane_attestation_binding.py::test_guarded_application_composition_no_network_or_protected_state. This executes existing app.main composition in a subprocess with protected-state/network/provider/native guards and TestClient in-process ASGI; owner policy None, permit None, dispatch_count=0, live_http=false, live_actions=LOCKED. Memory-only PENDING fixture state is discarded; production data is not changed. Other backend cases were unnecessary for this audit and include policy-bearing fixtures; no full backend suite claim.

Combined: **53 tests passed**. UI.xml, BACKEND.xml, TEST_RESULTS.json contain results and exact selected test names. Backend has one inherited Starlette/httpx deprecation warning. The existing jsdom router test emits window.scrollTo-not-implemented diagnostics twice; assertions pass, but actual scrolling/visual browser behavior remains unverified. No dependency upgrade or diagnostic suppression.

Commands from repository root:

```powershell
$env:R2_CPLANE_ISOLATED_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\ui-completion-audit-20261008-a14ec92f\BACKEND_PROJECTION.json'
& .venv/Scripts/python.exe -B docs/reports/ui-completion-audit-20261008-a14ec92f/backend_runner.py
```

Commands from control-plane directory:

```powershell
$env:CPLANE_SNAPSHOT_FILE='C:\Users\dmaza\mcp-starter\docs\reports\r2-a9-control-plane-implementation-20261008\SYNTHETIC_NORMAL.json'
$env:R2_CPLANE_ISOLATED_EVIDENCE='C:\Users\dmaza\mcp-starter\docs\reports\ui-completion-audit-20261008-a14ec92f\BACKEND_PROJECTION.json'
& 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --require '../docs/reports/ui-completion-audit-20261008-a14ec92f/network_guard.cjs' node_modules/vitest/vitest.mjs run --config vitest.config.ts --cache=false --pool=threads --reporter=default --reporter=junit --outputFile.junit=../docs/reports/ui-completion-audit-20261008-a14ec92f/UI.xml
```

Node guard blocks socket connections/server listen/default fetch and protected synchronous/callback file reads; tests replace fetch with explicit mocks. Backend runner reuses existing guarded test infrastructure and disables real transport/database/provider/permit/IPC paths. No guard violation observed. These are scoped Python/Node guards, not exhaustive OS-level file monitoring. Normal tooling transforms/workers and report/temp artifacts are test activity, not production service activation.

Existing E2E files control-plane/e2e/human.spec.ts and control-plane.spec.ts were inspected **but not run**. playwright.config.ts normally starts a Vite server on 5174; live mode uses 5173. Both cross this audit's no-service/live-request boundary. Existing E2E mainly targets NORMAL fixtures/live switch; no dedicated ATTESTATION real-browser spec was found. The jsdom router test is not a substitute for Playwright/browser E2E. Historical R2-A9 83-pass implementation and failed localhost verification reports are references only, not new audit outcomes. Historical C0's source mismatch is not repaired or re-probed.

## Minimum next implementation recommendation

**One recommended next step: separately authorize a mock-only ATTESTATION browser E2E test harness**, with explicit no production backend access and strict isolation of any temporary test hosting. Extend the existing test system rather than rebuild UI or integrate native authority. This would close the most immediate UI completion evidence gap: actual five-stage navigation, render/scroll/mobile behavior, PENDING-only action, API error states and stale-context reset in a browser.

Candidate files for that future authorization: new control-plane/e2e/attestation.spec.ts; control-plane/playwright.config.ts only if needed to separate explicit isolated mock mode from service/live mode; optional control-plane/e2e/control-plane.spec.ts for common unavailable/malformed/error assertions. UI source should change only if those tests prove a defect; this audit does not establish a specific frontend code fix as necessary. Any future test host/start or browser requests must be expressly authorized with a fail-closed route/network policy. These are recommendations, not executed changes.

Broader gaps require separate decisions and must not be folded into UI polish: trusted native decision/persistence integration, safe loaded backend profile/projection availability, real provider evidence, live build correlation. Do not add browser-held permits, accept reviewer JSON, expose production DB digests or relabel PENDING as authorization. ATTESTATION engineering pages currently reuse the same bounded identity view; richer page-specific diagnostics are an optional design requirement, not proof of missing authorized authority functionality.

## Preservation and stop

Only new audit reports/helpers/test outputs were written. No application/test/config source edit, dependency installation, migrations, database/WAL/SHM/RAG/model/index/knowledge operation, service start/restart, provider probe/generation, Git reset/cleanup/staging/commit or gate mutation. No R2-A11 repair performed. Existing tracked/uncommitted work preserved. New derived fixture data does not replace historical/live evidence.

Full Runtime Identity and live provider/model correlation remain NOT_VERIFIED; ACTIVE_PROCESS_BUILD NOT_DIRECTLY_VERIFIED; R2-A8 BLOCKED / NOT_VERIFIED; R2-A9 HOLD. UI completion remains PARTIAL at current evidence scope. **STOP after this audit.**
