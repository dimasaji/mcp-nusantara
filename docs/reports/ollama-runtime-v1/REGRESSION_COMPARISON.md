# Regression Comparison

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:54:45Z` (frontend/build), `~00:56Z` (Python/security), `01:04:36Z` (static)
- Baseline remediation: Python `73 failed, 1528 passed, 45 skipped, 30 errors`; frontend `221 passed`, build PASS; security subset `46 failed, 166 passed`.

## Command

```bash
# targeted
.venv/bin/python -m pytest -q tests/test_ollama_timing.py \
  tests/test_ollama_provider_proxy_env.py tests/test_provider_identity.py \
  tests/test_runtime_verification.py tests/test_ncp_v1_chat_contract.py \
  tests/test_openwebui_adapt.py tests/test_hermes_v1_conversation.py

# full backend
.venv/bin/python -m pytest -q

# frontend
npm test
npm run build

# security subset
.venv/bin/python -m pytest -q tests/test_phase3_observability.py \
  tests/test_phase2_hardening.py tests/test_v1_stage_budget.py \
  tests/test_v1_stage_timing.py tests/test_runtime_authorization.py \
  tests/test_admin_token_source.py tests/test_approval_boundary.py \
  tests/test_langchain_hardening.py tests/test_v1_langgraph.py \
  tests/test_web_evidence_pipeline.py tests/evaluation/test_live_harness.py

# static
git add -f -N docs/reports/ollama-runtime-v1/*.md
git diff --check
```

## Hasil

| Suite | Baseline | Hasil saat ini | Delta | Exit code |
| --- | --- | --- | --- | --- |
| Targeted Ollama/provider/Hermes | subset baseline | `7 failed, 161 passed` | ketujuh failure adalah failure baseline yang sama | `1` |
| Full Python | `73 failed, 1528 passed, 45 skipped, 30 errors` | `69 failed, 1532 passed, 45 skipped, 30 errors` | `4` failure baseline membaik; `0` failure/error baru | `1` |
| Frontend Vitest | `221 passed` | `29 files passed`, `221 passed` | tidak ada perubahan | `0` |
| Frontend build | PASS | `tsc --noEmit && vite build` PASS; 446 modules | tidak ada perubahan | `0` |
| Security subset | `46 failed, 166 passed` | `44 failed, 168 passed` | `2` failure baseline membaik; `0` failure baru | `1` |
| `git diff --check` | PASS | PASS | tidak ada whitespace error | `0` |

Failure yang membaik pada full suite:
- `tests/test_langchain_hardening.py::test_empty_retrieval_abstention`
- `tests/test_langchain_hardening.py::test_request_contract_unchanged`
- `tests/test_phase4_v1_chat_runtime.py::test_phase4_v1_chat_exposes_trust_assessment`
- `tests/test_phase4_v1_chat_runtime.py::test_phase4_v1_chat_trust_confidence_is_bounded`

Failure/error yang tersisa tetap berasal dari blocker baseline: Windows-only authorization (`WINDOWS_REQUIRED`), artifact historis missing, R2/RAG fixture, dan top-k policy yang masih menjadi keputusan owner. Tidak ada assertion yang dilemahkan atau test yang dihapus; tidak ada perubahan source code pada branch ini.

## Exit code

- `targeted_exit=1`, `full_pytest_exit=1`, `security_exit=1`: disebabkan failure baseline yang tidak diubah, bukan failure baru.
- `npm_test_exit=0`, `npm_build_exit=0`, `git_diff_check_exit=0`.
- `secret_pattern_hits=0`; `report_files=10`; tidak ada file source yang berubah.

## Bukti

- `/data/tmp/opencode/ollama_targeted_tests.txt`
- `/data/tmp/opencode/ollama_full_tests.txt`
- `/data/tmp/opencode/remediation_full_after_openwebui.txt` (baseline)
- `/data/tmp/opencode/ollama_frontend_tests.txt`
- `/data/tmp/opencode/ollama_frontend_build.txt`
- `/data/tmp/opencode/ollama_security_tests.txt`
- `/data/tmp/opencode/remediation_security_tests.txt` (baseline)
- `/data/tmp/opencode/ollama_security_static.txt`

## Blocker

- Regression suite baseline memang tidak hijau; kontrak melarang melemahkan assertion, jadi status yang benar adalah “tidak memburuk dibanding baseline”, bukan “semua PASS”.
- `git diff --check` dijalankan dengan `-f -N` karena `docs/reports/` diabaikan oleh `.gitignore`.
