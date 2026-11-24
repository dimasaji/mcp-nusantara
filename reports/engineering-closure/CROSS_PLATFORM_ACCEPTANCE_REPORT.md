# WP-02 — Cross-Platform Acceptance Report

- Commit SHA baseline: `937118a4bfd46b2bf4f5d4d2c0f60d1a6c5e19a8` (WP-01)
- Environment: Instabox Linux VPS, Python 3.13.5, Node/Vite frontend build, isolated worktree `/data/workspace/nus-v1-engineering-closure-20261124/worktrees/closure`
- Expected result: Linux backend/frontend build and runtime PASS; Windows-only tests separated from cross-platform tests without bypassing security controls.
- Actual result: Linux startup/build/auth PASS; 37 Windows-native IPC cases explicitly skipped as platform-dependent; 49 related auth/control-plane tests executed locally with 48 passing and one historical-artifact failure.
- Final status: **PARTIAL** — Linux portability PASS; Windows compatibility pending valid PC/CI Windows verification.

## Commands and evidence

| Command | Exit | Expected | Actual | Status | Evidence |
|---|---:|---|---|---|---|
| `git diff --check` | 0 | clean patch | clean | PASS | `evidence/WP-02/commands.tsv` |
| `python -m compileall -q backend/app/security/local_operator.py backend/app/approval/runtime_authorization.py` | 0 | syntax OK | OK | PASS | `evidence/WP-02/compileall.out` |
| inline uvicorn startup on `127.0.0.1:18220` | 0 | health 200 | health 200, readyz 200 | PASS | `evidence/WP-02/backend_startup_check.out` |
| `npm --prefix frontend ci --no-audit --no-fund` | 0 | deps installed | OK | PASS | `evidence/WP-02/frontend_ci.out` |
| `npm --prefix frontend run build` | 0 | production build | 451 modules, 4 assets | PASS | `evidence/WP-02/frontend_build.out` |
| pytest admin-token source | 0 | 3 passed | 3 passed | PASS | `evidence/WP-02/auth_admin.out` |
| pytest runtime auth/attestation/portability subset | 0 | 17 passed | 17 passed | PASS | `evidence/WP-02/auth_runtime.out` |
| pytest `test_v1_operator_control.py` | 0 | all passed | 26 passed | PASS | `evidence/WP-02/operator_control.out` |
| pytest auth/control-plane/runtime-attestation full | 1 | no Linux platform failures | 48 passed, 37 skipped, 1 missing-artifact failure | PARTIAL | `evidence/WP-02/authorization_full.out` |
| pytest control-plane readonly with `PYTHONPATH=backend` | 1 | no platform failures | 22 passed, 1 missing-artifact failure | PARTIAL | `evidence/WP-02/control_plane_readonly_pythonpath.out` |
| `ruff check` on changed files | 1 | no lint findings | pre-existing repository lint findings remain | FAIL / tracked | `evidence/WP-02/ruff_changed.out` |
| `python -m mypy` on changed backend files | 1 | clean typing | pre-existing typing findings remain | FAIL / tracked | `evidence/WP-02/mypy_changed.out` |

## Root cause

- 69 baseline Windows-bound failures originated from `backend/app/security/local_operator.py:117-118`, which intentionally rejects non-Windows execution of native actor proof, named pipes and process impersonation.
- `backend/app/approval/runtime_authorization.py:124` used the Windows-only `Windows().process_start()` for non-authoritative process-start binding metadata, causing otherwise cross-platform authorization tests to fail before reaching their real assertions.
- `tests/test_runtime_authorization.py::fixture` and `tests/test_control_plane_attestation_binding.py::isolated` used a live `Windows().current_actor()` policy even where tests only required a test policy object.
- Missing historical artifacts (`control-plane/evidence-sources.json`, `docs/reports/r2-a7-runtime-attestation-20261008/main.py.before`) are legacy fixture gaps, not cross-platform defects; they remain for WP-03.

## Changes made

- `backend/app/security/local_operator.py`
  - Added module-level `process_start(pid)` with Windows native path and Linux `/proc/<pid>/stat` + `/proc/stat btime` path.
  - Windows actor proof, `VerifiedPeer`, named pipe, SDDL, impersonation and `Windows.__init__` guard were not changed.
- `backend/app/approval/runtime_authorization.py`
  - `_material()` now uses platform-neutral `process_start()` for process-start metadata only.
  - Peer type gates, code hash, digests, one-use authorization and live-lock behavior unchanged.
- `tests/test_runtime_authorization.py`
  - Test fixture uses a synthetic local policy on non-Windows; Windows path remains unchanged.
  - Added `windows_only` skipif to 35 cases that require native Windows IPC proof.
  - Preserved the two subprocess `PYTHONPATH` fixes from WP-01.
- `tests/test_control_plane_attestation_binding.py`
  - Added `windows_only` skipif to the two live-lock cases requiring `Windows().current_actor()`.
  - The 28 browser/origin/JSON/queue cases and guarded-composition test remain active on Linux.

## Classification

- `APPLICATION_BUG`: Windows-only process-start metadata call in `_material()` is removed for Linux.
- `PLATFORM_DEPENDENCY`: 37 native IPC cases require Windows PC/CI validation; skipped on Linux with explicit reason `WINDOWS_NATIVE_IPC_REQUIRED`.
- `LEGACY_ARTIFACT`: 2 remaining failures from missing archived evidence/fixture files; transferred to WP-03.
- No authorization, Human Approval or Fullroot Control was disabled. No Linux actor-identity fallback was added. No test assertion was deleted.

## Modified files

- `backend/app/security/local_operator.py`
- `backend/app/approval/runtime_authorization.py`
- `tests/test_runtime_authorization.py`
- `tests/test_control_plane_attestation_binding.py`
- `reports/engineering-closure/CROSS_PLATFORM_ACCEPTANCE_REPORT.md`
- `reports/engineering-closure/evidence/WP-02/*`

## Remaining blocker

- Windows PC or CI Windows validation of the 37 skipped native IPC cases remains required. Linux results do not substitute PC attestation.
- Two historical-artifact failures remain and are assigned to WP-03.
- Ruff and mypy report existing repository-wide findings on changed files; no semantic lint/type rewrite was attempted in WP-02.

## Rollback procedure

- Revert the four source/test files to WP-01 baseline `937118a4bfd46b2bf4f5d4d2c0f60d1a6c5e19a8`.
- After WP-02 commit, use `git revert <wp02-commit>` on the engineering branch.
- No runtime service, database, volume, model or production port was changed by WP-02.
