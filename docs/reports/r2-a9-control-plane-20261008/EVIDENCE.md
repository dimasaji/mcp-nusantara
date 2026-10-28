# Evidence

Evidence type: SOURCE_INSPECTION_AND_DOCUMENTATION. Scope: R2-A9 preflight. Date: 2026-10-08. Status: BLOCKED. Provenance: actual contract, inspected repository source, read-only Git metadata and existing R2-A8 result file.

`SOURCE_BEFORE.json` / `SOURCE_AFTER.json` bind inspected source/test/style/contract bytes to SHA-256 and capture UTC time. Both were captured after the initial Markdown report creation, around documentation verification. `SOURCE_COMPARISON.json` records equality over that interval; this is not a pre-task source baseline, loaded-code proof or active application build. Tool action history contains only read operations and owned report writes. `GIT_INSPECTION.txt` records the dirty worktree including these new reports; five inherited reports directories were inaccessible to Git, so inventory coverage is incomplete. No repair was attempted.

Primary source references:

- Contract §§23–28, 34, 40–42.
- UI router/human/acceptance/api/schemas/styles and existing test definitions.
- Control Plane endpoint and projection; security auth; approval audit/queue; v2 owner and decision route; developer approval controller.
- Runtime correlation grant and runtime verification installation; app.main profile composition.
- Prior `docs/reports/r2-a8-remediation-20261008/PROFILE_RESULT.json` (historical isolated evidence).

No new runtime_instance_id, PID, scoped_loaded_code, invocation_id, actual_model or live response observation was collected. Those fields are NOT_AVAILABLE for this task. Historical PID 32796 is not current attestation. No raw prompt/output, credentials or internal permit was collected.
