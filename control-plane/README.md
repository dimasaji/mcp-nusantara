# Nusantara Engineering Control Plane v0.1

Local, read-only projection of existing engineering evidence. Owner approval and exact file scope are recorded in CPLANE_OWNER_AUTHORIZATION.json and SCOPE.json. Existing chat/review UI is preserved.

Run `npm ci --ignore-scripts`, then `npm run dev` inside this directory. The frontend binds 127.0.0.1:5180 and proxies configured API routes to the existing FastAPI app on 127.0.0.1:8000. Ports are defined in `../config/local-services.json`. Windows lifecycle and autostart commands authorized under NCP-V1-AUTOSTART-001 are documented in `../docs/NCP-V1-AUTOSTART-001.md`. Startup can initialize database/worker owners; isolated evidence-only mode remains available below.

For the Owner-approved local evidence-only mode, run the existing backend entrypoint from the repository root in a separate PowerShell terminal:

```powershell
cd C:\Users\dmaza\mcp-starter
$env:NUSANTARA_CONTROL_PLANE_READ_ONLY = '1'
& .venv\Scripts\python.exe -B -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then run the frontend command above and open http://127.0.0.1:5180/overview. Evidence-only boot skips production API/configuration/knowledge/model/worker composition. Only the GET evidence projection is mounted; chat and legacy runtime UI are unavailable. `/health` reports `evidence_only` and `runtime: NOT_VERIFIED`. This is a local process flag; no runtime configuration file is changed. In a fresh terminal the normal startup remains the default. A missing backend previously made the Vite proxy return HTTP 500.

`npm run build` performs TypeScript validation and a production build. `npm test` and `npm run e2e` consume a real read-only projection JSON supplied through CPLANE_SNAPSHOT_FILE. E2E intercepts the API with this actual captured projection; backend integration is tested separately with FastAPI TestClient. No second production backend is introduced.

Missing/invalid/hash-mismatched evidence remains UNKNOWN/NOT_VERIFIED. Runtime receipts are historical, and R3 knowledge receipts are fixtures. The projection does not assert current production execution. Manual refresh only; no credentials are persisted in the browser, no state-changing API calls, no Git mutation, no SQLite connections.

R3 artifact references point to its existing temporary audit directory. If that directory disappears, R3 state becomes NOT_VERIFIED; evidence is never reconstructed. Full-root Graphify coverage is distinct from the declared UI graph. Dependency changes/build output are confined to this directory. Commit and push remain unauthorized.

## Human Acceptance Console

## V1 user and operator control (2026-10-09)

`/` is the user conversation UI; `/console` is the operator model panel. The existing evidence workflow remains at `/overview`. Operator inventory/selection uses the existing admin-token mechanism; tokens stay in component memory and are not persisted. The operator selects a real provider inventory identity rather than an invented speed/cost profile. Runtime selection is volatile and applies to subsequent V1 requests in the current NORMAL process; multiple declared workers reject it, and cross-process consistency is not claimed. A conflicting legacy per-request model override returns 409.

Build with the existing project dependencies before starting a local candidate. NORMAL backend serves `control-plane/dist/index.html` and `/assets`; the existing Dockerfile requires this prebuilt bundle in its build context. No image build/deployment was performed. Vite's exact `/v1/chat` proxy uses the same backend as the existing Console API. No second backend is introduced.

Memory remains legacy and CC-05 is open. Unsupported nonempty knowledge filters are rejected; official-source authority is not inferred from retrieval relevance. Guarded integration uses explicit external fixtures and must not be described as a live installed-model or production verification. Evidence is in `docs/reports/v1-user-hermes-implementation/`.

The read-only statements elsewhere in this README describe the evidence workflow, not the new authenticated operator model-selection action.

Open `/overview` for the primary flow: **System → Evidence → Human Test → Review → Decision**. Previous engineering views remain under the expandable Engineering views navigation; the previous Overview is now `/engineering-overview`.

Engineering gates come from the same existing GET API. The eight human checks default to **NOT TESTED** and change only when a reviewer selects PASS, FAIL or BLOCKED. Approval requires the System acknowledgement, inspection and acknowledgement of all 14 R3 gate sources, verified recorded gate evidence, all eight human checks PASS, an initially unchecked review checkbox, and a separate confirmation. REJECT and HOLD require reasons; Other also requires notes. A missing evidence response blocks approval.

Human results and decisions are **in-memory session state**. They persist through SPA navigation, clear on page reload, and are invalidated when material evidence changes. A timestamp-only refresh preserves the session. These selections do not write files, evidence, backend governance or R2 Authorization; no authorization endpoint was added. Automated E2E decisions are UI test inputs, not Owner acceptance.

Runtime NOT VERIFIED, fixture/historical receipts, temporary evidence storage and current protected-sidecar limitations remain explicit. The pre-existing WAL/SHM integrity HOLD is retained; this frontend implementation does not resolve or repair it.

Run `npm test` with CPLANE_SNAPSHOT_FILE pointing to an actual captured projection JSON. `npm run e2e` uses its own frontend test server on 5174 and intercepted actual captured data. With `CPLANE_E2E_LIVE=1`, Playwright uses the independently running UI on 5173; the full human flow reads the existing API directly, while negative-path tests use explicitly scoped test interceptions. No backend is started by these tests.
