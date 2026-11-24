# INDOBERT Runtime Report

- Status: **BLOCKED**
- Scope: real IndoBERT/Docling worker availability for grounded retrieval.
- Evidence: `evidence/WP-03/regression_final_tb_line.out`, `evidence/WP-03/regression_final.out`.

## Observed failures

| Test | Observed | Evidence |
|---|---|---|
| `tests/test_langchain_e2e.py::test_retriever_e2e` | `assert 0 >= 1`; retrieval profile reports `embedding_identity.status=NOT_VERIFIED` and `execution_outcome.status=FAILED`, stage `embedding` | `evidence/WP-03/regression_final_tb_line.out` |
| `tests/test_langchain_hardening.py::test_knowledge_search_still_works` | `assert 500 == 200`; route logs `Knowledge search failed` | `evidence/WP-03/regression_final_tb_line.out` |

Root path from traceback:

`backend/nusantara-models/.venv/bin/python`

Exception: `FileNotFoundError: [Errno 2] No such file or directory`.

## Decision

- No fake worker, random embedding, stub model or synthetic vector was created.
- No active runtime, model path or environment variable on the live service was changed.
- The worker must be supplied as an approved IndoBERT/Docling artifact at the configured path or via an explicitly approved `NUSANTARA_INDOBERT_PYTHON` setting.

## Acceptance requirements before PASS

1. Provide approved worker/model artifacts on the target host.
2. Re-run the two failing tests with the exact pinned interpreter.
3. Confirm `embedding_identity.status` is verified and retrieval returns grounded documents from the approved knowledge source.
4. Record the worker SHA/build provenance in the final release notes.

Final status: **BLOCKED — external approved artifact required**.
