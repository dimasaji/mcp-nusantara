# Control Plane inspection_preview — Discovery Closure

Date: 2026-10-08. **Final status: BLOCKED / OUT-OF-SCOPE.** Discovery completed; UI implementation, focused UI tests and regression were NOT RUN. No acceptance PASS is claimed. Only this new report/evidence directory was created.

## Contract and repository

Requested `docs/NUSANTARA-CONTROL-PLANE.md` does not exist. Filename search located the exact contract at `docs/commands/NUSANTARA-CONTROL-PLANE.md`; it was read before any implementation. SHA256: `7067645c96f532fb8caeb666fb3eb3b576f6c962be115a5773f22b6e18086bff`.

Root: `C:\Users\dmaza\mcp-starter`. Branch: `codex/fullroot-control-20261007`. HEAD: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. Staging empty; inherited dirty worktree preserved. No reset, clean, checkout, restore, staging or commit. File enumeration/Git warned about inaccessible inherited temporary/report directories; no permission repair was attempted. Enumeration is bounded, not exhaustive.

Mandatory stop comes directly from contract §14:

> Jika perubahan API benar-benar diperlukan: STOP / REPORT GAP / DO NOT IMPLEMENT

And §24:

> Jika ditemukan kebutuhan di luar scope: STOP. Jangan memperluas authority.

No new approval is inferred from discovering a solution. A separate human decision is needed before changing API/request execution semantics, authentication delivery, or runtime composition.

## Current observed source

| Area | Observed fact | Consequence |
| --- | --- | --- |
| Navigation | `control-plane/src/router.tsx` retains SYSTEM/EVIDENCE/TEST/REVIEW/DECISION and existing engineering pages | Existing navigation can accommodate a later additive UI area; no navigation rewrite is necessary |
| Data client | `control-plane/src/api.ts` has snapshot GET and PENDING-intention POST; no DevCore client | Current Control Plane data path does not deliver inspection_preview |
| Snapshot schemas | `control-plane/src/schemas.ts` defines NORMAL/ATTESTATION evidence and PENDING intention; no preview request path | Existing snapshot/intention cannot be treated as a Developer Engine goal interface |
| Frontend transport | `control-plane/vite.config.ts` proxies `/v1/control-plane` and `/health`, not `/v2` | Relative `/v2/dev` requests have no existing development proxy to the application |
| Cross-origin transport | `app/main.py` CORS source allows localhost/127.0.0.1 ports 3000 and 8000; no 5173 origin | Direct cross-origin access from the existing Control Plane 5173 is not established by current configuration |
| Existing DevCore API | `POST /v2/dev` in `app/api/v2_routes.py` accepts `session_id` and general `user_input` only | There is no preview-only request discriminator or terminal preview guarantee for arbitrary goal text |
| Authentication | `/v2/dev` calls `_require_admin`; `app/security/auth.py` requires an existing server token and matching supplied header | The current credential-omitting UI client does not supply this authenticated path. No secret/environment value was read |
| Runtime composition | `app/main.py` mounts v2 only outside ATTESTATION/evidence-only composition | `/v2/dev` is not an existing endpoint in those compositions. Current live profile was not observed or assumed |
| Provider path | Existing `/v2/dev` constructs OllamaProvider and passes a generation callback to DevCore | Supported preview goals return before generation, but the general endpoint is not a preview-only surface |
| DevCore semantics | Preview branch returns early; explicit source input still uses `_resolve_reads` and may call `_analyze`/`generate` | Arbitrary text such as `Baca app/main.py` can enter a model-analysis path; merely sending text as “engineering goal” does not enforce preview-only behavior |

These are current disk/source facts, not claims about an active listener or loaded code. `STATIC_EVIDENCE.json` contains actual source line references and AST-derived DevRequest fields/endpoint call names. Neither the application nor backend routes/providers were imported or executed.

## Blocker and minimum required decision

The desired UI accepts human text and must consume a genuine DevCore preview without provider/runtime/protected-state consequences. A blind call to the current general `/v2/dev` endpoint cannot establish that boundary for all accepted input. Client-side replication of the planner or a mock fallback would violate the requirement to use actual DevCore data and would not enforce the backend boundary. Using the snapshot or ATTESTATION intention as a goal endpoint would change their semantics.

Therefore the minimum safe end-to-end integration needs a separately approved, explicit transport/authentication delivery choice and server-enforced preview-only request behavior in the intended runtime profile. The existing API has no such request option. Implementing it would change the public request contract or backend behavior outside this UI-only scope; enabling it in ATTESTATION would also change composition boundaries. None was done.

**Required human decision:** define the intended NORMAL versus ATTESTATION profile and authorize a narrowly scoped, server-enforced preview-only data path through existing DevCore, with explicit reuse of existing authentication and UI transport. Preserve all authority/protected-state restrictions. Do not weaken admin authentication, store/provision a new secret, add a new authority, mount NORMAL routes into ATTESTATION, or authorize live invocation as an incidental UI fix. Exact implementation files depend on that decision; likely inspection points are existing `app/api/v2_routes.py` request/handler and `control-plane/src/api.ts`/frontend transport. `app/main.py` composition/CORS remains unchanged and is not implicitly authorized for modification.

This is an implementation boundary, not an R2 identity assurance requirement. Runtime Identity NOT_VERIFIED and the accepted R2-A14 limitation were not used as reasons to block ordinary UI engineering.

## Executed commands and evidence

Read-only discovery used `Get-Content -LiteralPath` for the governing contract, frontend router/client/human components/schemas/configuration/tests and backend handler/auth/composition. `rg --files` located the moved contract; `rg -n` mapped fetch/provider/DevCore/profile references. File search exposed inherited access warnings; no protected data content was read. Git commands were limited to root, branch, HEAD, staging and porcelain status observation.

Graph navigation only:

```powershell
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify query 'Control Plane DevCore API client developer goal ReviewPage' --budget 1200
```

Graph query returned relevant DevCore/UI/client/schema relationships and explicit truncation. Source inspection supplied the decisive facts. No graph update was needed: no application source changed, graph files were preserved.

Bounded report-owned diagnostic command:

```powershell
& '.\.venv\Scripts\python.exe' -B 'docs\reports\control-plane-inspection-integration-20261008-5ab18f90\static_evidence.py' *> 'docs\reports\control-plane-inspection-integration-20261008-5ab18f90\STATIC_OUTPUT.txt'
```

Actual output: eight static observations confirmed; 389 monitored existing non-protected files unchanged; UI_INTEGRATION BLOCKED / OUT-OF-SCOPE; live_observation NOT_PERFORMED. Exit 0 means only the source diagnostic completed. It is not a UI test PASS, browser result, API test, runtime attestation or provider proof.

Focused UI tests: **0 run**. UI regressions: **0 run**. Browser tests/screenshots: **0 run**. Deterministic UI acceptance evidence: **NOT_AVAILABLE**, because implementation stopped before modification. No existing assertions were altered or weakened.

## Changes, preservation and limitations

Files created only under this fresh directory: `REPORT.md`, `static_evidence.py`, `STATIC_EVIDENCE.json`, `STATIC_OUTPUT.txt`, `FILES_BEFORE.json`, `PRESERVATION.json`, `GIT_BEFORE.txt`, `GIT_AFTER.txt`, `GIT_DELTA.json`. Existing application/UI/test/configuration files changed: **none**. Protected database/RAG/WAL/SHM content was not opened or hashed. No secret/token or environment credential was inspected.

`PRESERVATION.json` verifies 389 explicitly inventoried existing non-protected paths unchanged, including prior DevCore implementation/test and graph JSON/report. This is a bounded worktree-preservation check, not a full-build inventory. Git delta must contain only this new report directory, with no inherited entry removed. No dependencies installed, no service/browser started, no HTTP/provider generation/health/list-model operation, permit/intention/approval operation, runtime lifecycle or external consequential operation occurred.

Current live service loading/profile/API/provider status remains NOT_VERIFIED or NOT_OBSERVED; no request was made to resolve it. Existing historic UI/DevCore test results are not counted as fresh execution evidence. UI integration remains NOT_IMPLEMENTED.

Preserve:

- R2-A14: BLOCKED / KNOWN LIMITATION.
- Runtime Identity: NOT_VERIFIED.
- ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED.
- R2-A8: BLOCKED / NOT_VERIFIED.
- R2-A9: HOLD.

**STOP at the contract's API/scope boundary.** No workaround, source modification, implementation phase, live activation or status promotion follows this report.
