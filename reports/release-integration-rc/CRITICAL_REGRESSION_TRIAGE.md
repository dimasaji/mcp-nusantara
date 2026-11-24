# Critical Regression Triage

- SHA: `f4f8b7f5b99f6fbd034d21149675fb625881a788`
- Overall status: **FAIL** (raw suite), **PASS** (no new IDs vs PR #19), **BLOCKED** (2 critical open items)
- Evidence: `reports/release-integration-rc/evidence/regression_full.out`, `regression_tb_line.out`, `regression_after_fix.out`, `regression_triage.md`

## Commands and exit codes

| Command | Exit | Status | Evidence |
|---|---:|---|---|
| `env PYTHONPATH=backend python -m pytest -q --tb=no --continue-on-collection-errors` | 1 | FAIL | `evidence/regression_full.out` |
| `env PYTHONPATH=backend python -m pytest -q --tb=line --continue-on-collection-errors` | 1 | FAIL | `evidence/regression_tb_line.out` |
| same command after local harness fix | 1 | FAIL | `evidence/regression_after_fix.out` |
| `git diff --check` | 0 | PASS | `evidence/diff_check.out` |

Raw results before local fix: `85 failed, 1488 passed, 62 skipped, 48 errors` — identical to PR #19 baseline, `new_ids=0`, `fixed_ids=0`. After local fix: `84 failed, 1489 passed, 62 skipped, 48 errors`, `new_ids=0`, `fixed_ids=1`.

`PYTHONPATH=backend` is required because multiple tests launch child Python processes with their own environment. Without it, subprocesses fail with `ModuleNotFoundError: No module named 'app'`.

## Grouping of 133 IDs before local fix

| Root-cause group | Count | Status | Evidence example |
|---|---:|---|---|
| Windows platform-bound | 69 | NON_CRITICAL / BLOCKED on PC | `ActorError: WINDOWS_REQUIRED` |
| V2 endpoints intentionally not mounted in V1 | 9 | NON_CRITICAL, release-note required | 404 where old tests expect 403/200 |
| Optional LangChain/LangGraph extra absent | 10 | NON_CRITICAL | adapter returns `None` |
| Evidence isolation harness | 17 | NON_CRITICAL | `EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED` |
| Historical fixture/artifact missing | 20 | NON_CRITICAL | `FileNotFoundError` for archived snapshots |
| AST snapshot drift | 1 | NON_CRITICAL | `CHAT_SESSION_PATTERN` hardening |
| IndoBERT worker unavailable | 1 | **CRITICAL / BLOCKED** | HTTP 500 on `/v1/knowledge/search` |
| RAG top_k semantics | 1 | **CRITICAL / BLOCKED** | `assert 1 == 3` |
| Subprocess import path | 2 | NON_CRITICAL | child PYTHONPATH used repo root |
| Collection errors | 2 | NON_CRITICAL | missing operator credential / `developer.py` |
| Blank PDF fixture | 1 | NON_CRITICAL | `EXTRACTED_TEXT_QUALITY_CHECK_FAILED` |

## Critical security / database / API / chat read-out

| Domain | Status | Finding |
|---|---|---|
| Security/auth | PASS with disclosure | Auth-shaped failures are Windows-bound attestation tests or V2 routes intentionally not mounted in V1; no live bypass observed. |
| Database | PASS for scope | Active DB untouched; staging persistence and rollback passed; collection guards blocked active DB paths as designed. |
| API | BLOCKED / disclosure | V2 404s are intentional in V1 profile and must be in release notes. |
| Chat | PASS | `/v1/chat` Ollama PASS, provider failure controlled 503, model `llama3.2:1b` verified. |

## Critical items

### 1. IndoBERT worker unavailable — BLOCKED

- Test: `tests/test_langchain_hardening.py::test_knowledge_search_still_works`
- Reproduce: `env PYTHONPATH=backend python -m pytest -q tests/test_langchain_hardening.py::test_knowledge_search_still_works`
- Observed: `assert 500 == 200`; configured default worker path `backend/nusantara-models/.venv/bin/python` does not exist.
- Minimal fix: provision the approved IndoBERT/Docling worker at the configured path or set `NUSANTARA_INDOBERT_PYTHON` to a valid approved worker.
- Why BLOCKED: no approved worker/model artifact is present on this VPS; creating a fake worker would misrepresent grounded retrieval and was not done.

### 2. RAG top_k semantics — BLOCKED

- Test: `tests/test_configuration_integration.py::test_rag_actual_query_and_ingestion_use_config`
- Observed: `assert 1 == 3` because `backend/app/knowledge/engine.py:150-156` deduplicates results per `document_id`.
- Minimal fix: owner must choose between top_k per document (align fixture/contract documentation) and top_k chunks (retrieval semantics change).
- Why BLOCKED: changing retrieval semantics is architectural/policy-level; assertions and thresholds were not changed.

## Fix applied

| File | Change | Before | After | Evidence |
|---|---|---|---|---|
| `tests/test_control_plane_attestation_binding.py:223` | child `PYTHONPATH` root → `root / 'backend'` | `ModuleNotFoundError: app` | proceeds to platform-bound `WINDOWS_REQUIRED` | `subprocess_path_before.*`, `subprocess_path_after.*` |
| `tests/test_runtime_attestation.py:166` | child `PYTHONPATH` root → `root / 'backend'` | `ModuleNotFoundError: app` | PASS | `subprocess_path_after.out` |

No test was deleted, skipped by modification, or given a lower threshold. Ruff/mypy on the whole modified test files still report pre-existing findings; the diff itself passes `git diff --check`.
