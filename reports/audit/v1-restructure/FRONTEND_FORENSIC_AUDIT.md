# FRONTEND_FORENSIC_AUDIT

**Project:** Nusantara V1
**Contract:** deliverable §12.12
**Date:** 2026-11-18
**Scope:** `control-plane\` — `src\` (36 files), `tests\` (30), `e2e\` (12)
**Stack:** React 19.3.0 · Vite 7.3.7 · TypeScript 5.9.3 · TanStack Router 1.170.41 · TanStack Query 5.104.1 · zod 4.6.5 · @xyflow/react 12.12.0

---

## 1. Build state — measured, after repair

| Check | Command | Result |
|---|---|---|
| Type check | `npx tsc --noEmit` | **exit 0** |
| Production build | `npx vite build` | **exit 0**, 4.07 s |
| Modules transformed | — | **446** |
| Main bundle | `dist\assets\index-Bg4-yd-G.js` | **689.90 kB** (gzip **206.31 kB**) |
| Graph chunk | `dist\assets\graph-BLDO6ogC.js` | 180.38 kB (gzip 59.11 kB) |
| CSS | `index-USRHoMw1.css` | 78.63 kB (gzip 15.84 kB) |
| Warning | chunk > 500 kB | advisory only, build succeeds |

### 1.1 Two defects found and fixed

**Defect 1 — `TS2322` type error made the whole build fail.**

`control-plane\src\overview.tsx:199` passed `onChanged={()=>query.refetch()}` to `SOPReviewPanel`, but the component never declared that prop. `npm run build` runs `tsc --noEmit && vite build`, so type checking failure blocked the artefact entirely.

Fix — declare the optional prop and invoke it after a successful mutation:

```tsx
// control-plane\src\sop-review.tsx:75
export function SOPReviewPanel({
  documentId, token, autoProcess = false, onChanged,
}: {
  documentId: string; token: string; autoProcess?: boolean; onChanged?: () => void;
}) {

// control-plane\src\sop-review.tsx:~120, inside act()
try {
  await action();
  await load();
  setReport(null);
  setPublicationAction(null);
  setNote('');
  onChanged?.();          // ← new
}
```

This is an **additive, optional** prop. No existing call site changes behaviour; the only consumer that passes it (`overview.tsx`) now gets a knowledge-list refresh after approving a SOP, which is what it was already asking for.

**Defect 2 — esbuild could not create its temp file.**

Failure:

```
[vite:esbuild-transpile] remove
C:\Users\dmaza\AppData\Local\Temp\esbuild-e6c9b0ab… : Access is denied.
```

esbuild writes an intermediate file to `%TEMP%`, and in this environment that directory denies writes to the sandboxed process. Fix is environmental, not a code change: point the build's temp directory inside the repository.

```powershell
$env:TMP = "C:\Users\dmaza\mcp-starter\.tmp-build"
$env:TEMP = $env:TMP
$env:TMPDIR = $env:TMP
npx vite build
```

`.tmp-build/` is gitignored (`.tmp-build/` rule). With this in place the build is reproducible.

### 1.2 Consequence for Docker

`Dockerfile:14` previously read:

```dockerfile
# COPY control-plane/dist ./control-plane/dist  # Optional, build separately
```

Because `dist/` did not exist (build was broken), the frontend was absent from the image. With the build repaired, the line is restored to:

```dockerfile
COPY control-plane/dist ./control-plane/dist
```

Verified inside the built image:

```
/app/control-plane/dist/index.html
/app/control-plane/dist/assets/graph-BLDO6ogC.js
/app/control-plane/dist/assets/graph-BnuhLJ6X.css
/app/control-plane/dist/assets/index-Bg4-yd-G.js
/app/control-plane/dist/assets/index-USRHoMw1.css
```

---

## 2. Source inventory — 36 files, 3,754 lines

| File | Lines | Bytes | Role |
|---|---:|---:|---|
| `human.tsx` | 336 | 49,088 | **Largest module** — human review surface, 10 exports |
| `api.ts` | 355 | 30,676 | Typed API client |
| `engineering-evidence.ts` | 739 | 30,261 | Evidence model + projections |
| `styles.css` | 286 | 49,952 | Global stylesheet |
| `overview.tsx` | 228 | 22,586 | Overview + knowledge operations |
| `sop-review.tsx` | 188 | 25,371 | SOP review panel |
| `operator-design.css` | 174 | 19,813 | Operator theme |
| `assistant.tsx` | 167 | 27,790 | Chat + operator console |
| `sop-metadata.tsx` | 143 | 13,197 | Official metadata form |
| `readiness.ts` | 145 | 9,939 | Readiness model |
| `operator.tsx` | 130 | 21,774 | 8 operator pages |
| `acceptance.ts` | 94 | 7,465 | Acceptance workflow |
| `hermes-connection.tsx` | 74 | 4,509 | Hermes connection panel |
| `workspace.css` | 75 | 6,205 | Workspace theme |
| `settings.tsx` | 60 | 6,384 | Settings |
| `ui.tsx` | 58 | 12,285 | Shell, navigation, badges |
| `human-control.tsx` | 51 | 11,073 | Human control view |
| `operator-panels.tsx` | 51 | 9,210 | Drawers + registries |
| `engineering-console.tsx` | 49 | 10,558 | Engineering console |
| `router.tsx` | 45 | 4,826 | Route table |
| `sop-progress.tsx` | 45 | 5,483 | Review progress |
| `schemas.ts` | 44 | 6,416 | zod schemas (12 exports) |
| `chat-citation.tsx` | 38 | 3,563 | Citation renderer |
| `workspace.tsx` | 38 | 8,685 | Workspace page |
| `runtime-readiness.tsx` | 22 | 2,524 | Readiness panel |
| `sop-workspace.css` | 22 | 2,544 | SOP theme |
| `work-approval-guide.tsx` | 21 | 1,205 | Static guide |
| `sidebar.tsx` | 19 | 1,087 | Sidebar |
| `auth.tsx` | 12 | 578 | **Admin auth provider — 12 lines** |
| `graph.tsx` | 11 | 2,632 | Graph wrapper |
| `technical-view.tsx` | 10 | 396 | Technical toggle |
| `sop-progress.css` | 10 | 1,189 | Progress theme |
| `main.tsx` | 9 | 583 | Entry point |
| `verification.tsx` | 4 | 225 | Verification page |
| `engineering-console.css` | 1 | 1,035 | Console theme |
| **`human.tsx.bak`** | **151** | **30,796** | **Stale backup — ARCHIVE** |

### 2.1 Finding — `human.tsx.bak` is the third-largest file in `src\`

A 30,796-byte backup of `human.tsx` sits in the shipped source directory. Vite does not bundle it (no import references it), but it is committed, and it is 151 lines of stale duplicate logic. Classified **ARCHIVE** in `FILE_ARCHIVE_MANIFEST.csv`. Its presence means `grep` over `src\` returns two versions of every symbol in the human surface.

---

## 3. API client — `api.ts` (355 lines)

The client is the entire frontend-to-backend contract in one file. Exports include:

`ModelStatus`, `fetchModelStatus`, `fetchRuntimeHealth`, `fetchRuntimeReadiness`, `CostSummary`, `fetchCostSummary`, `OperationsSummary`, `fetchOperationsSummary`, `KnowledgePipelineRun`, `SOPWorkflowState`, `SOPWorkflow`, `SOPSummary`, …

| Property | Assessment |
|---|---|
| Typed request/response pairs | **Yes** — domain types exported alongside fetchers |
| Single client module | **Yes** — no scattered `fetch()` calls in components except `sop-review.tsx` |
| Credential handling | `credentials:'omit'`, `redirect:'error'`, explicit `X-Admin-Token` header |
| Error normalisation | `hermesHttpError` / `hermesReason` in `hermes-connection.tsx` |

### 3.1 Finding — one component bypasses the client

`control-plane\src\sop-review.tsx:52-56` declares its own `requestReview()`:

```tsx
async function requestReview(path, token, body?, source=false) {
  const response = await fetch(`/v1/knowledge/pipeline/reviews/${path}`, {
    method: body ? 'POST' : 'GET',
    signal: controller.signal,
    cache: 'no-store',
    credentials: 'omit',
    redirect: 'error',
    headers: { 'X-Admin-Token': token, ...(body ? {'Content-Type':'application/json'} : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
}
```

It is written defensively (abort signal, no-store, no redirect, credentials omitted), so this is **not a security defect** — but it is a second HTTP entry point that `api.ts` does not know about. A future change to base URL, auth header, or proxy prefix must be made in two places.

---

## 4. Routing

`control-plane\src\router.tsx` (45 lines) — TanStack Router, code-based route table.

| Surface | Component | Purpose |
|---|---|---|
| Overview | `OverviewPage` | System snapshot |
| Knowledge operations | `KnowledgeOperationsPage` | Pipeline runs, SOP list, review |
| Operator | `OperatorHome`, `TasksPage`, `BlockersPage`, `CostsPage`, `TechnicalPage` | Operator console |
| Human | `HumanPage` + 7 sub-exports | Human review + attestation + execution review |
| Settings | `SettingsPage`, `RuntimeSettingsPage` | Config |
| Workspace | `WorkspacePage` | Task workspace |
| Verification | `VerificationPage` | Evidence verification |
| Readiness | `RuntimeReadinessPanel` | Readiness probes |

Routing covered by `tests\ui-routing.test.tsx` (67 lines) and `e2e\operator-contract.spec.ts`.

---

## 5. Test inventory

### 5.1 Unit / component — vitest (30 files + 1 stale `.bak`)

Largest: `assistant.test.tsx` (300 lines), `sop-review.test.tsx` (198), `verification-pages.test.tsx` (186), `knowledge-operations.test.tsx` (165).

Coverage by domain:

| Domain | Specs |
|---|---|
| Chat / assistant | `assistant.test.tsx`, `chat-citation.test.tsx`, `chat-privacy.test.tsx`, `chat-stream.test.tsx`, `ncp-chat-contract.test.tsx` |
| SOP review | `sop-review.test.tsx`, `sop-metadata.test.tsx`, `sop-progress.test.tsx` |
| Operator | `operator.test.tsx`, `operator-followup.test.tsx`, `engineering-console.test.tsx` |
| Human | `human.test.tsx`, `attestation.test.tsx`, `acceptance.test.ts` |
| Knowledge | `knowledge-operations.test.tsx`, `knowledge-proxy.test.ts`, `knowledge-upload.test.ts` |
| Routing / UI | `ui-routing.test.tsx`, `ui.test.tsx`, `settings.test.tsx`, `runtime-readiness.test.tsx` |
| API / infra | `api.test.ts`, `api-health.test.ts`, `chat-proxy.integration.test.ts`, `snapshot-file.test.ts`, `inspection-preview.test.tsx`, `hermes-connection.test.tsx` |

Stale: `assistant.test.tsx.bak-20261010-200432` (142 lines), `ui-routing.test.tsx.bak` (46 lines) — **ARCHIVE**.

Measured pass/fail counts: `TEST_RUNTIME_AUDIT.md`.

### 5.2 End-to-end — Playwright (12 specs, 914 lines)

| Spec | Lines | Exercises |
|---|---:|---|
| `operator-followup.spec.ts` | 178 | Multi-turn context preservation |
| `attestation.spec.ts` | 147 | Human attestation flow |
| `docling-live.spec.ts` | 105 | Live Docling ingestion |
| `chat-settings.spec.ts` | 75 | Chat + settings |
| `main-chat-docling-live.spec.ts` | 62 | Chat → Docling |
| `operator-design.spec.ts` | 58 | Operator layout contract |
| `knowledge-human-live.spec.ts` | 53 | Knowledge → human review |
| `control-plane.spec.ts` | 47 | Control-plane contract |
| `human.spec.ts` | 47 | Human surface |
| `operator-contract.spec.ts` | 47 | Operator contract |
| `knowledge-duplicate-live.spec.ts` | 43 | Duplicate detection |
| `review-execution.spec.ts` | 42 | Review → execution gate |

Five specs are marked `-live`, meaning they drive the real backend and real model rather than a fixture. Those are the browser-level evidence the contract asks for.

---

## 6. Accessibility and layout

| Control | Evidence |
|---|---|
| `role="region"` + `aria-label` on problem-report block | `sop-review.tsx:175` |
| Disabled-state gating on review buttons | `sop-review.tsx:152` — blocks approval while `busy`, while `content_ok`, and while a PDF extraction is not `COMPLETE` |
| Keyboard-reachable navigation | `ui.tsx` `navigation` export + `sidebar.tsx` |
| Focus management | `@testing-library/react` user-event based tests |

This audit did not run an automated axe/Lighthouse pass — **not attempted, not claimed**.

---

## 7. Findings

| # | Finding | Severity | Action |
|---|---|---|---|
| F1 | `TS2322` blocked all builds | **Critical** | **FIXED** — optional `onChanged` prop |
| F2 | esbuild could not write `%TEMP%` | **Critical (env)** | **WORKED AROUND** — `TMP`/`TEMP`/`TMPDIR` → `.tmp-build` |
| F3 | Frontend absent from Docker image | High | **FIXED** — `COPY control-plane/dist` restored, verified in image |
| F4 | `human.tsx.bak` (30.8 kB) ships in `src\` | Low | ARCHIVE manifest |
| F5 | 2 stale `.bak` test files | Low | ARCHIVE manifest |
| F6 | `sop-review.tsx` has its own fetch path | Low | Recorded, not changed |
| F7 | Main bundle 689.90 kB > 500 kB advisory | Low | Recorded; code-splitting is an optimisation, not a defect |
| F8 | No automated accessibility scan | — | Not attempted |

---

## 8. Verdict

| Criterion | Result |
|---|---|
| Type check passes | **PASS** — exit 0 |
| Production build passes | **PASS** — exit 0, 446 modules |
| Build artefact reproducible | **PASS** — with documented env |
| Frontend served in Docker | **PASS** — verified inside image |
| Typed API client | **PASS** — `api.ts` + `schemas.ts` |
| Routing defined | **PASS** — TanStack Router |
| Unit tests exist | **PASS** — 30 files |
| Browser E2E tests exist | **PASS** — 12 specs, 5 live |
| No stale code in `src\` | **FAIL** — `human.tsx.bak` |
| Bundle within advisory budget | **FAIL** — 689.90 kB |

**Frontend status: ACTIVE.** The build is repaired and the image now ships the UI. Two residue files and one bundle-size advisory remain recorded rather than fixed.
