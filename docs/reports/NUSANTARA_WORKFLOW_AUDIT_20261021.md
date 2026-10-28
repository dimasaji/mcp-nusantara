# Nusantara workflow execution: 2026-10-21

Status: all five workflow stages completed for the collection failure and five behavior-test failures identified below. The complete backend suite and live production behavior remain unverified; this is not a release readiness claim.

## Scope and baseline

User requested execution of Graphify -> Diagnosing Bugs -> TDD -> Codebase Design -> Code Review. Baseline HEAD: `fe47e90575986d5c65856d0f68ce898038423e36`, branch `codex/fullroot-control-20261007`. Working tree already contained modifications to 17 tracked files plus untracked files, including P0 knowledge-boundary work. Those changes belong to the pre-existing working tree and are preserved.

## Graphify

Graph has 8,959 nodes. CLI failed with `uv trampoline failed to canonicalize script path`; stored interpreter location was unavailable. Used JSON graph BFS fallback with graph vocabulary `chat ingestion knowledge nusantara readiness test verification`. Relevant sources include `app/knowledge/official_knowledge_ingestion.py`, `app/knowledge/rag.py`, and `tests/test_v1_operational_data.py`. Wiki index was absent. Graph references are navigation evidence, not runtime verification.

## Reproduction and diagnosis

Commands below ran from the repository root using the existing virtualenv, with elevated access because its interpreter was inaccessible in the sandbox.

| Command | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q --maxfail=3` | Collection failed on three backup modules before reaching the configured stop limit. |
| `.venv/Scripts/python.exe -m pytest tests/test_chat_openrouter_route_wiring_v1.py --collect-only -q` | Original module collected successfully: one test. |
| `.venv/Scripts/python.exe -m pytest --collect-only -q --ignore-glob=*.bak-*.py` | 1,314 tests collected successfully. |
| `.venv/Scripts/python.exe -m pytest -o addopts= -q --ignore-glob=*.bak-*.py --maxfail=5` | 114 passed, five failed, four subtests passed; stopped early. |

Collection hypotheses: broad filename pattern, backup placement, or broken original module import. Original collection succeeds; CLI exclusion restores collection. Evidence supports excluding backup artifacts from default collection without deleting them.

The five behavior failures are:

1. `test_authorized_ingest_keeps_path_literal`: patches `ingest_document`, while current HTTP route calls `process_knowledge_source`; fake receives no call.
2. `test_search_empty_and_populated_results`: expects unauthenticated 200, receives 403. Existing P0 contract makes search operator-only.
3. `test_slow_knowledge_work_keeps_event_loop_responsive[ingest]`: same stale ingestion fake; real pipeline rejects short content. This run reached the real ingestion path, so it is not an isolated responsiveness proof. Database rollback or cleanup was not performed because unrelated data must be preserved.
4. `test_provider_payload_uses_snapshot_and_request_precedence`: outgoing options contain additional fixed `top_k`, `repeat_penalty`, and `num_batch` values.
5. `test_legacy_provider_and_explicit_nondefault_arguments`: same additional options contradict exact expected legacy payload.

## TDD and implemented changes

The user confirmed continuation after the proposed seams: pytest CLI, authenticated ingest/search HTTP behavior, and provider generation observed through a simulated HTTP transport.

Completed scope:

- `pyproject.toml`: exclude `*.bak-*.py` through default pytest options, without deleting backups. `tests/test_pytest_collection.py` runs the real CLI in a temporary fixture project and proves active `test_backup_restore.py` remains collectible. The final test was observed red with the exclusion removed and green after restoration. Plugin loading is explicit so the child works under the protected runner.
- `tests/test_audit_regressions.py`: use the existing AST-isolated route-composition approach for the affected knowledge tests. The fixture compiles real request classes, HTTP route functions, and async sync-work wrapper; it supplies an explicit fake backend instead of starting the application. Ingestion observes the literal filename/bytes/ID/metadata forwarded to `process_knowledge_source`.
- Authenticate positive search fixtures; add missing/invalid-token denial cases for search and ingestion. Keep the operator-only application guard unchanged. Preserve the pre-existing fixture-admin change in the responsiveness test.
- `app/models/ollama.py`: remove unconditional `top_k=20`, `repeat_penalty=1.05`, and `num_batch=256`. Existing exact transport expectations and the generation-options contract remain unchanged; the provider now delegates those unspecified settings to Ollama defaults. This can change live sampling and batching from the previous hardcoded tuning; no live performance claim is made.
- `scripts/verify_development_workflow.py`: reuse the protected offline runner and extend its selected tests rather than duplicating its data/dotenv safeguards.

Red/green evidence: initial isolated run reported 97 passed and three failed (the two provider regressions plus a test-child plugin setup issue). The child explicitly loads pytest-asyncio after plugin autoload is disabled; the final collection test was then separately proved red against the original collection configuration. After both fixes, the protected runner passed all 100 selected cases. Final output is stored at `artifacts/development-workflow-20261021/backend-final.txt`.

## Codebase Design

Collection policy belongs in pytest configuration, without moving or deleting backups. Existing operator authorization belongs in the security interface and must remain enforced. Test adapters should match the current ingestion interface so failures cannot accidentally invoke real storage. Provider defaults should have one documented owner, with transport-level assertions covering precedence. No broad refactor is justified by the observed failures alone.

## Code Review

Independent Standards and Spec sub-agents reviewed both the initial findings and the completed scope. Review baseline remains `fe47e90575986d5c65856d0f68ce898038423e36`; no task commits were created. Working-tree review: `git diff HEAD -- app/models/ollama.py pyproject.toml tests/test_audit_regressions.py`, plus explicit reads of both new Python files. The Standards reviewer inspected the diff; the Spec worker could not access Git and reviewed the current files against the supplied scope and contracts.

### Standards results

Final review: zero actionable findings in completed scope. The AST fixture does not verify complete production application wiring; this is an explicit limit of the protected offline test. Pre-existing private adapter access and duplicated local hash logic remain outside the fix. A possible local-hash dimension mismatch has not been reproduced and remains a follow-up candidate, not a confirmed regression caused by this task.

### Spec results

Final review: zero blocking product findings in completed scope. The collection test retains the active backup-restore test, ingestion fake matches the READY response contract, positive/negative authorization cases preserve P0, and provider behavior matches the established options contract. Simulated HTTP transport does not verify a live model.

### Control-plane verification

Initial `npm --prefix control-plane run build` passed TypeScript checking but failed in Vite/esbuild while removing a Windows temporary file. Retried with TEMP/TMP pointing to `artifacts/development-workflow-20261021` under the workspace:

- `npm --prefix control-plane run build`: passed. Existing bundle-size and dependency annotation warnings remain.
- `npm --prefix control-plane test -- --reporter=dot`: 22 test files passed, 170 tests passed. jsdom emitted `window.scrollTo` not-implemented messages; they did not fail the suite.

These are frontend build/test results, not proof of live backend/provider integration. Build output was regenerated under `control-plane/dist`.

## Final verification and remaining limits

`.venv/Scripts/python.exe -B scripts/verify_development_workflow.py`: 100 passed in the final recorded run. Existing datetime deprecations, the parent runner's disabled-plugin asyncio configuration warning, and a TestClient dependency warning remain. New-file Ruff checks and `git diff --check` pass.

`graphify update .` succeeded AST-only after final import cleanup: 8,997 nodes, 18,277 edges, and 675 communities. Community labels may be stale; no LLM relabeling was run. A syntax warning concerns existing `patch_embedding_identity.py:44`, outside this task.

All initial five behavior failures now pass through the selected protected suite. The rest of the 1,314-test baseline backend suite has not been rerun to completion. Full application composition, live provider output/latency, deployment, and the pre-existing hash-embedding candidate remain unverified. Existing unrelated working-tree changes are preserved. No commit, push, deployment, database migration, or production data cleanup was performed.
