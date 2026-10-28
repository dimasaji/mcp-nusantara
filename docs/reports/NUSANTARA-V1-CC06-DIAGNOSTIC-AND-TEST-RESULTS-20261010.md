# CC-06-DIAGNOSTIC-AND-TEST-RESULTS — 2026-10-10

## Status

`PARTIAL`; the precise candidate model/cache/preprocessing failure is `NOT_VERIFIED` because the approved candidate is inaccessible through Docker in this session.

## Findings

- Baseline candidate evidence: knowledge search HTTP 500 followed by timeout; effective profile says embedding stage FAILED, configured model `indobenchmark/indobert-base-p1`, actual model identity `null` / `NOT_VERIFIED`.
- Source-confirmed: `app/knowledge/indobert_embedding.py` turns any worker `{ok: false}` response into `RuntimeError`, and rejects non-list or non-768-dimensional output.
- Source-confirmed: `app/language/semantic/indobert_client.py` starts a persistent worker, waits 60 seconds by default, and uses `stderr=subprocess.DEVNULL`. Worker stderr includes loading/ready events, but the caller discards it. `nusantara-models/indobert_worker.py` loads tokenizer/model at process startup using `AutoTokenizer.from_pretrained` and `AutoModel.from_pretrained`; there is no local-only setting or bounded diagnostic capture. Text preprocessing is limited to string conversion/strip in the client and worker, then tokenizer truncation/padding to 128 tokens. No runtime evidence isolates preprocessing as the cause.
- Source-confirmed: `app/api/routes.py::_run_sync_v1` times out synchronous V1 work at 30 seconds and shields the background task. That can return HTTP 504 before the worker's default 60-second response timeout, with the timed-out thread retaining a slot. It explains a route-level timeout mechanism but does not prove exact candidate request chronology.
- Source-confirmed cache topology: Compose sets `HF_HOME=/app/data/huggingface`; `/app/data` is a project-scoped named volume and no host Hugging Face cache bind mount is declared. Dockerfile installs worker dependencies and copies only `indobert_worker.py`; it does not pre-download model weights. The host has a Hugging Face IndoBERT cache, but that cache is not declared as a container mount. The candidate volume's actual current cache state remains inaccessible. A cold-cache/download/network failure is therefore a plausible hypothesis, not a runtime-confirmed root cause.
- No provider, model, RAG policy, cache, security setting, database, or application code was changed.

## Tests

Exact focused command (exit 0):

`\.venv\Scripts\python.exe -B -m pytest -c tests/pytest-evidence.ini -o addopts='' -p no:cacheprovider --basetemp <run>\pytest-tmp --junitxml <run>\results.xml -q tests/test_indobert_timeout.py tests/test_configuration_integration.py::test_adapter_constructs_existing_client_without_starting_worker tests/test_configuration_integration.py::test_incompatible_embedding_rejected_before_store_or_worker tests/test_effective_rag_profile.py -k 'not actual_v1_chat and not actual_v2_callback and not actual_v1_search and not dev_endpoint'`

Result: **28 passed, 5 deselected, 0 failed**, 46 deprecation warnings, XML at `runs/cc06-offline-20261010-03/results.xml` (SHA-256 `BD95B7D6FAB81EC2AE298477FEDDDEC743588E8E0425A380DA70BE16279AAA72`). Test source hashes are in `NUSANTARA-V1-CLOSURE-EVIDENCE-MANIFEST-20261010.json`. This covers worker timeout/recovery, adapter configuration/validation, and offline retrieval profile fixtures; it does not load the actual IndoBERT weights or validate candidate cache/network.

A preceding broader offline selection reached HTTP/TestClient cases and was manually interrupted, exit 1, with no XML. It is not counted as a test result.

## Required next check

With read-only access to the exact candidate, collect bounded worker startup diagnostics and the effective retrieval profile. Keep stderr bounded and redact request text/secrets. Verify whether configured model files are present under the candidate's actual `HF_HOME`, then separately classify model-load, download/cache, preprocessing, response-shape, and timeout outcomes before making any fix.
