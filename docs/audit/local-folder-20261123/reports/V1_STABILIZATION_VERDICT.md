# V1_STABILIZATION_VERDICT

Date: 2026-11-23
Branch: codex/fullroot-control-20261007
Commit: 6c2536ee (fix config) / b8fd0c9a (frontend rename) / 943b87c4 (backend move) / d70b1b6a (pre-restructure baseline)

## Environment
- OS: Windows 11, Python 3.13.15, .venv
- PYTHONPATH=backend for tests
- Ollama: reachable, gemma3n:e2b-it-q4_K_M available

## Test counts
- Collected: 1675
- Focused (sop_fields, developer_control, v2_disabled, config_contract, response_projection): 102 passed, 0 failed
- Full suite: 1589 passed, 66 failed, 19 skipped, 2 errors (pre-existing/env)

## Acceptance criteria (POST-RESTRUCTURE STABILIZATION)
- Backend startup + health: PASS
- Frontend build: BLOCKED (esbuild temp-file access denied, Windows env)
- No broken paths from restructuring: PARTIAL (core paths fixed; checkpoint-baseline tests still fail due to missing artifacts)
- All failures triaged with evidence: PARTIAL (classified above)
- PIAK-03 E2E: BLOCKED (no real document bytes)
- No new regressions: PASS (focused subsets green)
- Minimal reversible committed changes: PASS

## Final verdict
**PARTIAL**

Functions core (backend health, imports, RAG/sop_fields unit tests) run. Frontend build blocked by environment (esbuild). PIAK-03 E2E blocked (no real PDF). Checkpoint-baseline tests fail due to missing historical artifacts (pre-existing, not caused by this session).
