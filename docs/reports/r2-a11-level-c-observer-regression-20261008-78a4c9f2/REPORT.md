# R2-A11 Level C — bounded process-observer regression

Date: 2026-10-08. **PASS_SCOPED — existing correction confirmed; no application source change required. STOP.**

## Authorization and discovery

The latest human decision authorizes only minimum fail-closed handling for process observers returning `{}` or `None`, related isolated regression and evidence review. No Control Plane/UI/E2E, provider/model, protected state, gate, authorization record or runtime activation work is included.

Inspection found the previously authorized Level C correction already present in `app/api/runtime_verification.py::VerificationController.receipt_assessment`. Observer acquisition, dictionary access, runtime-instance attribute access and `assess_receipt` arguments are inside the existing try/except boundary. `{}` raises KeyError and `None` raises TypeError internally; both are caught and produce the existing bounded NOT_VERIFIED response. No extra implementation gap was reproduced, so application source was preserved.

The historical Level C report `docs/reports/r2-a11-level-c-20261008-7d1ea04b/REPORT.md` and unchanged B2 acceptance tests were inspected. Historical 62-pass results are references only, not results of this task. No full-suite/human/Control Plane/browser tests were rerun.

## Minimum new regression evidence

Added only report-owned `test_observer_regression.py` and `isolated_runner.py`, plus evidence in this fresh directory. The new two-case regression strengthens the original acceptance check by asserting the complete bounded response, unchanged stored receipt/observation object identity, DISARMED authorization, zero dispatch and no mock transport calls. It uses the existing B2 no-dispatch fixture; synthetic receipt labels are never represented as genuine provider evidence.

The runner executes precisely these four cases:

1. Original B2 `test_incomplete_process_observer_fails_closed[result0]` — `{}`.
2. Original B2 `test_incomplete_process_observer_fails_closed[None]` — `None`.
3. New `test_incomplete_observer_is_bounded_without_mutating_receipt[empty_mapping]`.
4. New `test_incomplete_observer_is_bounded_without_mutating_receipt[none]`.

The original B2 test file and assertions were not modified. Report helpers block SQLite/protected-file access, real HTTP/socket connections/listeners, provider generation/health/list-model, grant/reserve/dispatch, native authorization/IPC owners, knowledge/RAG and Control Plane/v2 imports. No guarded operation was attempted; `GUARDS.json` has an empty violations list. These are scoped Python-level guards, not an exhaustive OS activity monitor.

## New execution results and command

Interpreter verified before execution: `C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe`; Python **3.13.15**, pytest **9.1.1**. Existing environment only; no dependency installation. Bytecode and automatic pytest plugins disabled; no pytest cache; new report-owned basetemp/XML.

From repository root:

```powershell
& .venv/Scripts/python.exe -B docs/reports/r2-a11-level-c-observer-regression-20261008-78a4c9f2/isolated_runner.py
```

Output captured to `TEST_RUN.log`. **4 passed, 0 failed, 0 errors, 0 skipped, 0 deselected, 0 warnings; 0.20 seconds; exit 0.** Other B2/suite cases were not collected, rather than being reported as passed. One focused run only, no retries or unrelated regression.

`RESULTS.xml` records actual results; `SELECTED_IDS.json` contains exact expanded IDs. Both observer forms returned:

```json
{"status":"NOT_VERIFIED","correlation_valid":false,"reason":"CURRENT_CONTEXT_UNAVAILABLE","application_response_sent":false,"external_client_observed":false}
```

No raw exception, sensitive process details, authority or fabricated PASS is returned. Provider/response delivery evidence is not inferred from this fallback. Tests exercise storage/assessment only, never the invoke/authorization/provider lifecycle.

## Diff and preservation

Root `C:/Users/dmaza/mcp-starter`; branch `codex/fullroot-control-20261007`; HEAD `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. Staging remained empty and the 26 inherited tracked modifications remained present. `GIT_COMPARISON.json` shows zero accessible inherited-status changes outside this new report directory. No Git reset/cleanup/staging/commit occurred.

`FILES_BEFORE.json` / `FILES_COMPARISON.json` show **383 monitored existing files unchanged**, including application/test/config source, ATTESTATION E2E and original B2 acceptance evidence. Runtime verification source remains SHA-256 `e2dec6bc0ae0e8b6eaa2ab247834f0920a2014c083180a50de2f4a0484737069`, matching the earlier Level C corrected source. No source diff was produced because the required correction was already present. Only new report-owned regression/guard/evidence files were created; `ARTIFACT_MANIFEST.json` inventories them.

Five inherited inaccessible report directories remain Git enumeration warnings; their files were not opened or repaired. The sandbox also denied recursive enumeration of new pytest-tmp after the elevated test run; artifact inventory therefore covers top-level report/test evidence files, not temporary fixture-directory contents. No permissions were changed or temporary files removed. No protected-data digest was used. No existing application/test code was changed and no graph update was performed; discovery used a read-only graph query.

## Limitations, unchanged statuses and stop

This proves only controlled receipt assessment for the two authorized malformed process-observer returns. It does not assess new behavior in invoke(), broader receipt failure modes, real provider receipts, live process/build binding, response delivery, or production safety. Historical process/disk snapshot mismatch remains unresolved. No live requests, native actions, service loading/restart, provider/model operation, database/WAL/SHM/RAG/index access, UI/E2E change or R2-A11 scope expansion occurred.

Full Runtime Identity: **NOT_VERIFIED**. ACTIVE_PROCESS_BUILD: **NOT_DIRECTLY_VERIFIED**. Live provider/model correlation: **NOT_VERIFIED**. R2-A8: **BLOCKED / NOT_VERIFIED**. R2-A9: **HOLD**. No gate, authorization record or status was modified or promoted.

**STOP after focused tests and this evidence/diff review. No automatic activation or next phase.**
