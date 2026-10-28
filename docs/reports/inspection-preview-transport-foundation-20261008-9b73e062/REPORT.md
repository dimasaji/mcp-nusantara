# Inspection Preview Transport Foundation — Contract Stop Report

Date: 2026-10-08. **Final status: BLOCKED — AUTHENTICATION_DELIVERY_GAP.** Discovery only completed. Endpoint/source implementation and tests were not started because the governing contract explicitly requires stopping at the observed credential-delivery gap.

## Repository and authority

Root: `C:\Users\dmaza\mcp-starter`. Branch: `codex/fullroot-control-20261007`. HEAD: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. Target profile selected by human: **NORMAL**. Current live profile was not observed.

Requested `docs/Inspection-Preview-Transport-Foundation.md` is absent. Exact named contract found and read at `docs/commands/Inspection-Preview-Transport-Foundation.md`. It authorizes minimum backend preview transport but makes credential-delivery and CORS gaps mandatory STOP conditions.

Contract §4 explicitly states:

> If the existing frontend cannot safely receive/use the existing authentication credential without an additional credential-delivery design: STOP / REPORT GAP / DO NOT INVENT A SECRET DELIVERY MECHANISM.

Contract §15 explicitly states:

> If secure delivery of the existing credential cannot be established within current architecture: STOP … AUTHENTICATION_DELIVERY_GAP.

Contract §16 also prohibits changing `app/main.py` CORS/composition to bypass the transport boundary. These are direct contract requirements, not a new approval rule or an R2-assurance requirement.

## Current disk-source evidence

`SOURCE_EVIDENCE.json` records observed file/line/source references. Source and graph inspection established:

1. `app/security/auth.py::require_admin` requires a nonempty existing `NUSANTARA_ADMIN_TOKEN` and a matching supplied token, checked using `hmac.compare_digest`. Existing `/v2/dev` receives `x_admin_token` and calls `_require_admin`. Neither the token nor environment value was read.
2. `control-plane/src/api.ts` provides snapshot and PENDING intention requests with `credentials:'omit'`; it supplies no admin header or authenticated session mechanism. Bounded searches of current frontend source/security modules found no existing credential-delivery flow for this operation.
3. `control-plane/src/human.tsx` session state is browser review state, not server authentication. Existing ATTESTATION intention is explicitly untrusted and does not authenticate an admin. Neither may be repurposed as authority.
4. `control-plane/vite.config.ts` proxies `/v1/control-plane` and `/health`, not a v2 preview route; there is no existing credential-injecting preview proxy in that source configuration.
5. `app/main.py` CORS declarations do not include the Control Plane's configured 5173 origin. A direct cross-origin browser path is therefore not established by current configuration. NORMAL mounts v2 conditionally; ATTESTATION/evidence-only composition is preserved.
6. Existing `/v2/dev` is a general handler with a provider callback. A dedicated server-enforced preview boundary remains necessary, but backend route creation alone would not establish the authenticated UI-to-NORMAL path required by this contract.

These are **current disk/source observations only**. External deployment proxies, credentials, active listeners or live origins were not inspected and are not assumed. Absence of an established credential-delivery design in the inspected architecture is sufficient for the contract's hard stop; it is not proof that no external deployment arrangement could ever exist.

## Result and changes

Proposed endpoint remains `POST /v2/dev/inspection-preview`; it was **not created**. Authentication method to reuse remains existing admin header/token verification; it was **not bypassed or activated**. No frontend credential input/storage, new secret, token hard-coding, session authentication, proxy injection, cookie system, CORS relaxation or composition change was invented.

Before/after application behavior: unchanged. Existing DevCore planner, source inspection, find/list, grounding, modification refusal, fallback and audit remain inherited. `/v1/chat`, `/v2/chat`, `/v2/dev`, ATTESTATION, evidence-only composition, provider/model, RAG/database/index/WAL/SHM, runtime identity, authorization policy and gate records were not modified.

Only this fresh report directory was created: `REPORT.md`, `SOURCE_EVIDENCE.json`, `FILES_BEFORE.json`, `PRESERVATION.json`, `GIT_BEFORE.txt`, `GIT_AFTER.txt`, `GIT_DELTA.json`. Preservation evidence compares 390 explicitly inventoried existing non-protected files and must report zero changes. Protected-state content was not opened or hashed. Staging empty before/after; inherited dirty worktree preserved.

## Commands and validation actually performed

- `Get-Content -LiteralPath`: governing contract and current frontend client/configuration, admin auth, v2 handler and NORMAL composition source. No application/provider module import.
- `rg --files docs/commands -g '*Inspection*' -g '*Transport*'`: located exact contract after requested location was absent.
- `rg -n 'x.admin.token|NUSANTARA_ADMIN_TOKEN|Authorization|credentials|localStorage|sessionStorage|cookie|proxy' control-plane/src control-plane/vite.config.ts app/security app/api/control_plane.py`: bounded static mechanism search; did not inspect secret values.
- Graph navigation before any possible changes:

```powershell
& 'C:\Users\dmaza\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe' -B -m graphify query 'Control Plane frontend admin authentication require_admin proxy credential session' --budget 1000
```

Graph query was truncated and used only for navigation; direct source supplied decisive evidence. No AST update: no application source changed.

- Existing Git executable: `rev-parse --show-toplevel`, `branch --show-current`, `rev-parse HEAD`, `diff --cached --name-status`, `status --porcelain=v1 -uall`. Read-only state observation only.
- PowerShell `Get-FileHash -LiteralPath … -Algorithm SHA256`: bounded non-protected source/configuration/contract inventory only. No protected database/data digests.

Focused backend tests: **0 run**. Transport/authentication/negative tests: **0 run**. DevCore regression: **0 run**. None claimed PASS. Prior DevCore tests remain historical evidence only. Runtime/provider/database mutation guards were not exercised by a test runner; no relevant invocation or request was attempted. No live HTTP, browser, restart, deployment, generation, health/list-model request, DB/RAG operation, IPC/ARM/EXECUTE/permit or dependency installation occurred.

Git warned about five inaccessible inherited report directories; permissions were not changed. Observed Git state preservation is bounded by those access limits. No reset/clean/checkout/restore/stash/stage/commit occurred.

## Required next human decision

Authorize a separate **credential-delivery/transport design-only** task, or provide an already approved existing server-side authenticated deployment mechanism for inspection. It must define how NORMAL Control Plane requests use the existing admin authentication while keeping the admin credential out of frontend source/storage and preserving fail-closed access. It must also explicitly define the communication path under existing origin/proxy constraints. Any required CORS/composition change needs separate authorization under §16.

No design option is implemented, selected automatically or treated as a live grant. After that decision establishes a supported path, the backend preview foundation can resume under its applicable authorization. This report does not authorize that next task.

## Final statuses

- Transport foundation: **BLOCKED — AUTHENTICATION_DELIVERY_GAP**.
- Preview-only endpoint: **NOT_IMPLEMENTED**.
- SOURCE-LEVEL preview transport verification: **NOT_VERIFIED**.
- LIVE LOADED STATE / live service verification: **NOT_VERIFIED**.
- Provider/model and database: unchanged; not invoked/accessed.
- ATTESTATION and evidence-only composition: unchanged.
- R2-A14: BLOCKED / KNOWN LIMITATION.
- Runtime Identity: NOT_VERIFIED.
- ACTIVE_PROCESS_BUILD: NOT_DIRECTLY_VERIFIED.
- R2-A8: BLOCKED / NOT_VERIFIED.
- R2-A9: HOLD.

**STOP as explicitly required by §§4/15/16/21.** No UI integration, credential-delivery workaround, backend implementation, live action, gate promotion or further phase follows this report.
