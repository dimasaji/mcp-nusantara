# NUSANTARA V1 — Resume from HOLD (2026-10-10)

Decision remains `V1_HOLD`. This addendum supplements `NUSANTARA-V1-AUTONOMOUS-CLOSURE-20261010.md`; it does not supersede historical results.

## Current access and test status

- Docker candidate re-inspection: `BLOCKED`. `docker ps --format '{{.Names}}'` exited 1 with `permission denied while trying to connect to the Docker API at npipe:////./pipe/dockerDesktopLinuxEngine`. No container, volume, database, or port-8001 stack was changed.
- Graph query: `NOT VERIFIED`; the graphify launcher previously failed with `uv trampoline failed to canonicalize script path`. The repository graph was not modified.
- Existing CC-01 pure projection evidence remains `PASS_SCOPED_HISTORICAL`: `results.xml` records 11 tests, 0 failures, 0 skips (from 2026-10-10 16:15:55 +07:00). SHA-256 is recorded below.
- The earlier broader CC-01 run was interrupted and has no result XML; it is not a PASS.
- One current HTTP case was attempted in a new run directory: `docs/reports/nusantara-v1-autonomous-closure-20261010/runs/cc01-http-followup-20261010-01/`. Exact command:

  `.\.venv\Scripts\python.exe -B -m pytest -c tests/pytest-evidence.ini -o addopts='' -p no:cacheprovider --basetemp <run>\pytest-tmp --junitxml <run>\results.xml -q tests/test_v1_response_projection.py::test_http_branch_projection_preserves_public_behavior_and_excludes_internal_state[local_rule]`

  Exit code 1 after manual interruption at about 40 seconds. The interpreter also printed `Failed to find real location of C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe`. No `results.xml` was produced, so counts are unavailable and the test is `NOT_VERIFIED` (interrupted), not PASS. Temporary and data paths were redirected into that new run directory.

## CC-06 diagnosis

The prior candidate evidence (from the baseline report) is still the only runtime evidence available: `/v1/knowledge/search` returned 500, then timed out; retrieval profile marked `stage=embedding`, `status=FAILED`, `exception_type=RuntimeError`, configured model `indobenchmark/indobert-base-p1`, `actual_model=null`, identity `NOT_VERIFIED`. Since Docker access is blocked now, these findings cannot be refreshed against the currently running candidate.

Source inspection establishes the failure propagation and timeout relationship, but not the worker's underlying model/cache/preprocessing failure:

- `app/knowledge/indobert_embedding.py` calls the IndoBERT client and raises `RuntimeError` when its worker response is not successful; it requires a 768-element embedding.
- `app/language/semantic/indobert_client.py` starts the configured external worker, waits up to the embedding timeout (default 60 seconds), and suppresses worker stderr (`stderr=subprocess.DEVNULL`). That removes a useful diagnostic channel for differentiating worker startup/model/cache/preprocessing failures.
- `app/api/routes.py` bounds synchronous V1 stages at 30 seconds. The wait is shielded, so a stage timing out at the HTTP layer may continue in its thread while holding a bounded slot; this accounts for a possible HTTP 504 / later contention when an embedding worker does not answer promptly. This is a source-level explanation for the timeout behavior, not proof of the exact candidate request timeline.
- The candidate's effective retrieval profile and runtime worker/cache state cannot be examined without Docker access. No model/provider/RAG setting or security policy was changed; no facts were promoted. The exact root cause inside model loading, cache availability, and preprocessing remains `NOT_VERIFIED`.

## Runtime attestation

Baseline evidence says unauthenticated `/v1/runtime/attestation` returned 403 and no candidate admin token was supplied. Current Docker/environment credential availability could not be verified. No credential was read, printed, changed, or written to evidence. Attestation remains `NOT_VERIFIED`; HTTP health/build identity is not a substitute.

## Source evidence inventory

All listed source files were read-only in this continuation. SHA-256 values establish the inspected bytes, not runtime identity.

| File | Modified UTC | SHA-256 |
|---|---|---|
| `app/knowledge/indobert_embedding.py` | 2026-10-06T11:30:03.7594274Z | `065202822C8EC152A692CF6EB47AAF221D4BE1F29216E640B911183A53968FB9` |
| `app/language/semantic/indobert_client.py` | 2026-10-06T02:48:27.9880549Z | `16205C4213F3B4D051208A9335594AAF7DAA0A39D8A14BDD472A30AF9807A916` |
| `app/api/routes.py` | 2026-10-09T12:00:56.7927860Z | `845B8846FABB491B7F43D11D5FAD4D8C9694F61E1B1576DEEB7188B22BEA8402` |
| `app/core/runtime_attestation.py` | 2026-10-08T09:41:39.1948796Z | `83E45EDA842BA7B768C6F21D1997CD6416AA99248399C4AE16DD154501BDA55C` |
| `tests/test_indobert_timeout.py` | 2026-10-06T02:48:28.4617710Z | `8D6EB32F5C5FD55B3A16EBE77C774975CDE93E0579F19D53090E97F356DBEB81` |
| `tests/test_v1_response_projection.py` | 2026-10-09T01:59:44.9997121Z | `F5D72F8E4CF998EEFDAA8A19E747E5D6FF0035C15361B02B542685CB4A115A1C` |
| Existing pure CC-01 `results.xml` | 2026-10-10T09:15:57.3711146Z | `0D90F182AB0A11437DD685B8099163A1D3FC5C9051081697A7F58ADB8543932C` |

## Changes and next blocker

Only this report addendum was created in this continuation; application/runtime, configuration, database, credentials, containers, and volumes were not changed. No new successful test evidence was generated.

Next blocker is access to the already-approved candidate inspection environment and a functioning isolated Python test environment. With that access, the pending checks are (1) retrieve worker startup/model/cache/preprocessing diagnostics and effective retrieval profile without exposing secrets, (2) distinguish the model/cache/preprocessing cause using existing tests/fixtures, (3) repeat targeted CC-01 HTTP tests with bounded execution and isolation, and (4) perform authenticated runtime attestation only if a legitimate credential is available through an existing secure mechanism. Candidate admin credential availability and candidate/container access are the only human/environment decisions needed; no approval is requested for a code or policy change because no such change is currently justified by evidence.
