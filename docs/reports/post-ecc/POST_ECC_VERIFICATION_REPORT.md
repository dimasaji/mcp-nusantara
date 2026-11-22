# Post-ECC Verification Report

Contract: `NUS-V1-POST-ECC-001`

Date: 2026-11-22

Branch: `codex/ecc-fullstack-verification-20261122`

HEAD: `35efdd382405442a3aabe0e05b112f47a2ff3603`

## 1. Verification policy

- Only non-destructive, read-only or isolated-data checks were run.
- No ECC installation, full forensic re-audit, repository restructuring, or feature work was performed.
- Runtime checks used `NUSANTARA_DATA_DIR=/data/tmp/opencode/post_ecc_runtime_data` and `NUSANTARA_KNOWLEDGE_DB=/data/tmp/opencode/post_ecc_runtime_data/knowledge/runtime.db`; production data was not used.
- `PASS` is reported only where the command exited successfully or the expected HTTP response was observed.
- `BLOCKED` and `NOT_RUN` are reported explicitly where the environment lacks required dependencies.

## 2. Verification matrix

| Area | Command / check | Exit or observed code | Result | Evidence | Notes |
|---|---|---:|---|---|---|
| Repository state | `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git remote -v` | 0 | PASS | `ECC_REPORT_DISCOVERY.md` | Clean except untracked duplicate checkout `mcp-nusantara/` |
| Report discovery | `find` + Git object lookup for ECC report variants | 0 | PASS | `ECC_REPORT_DISCOVERY.md` | Authenticated tracked report, blob `8d1049dc...` |
| Source reconciliation | `git diff --name-only 8b7f9b78..HEAD` | 0 | PASS | `ECC_FINDINGS_ANALYSIS.md` | Only 4 app files changed after audit, all RAG-related |
| Python dependency resolution | importlib metadata for `fastapi`, `uvicorn`, `pydantic`, `haystack-ai`, `pytest` | 0 | PASS | `/data/tmp/opencode/post_ecc_python_env.txt` | `fastapi=0.165.0`, `uvicorn=0.54.0`, `pydantic=2.14.4`, `haystack-ai=2.31.1`, `pytest=9.2.0` |
| Python import | `import app.main` | 0 | PASS | same as above | `IMPORT_OK=app.main` |
| Full Python regression | `.venv/bin/python -m pytest -q --tb=no` | 1 | FAIL | `/data/tmp/opencode/post_ecc_full_pytest.txt` | `93 failed, 1508 passed, 45 skipped, 1053 warnings, 30 errors` |
| Full regression delta | Compare FAILED/ERROR IDs with ECC baseline | 0 | PASS | `ECC_FINDINGS_ANALYSIS.md` | 5 fixed, 0 new |
| Targeted RAG/regression | `pytest` on effective profile, source recovery, contextual follow-up, selected-document contract | 0 | PASS | `/data/tmp/opencode/post_ecc_targeted_rag.txt` | `40 passed, 8 warnings` |
| RAG regression suite | `pytest` on 5 RAG-related test files | 1 | FAIL | `/data/tmp/opencode/post_ecc_rag_suite.txt` | `2 failed, 74 passed, 126 warnings`; both failures are baseline PF-19 |
| Synthetic RAG + secret gate | `pytest tests/test_synthetic_rag_fixture.py tests/v2/...::test_project_has_no_secrets` | 0 | PASS | `/data/tmp/opencode/post_ecc_synthetic_secret.txt` | `4 passed, 24 warnings` |
| Frontend dependency/tools | `control-plane/node_modules/.bin/vite` present and executable | 0 | PASS | command check | Vite `7.3.7` |
| Frontend test suite | `CI=1 npm test -- --reporter=basic` | 1 | FAIL | `/data/tmp/opencode/post_ecc_frontend_test.txt` | `2 failed files, 27 passed files; 4 failed tests, 217 passed tests` |
| Frontend retry test isolation | `npx vitest run ... -t 'keeps a failed upload selected...'` x3 | 0 | PASS | `/data/tmp/opencode/post_ecc_frontend_retry_1.txt` … `_3.txt` | Passed 3/3; full-suite failure is likely order/timing related |
| Frontend production build | `npm run build` | 0 | PASS | `/data/tmp/opencode/post_ecc_frontend_build.txt` | `tsc --noEmit && vite build` succeeded; chunk-size warning only |
| Backend runtime | Uvicorn `127.0.0.1:8100`, `GET /health`, `GET /v1/health` | 0 | PASS | `/data/tmp/opencode/post_ecc_runtime_status.txt`, backend log | Both HTTP `200` |
| Frontend runtime | Vite `127.0.0.1:5200`, `GET /` | 0 | PASS | same status file, frontend log | HTTP `200` |
| Proxy connectivity | `GET /health` through Vite to backend | 0 | PASS | `/data/tmp/opencode/post_ecc_backend_health.json`, `/data/tmp/opencode/post_ecc_frontend_proxy_health.json` | Identical body SHA-256 `b5f6c2ff...` |
| Static analysis | Ruff on 4 touched files | 1 | FAIL | `/data/tmp/opencode/post_ecc_ruff.txt` | 103 output lines; pre-existing debt, not blocking this analysis-only contract |
| Static analysis | Mypy on 4 touched files | 1 | FAIL | `/data/tmp/opencode/post_ecc_mypy.txt` | 130 output lines; pre-existing debt |
| Ollama API | `curl http://127.0.0.1:11434/api/tags` | non-zero, HTTP `000` | BLOCKED | `/data/tmp/opencode/post_ecc_ollama.json` | No Ollama binary/service on VPS |
| IndoBERT worker | `test -x nusantara-models/.venv/bin/python` | 1 | BLOCKED | command check | MISSING; HTTP Knowledge path cannot be verified |
| Graphify | `test -f graphify-out/graph.json`; `command -v graphify` | 1 | NOT_RUN | command check | Justified skip already recorded in ECC report |
| Windows PC acceptance | Windows attestation suite | — | NOT_RUN | PF-14 | Cannot execute `WINDOWS_REQUIRED` checks on Linux VPS |

## 3. Backend verification

Dependency resolution and application import succeeded. The backend health endpoints were verified with isolated data paths:

```text
backend_health_http=200
backend_v1_health_http=200
```

Backend runtime result: **PASS** for health only. This does not imply `/v1/chat` E2E success.

## 4. Frontend verification

Build result: **PASS**.

Full test result: **FAIL**:

```text
Test Files  2 failed | 27 passed (29)
Tests       4 failed | 217 passed (221)
```

Three failures are missing historical evidence files consumed by `engineering-console.test.tsx`. One failure is a retry-count assertion in `knowledge-operations.test.tsx`; it passed 3/3 when run in isolation. No `control-plane/` source changed between the ECC baseline commit and current HEAD, so this is classified as a test-stability issue, not a post-ECC code regression.

## 5. Knowledge and AI verification

Direct synthetic retrieval remains verifiable: 4 tests passed including `tests/test_synthetic_rag_fixture.py` and the secret gate.

HTTP knowledge and real chat generation are **BLOCKED**:

- IndoBERT worker path `nusantara-models/.venv/bin/python` is missing.
- Ollama API is unreachable and no `ollama` binary is present.

No large model was installed and no production database was modified.

## 6. Database and release evidence

- R2 owner acceptance record: MISSING.
- `REMAINING_GATES.json` checksum mismatch remains as recorded in the ECC report.
- Control-plane tests fail on missing archived evidence paths.
- Windows attestation cannot be executed on this VPS.

These are release-readiness blockers, not defects introduced by the RAG stabilization commits.

## 7. Runtime chain conclusion

| Link | Result |
|---|---|
| Frontend | PASS |
| Backend API health | PASS |
| Frontend → backend proxy | PASS |
| Knowledge/RAG direct fixture | PASS |
| Knowledge/RAG HTTP | BLOCKED |
| Database/release evidence | FAIL / OPEN |
| LLM provider | BLOCKED |

Overall runtime readiness: **PARTIAL**. Full V1 SOP chat E2E remains **NOT_RUN / BLOCKED**.

## 8. Evidence files

- `/data/tmp/opencode/post_ecc_full_pytest.txt`
- `/data/tmp/opencode/post_ecc_targeted_rag.txt`
- `/data/tmp/opencode/post_ecc_rag_suite.txt`
- `/data/tmp/opencode/post_ecc_synthetic_secret.txt`
- `/data/tmp/opencode/post_ecc_frontend_test.txt`
- `/data/tmp/opencode/post_ecc_frontend_build.txt`
- `/data/tmp/opencode/post_ecc_frontend_retry_1.txt`
- `/data/tmp/opencode/post_ecc_frontend_retry_2.txt`
- `/data/tmp/opencode/post_ecc_frontend_retry_3.txt`
- `/data/tmp/opencode/post_ecc_runtime_status.txt`
- `/data/tmp/opencode/post_ecc_backend.log`
- `/data/tmp/opencode/post_ecc_frontend.log`
- `/data/tmp/opencode/post_ecc_ruff.txt`
- `/data/tmp/opencode/post_ecc_mypy.txt`
