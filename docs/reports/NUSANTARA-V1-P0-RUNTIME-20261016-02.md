# Nusantara V1 P0 Runtime Evidence — 16 October 2026, run 02

## Decision

**HOLD.** The active backend authenticates requests and reaches the real Hermes ACP probe, but Hermes does not complete `initialize`. The safe backend reason is `HERMES_INSTALL_STATE_NOT_WRITABLE`. Runtime identity remains `NOT_VERIFIED`; no ACL or permission change was made.

## Active runtime evidence

- `http://127.0.0.1:8000/health`: HTTP 200, build ID `sha256:d00c072d735bc658357546ab46d632f9c74f22e491c5315f92d7d8e09bbf1578`.
- `http://127.0.0.1:8000/v1/control-plane/model-status`: HTTP 200, process ID `12820`, source build ID matches health, provider `openrouter`; availability and runtime status remain `NOT_VERIFIED`.
- Authenticated GET `/v1/control-plane/hermes/connection` on 8000: HTTP 200, initially `NOT_CHECKED`.
- Authenticated POST to the same route on 8000: HTTP 200, `UNAVAILABLE`, reason `HERMES_INSTALL_STATE_NOT_WRITABLE`, scope `ACP_INITIALIZE_ONLY`, `task_execution_enabled=false`, `runtime_identity=NOT_VERIFIED`.
- Authenticated GET through `http://127.0.0.1:5180/v1/control-plane/hermes/connection`: HTTP 200 and returned the same backend probe state. Model status through 5180 reported the same process ID and source build ID.
- Invalid test token: HTTP 403 on both 8000 and 5180. The configured token was read into process memory for these checks and was not printed or changed.
- `http://127.0.0.1:5180/`: HTTP 200 with HTML. No browser surface was available in this session, so visual/UI interaction remains unverified.
- Listener check: 8000 PID `12820`, 5180 PID `23212`, 8765 PID `3904`. Port 8765 remained listening with the same PID before and after the backend restart.

## Test evidence

- Earlier isolated ACP tests: 5 passed; these exercise the stdio handshake contract and safe error mapping, not Hermes runtime connectivity.
- Earlier frontend suite: 139 passed; targeted connection/workspace/proxy group: 21 passed; TypeScript check and Vite build passed. Existing evidence is recorded in `docs/reports/NUSANTARA-HERMES-ACP-CONNECTION-20261016.md` and `artifacts/knowledge-upload-entry/`.
- Read-only code review: standards review found no material issue in the scoped implementation. Spec review confirms the real runtime handshake and runtime identity gates remain HOLD. Existing backend tests do not cover the full FastAPI route/auth/boundary chain; this run's live HTTP checks cover valid and invalid tokens, POST initialize, and the 5180 proxy, but the browser boundary remains covered only by the component test.
- Re-running Python tests in this session was blocked because the virtualenv's base Python at `C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe` returned `Access is denied`. The frontend test command was unavailable because `npm` was not on this session's PATH. No dependency or tool was installed.
- Follow-up identity check: the automation shell reports `DESKTOP-GJHS3LR\codexsandboxoffline`; Windows denied `Get-Process -IncludeUserName` for PID `12820`, including the elevated read attempt. Treat this as the shell identity only; the backend process owner is still unverified. The accessible global Python is 3.13.13 but has no `pytest`, so it cannot replace the project virtualenv for tests.
- No model request, paid OpenRouter call, or agent task was made.

## Remaining blocker and safe next step

The Hermes installation is inaccessible or not writable to the identity used by the current backend process. This session cannot verify that process identity with the available Windows permissions. The next step requires the owner to run the existing startup script under the Windows account that owns the Hermes installation, or explicitly authorize a narrowly scoped permission change after reviewing the exact identity and target. Do not treat a successful API response as a connected Hermes runtime.

The backend restart used `scripts/Start-NusantaraV1.ps1 -Component backend` to load current source. No database, History, token, ACL, governance setting, or port 8765 process was changed. The API process remains healthy on port 8000, but P0 acceptance stays HOLD until a real handshake reports `CONNECTED` and runtime identity is verified.
