# Regression triage evidence — RC f4f8b7f5

## Commands

```bash
env PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m pytest -q --tb=no --continue-on-collection-errors
env PYTHONPATH=backend /data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python -m pytest -q --tb=line --continue-on-collection-errors
```

`PYTHONPATH=backend` is required because several tests spawn fresh Python processes with their own environment; the outer pytest `pythonpath` setting is not inherited by those child processes.

## Counts

- PR #19 baseline: `85 failed, 1488 passed, 62 skipped, 48 errors`; 133 FAILED/ERROR IDs.
- RC before local fix: `85 failed, 1488 passed, 62 skipped, 48 errors`; 133 IDs; `new_ids=0`, `fixed_ids=0`.
- RC after local test-harness fix: `84 failed, 1489 passed, 62 skipped, 48 errors`; 132 IDs; `new_ids=0`, `fixed_ids=1` (`tests/test_runtime_attestation.py::test_new_processes_have_distinct_instances_and_actual_main_integration`).

## Root-cause groups before local fix

| Group | Count | Severity | Representative cause |
|---|---:|---|---|
| Windows platform-bound | 69 | NON_CRITICAL | `ActorError: WINDOWS_REQUIRED` from `backend/app/security/local_operator.py:118`; 30 are setup errors in `tests/test_control_plane_attestation_binding.py` |
| V2 endpoints intentionally absent in V1 profile | 9 | NON_CRITICAL (release note) | `assert 404 == 403/200`; V2 routers are not registered unless ATTESTATION profile is selected |
| Optional LangChain/LangGraph extra not installed | 10 | NON_CRITICAL | `assert None is not None`; extras are optional in `pyproject.toml` |
| Evidence isolation harness | 17 | NON_CRITICAL | `EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED ... _pytest/main.py reason=active_database_or_sidecar` |
| Historical fixture/artifact missing | 20 | NON_CRITICAL | `FileNotFoundError` for archived snapshots such as `CONFIGURATION_BASELINE_20261006.json`, `app/api/routes.py.before` |
| AST snapshot drift | 1 | NON_CRITICAL | `CHAT_SESSION_PATTERN` hardening changed AST dump vs archived fixture |
| IndoBERT worker unavailable | 1 | **CRITICAL** | `assert 500 == 200` at `tests/test_langchain_hardening.py::test_knowledge_search_still_works`; default worker path missing |
| RAG top_k semantics | 1 | **CRITICAL** | `assert 1 == 3`; dedup per `document_id` in `backend/app/knowledge/engine.py:150-156` |
| Subprocess import path | 2 | NON_CRITICAL | child `PYTHONPATH` pointed to repo root instead of `backend/` |
| Collection errors | 2 | NON_CRITICAL | `Configured operator credential unavailable`; missing `developer.py` |
| PDF scan fixture | 1 | NON_CRITICAL | blank-page PDF fails `EXTRACTED_TEXT_QUALITY_CHECK_FAILED` |

## Critical findings

- `tests/test_langchain_hardening.py::test_knowledge_search_still_works` — `/v1/knowledge/search` returns HTTP 500 because no IndoBERT worker is provisioned at the configured default path. No approved worker/model artifact exists on this VPS, so provisioning is BLOCKED; no fake worker was created.
- `tests/test_configuration_integration.py::test_rag_actual_query_and_ingestion_use_config` — retrieval returns 1 document for `top_k=3` because the engine deduplicates per document. Changing the semantics to top_k chunks requires an owner policy decision; no assertion was weakened and no threshold was lowered.

## Security / database / API / chat read-out

- Security/auth: no live authorization bypass. Windows-bound attestation tests and intentionally unmounted V2 routes explain the auth-shaped failures.
- Database: active DB was untouched; no integrity failure in staging persistence; collection guards correctly blocked active DB paths.
- API: V2 404s are by design in V1 profile and must be disclosed in release notes.
- Chat: `/v1/chat` with Ollama PASS; provider failure returns controlled HTTP 503 and `/readyz` degraded; no critical chat failure.

## Local fix applied

Two test subprocesses built `PYTHONPATH` from repo root instead of `root/backend`:

- `tests/test_control_plane_attestation_binding.py:223`
- `tests/test_runtime_attestation.py:166`

Changed both to `root / 'backend'`. Evidence: `subprocess_path_before.*`, `subprocess_path_after.*`, `regression_after_fix.*`, `git_diff.out`. Ruff and mypy on the two whole test files still report pre-existing issues; the edit itself passes `git diff --check`.
