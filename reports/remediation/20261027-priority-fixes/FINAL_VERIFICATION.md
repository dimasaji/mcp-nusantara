# Final verification evidence — 2026-10-28

## Guarded backend regression

- Command: `.venv\Scripts\python.exe -B reports/audit/evidence/run_guarded_tests.py reports/remediation/20261027-priority-fixes/green-final-74 tests/test_review_publication_v1.py tests/test_review_replay_v1.py tests/test_sqlite_backup_wal.py tests/test_sop_review.py tests/test_document_tools.py tests/test_knowledge_pipeline_api.py tests/test_pdf_preview.py tests/test_selected_pdf_chat.py tests/test_document_scope_v1.py tests/test_v1_sop_boundary.py tests/test_ncp_v1_chat_contract.py tests/test_ingestion_atomic_profiles.py tests/test_v1_chat_history.py`
- Result: **74 passed, 0 failed**; JUnit: `green-final-74/junit.xml`.
- Pytest emitted 367 deprecation warnings, including Starlette/httpx and `datetime.utcnow()` usage. These warnings did not fail tests.

## Control Plane persistence test

- Command: from `control-plane/`, `node.exe node_modules/vitest/vitest.mjs run tests/sop-review.test.tsx`.
- Result: **6 passed**. The new test confirms content check is POSTed with the displayed revision, survives component reload, and leaves final approval disabled. The test uses a frontend mock; it does not prove browser-to-live-backend persistence.

## Current process and runtime observation

- Elevated process identity inspection: PID 27168 is `python.exe` at repo `.venv\Scripts\python.exe`; PID 30692 is a Python child. Both command signatures include repo path, `uvicorn app.main:app`, host `127.0.0.1`, port 8000, one worker and `--env-file`. Port 8000 was owned by PID 27168 in that inspection.
- `app/knowledge/sop_review.py` last write observed at 2026-10-27 09:36:48 UTC, before the current service processes were checked; `/health` later returned HTTP 200. This supports (but does not cryptographically prove) that the restarted process loaded the fixed source.
- Read-only probe record: `live-review-final-after-resume.json`. Backend health 200 and Ollama 200; the first Control Plane health and review proxy requests timed out. A later direct authenticated review GET succeeded and refreshed `live-sop-review-snapshot.json` at 2026-10-28 03:41:55 UTC.
- Latest live state: extraction COMPLETE, 2 pages, 4 blocks; `content_ok=true`; `can_approve=false`; approval absent. Four prior review trials and five events (one content check, four ratings) are visible. Their author/source cannot be attributed; this agent sent no POST for them.

## Evidence boundaries

- The backend suite is isolated/guarded; it proves code behavior against fixtures, including a database fixture with the live extra nullable column. It does not prove production backup/restore against the live DB or a real model answer.
- The live review GET is not final approval and does not prove ordinary Chat retrieval. Live Chat E2E remains gated on an explicit operator approval of the exact revision and stable service health.
- No schema alteration, live approval, Chat request, commit, or push was performed by this agent in the resumed work.
- Final spec review: no new blocker in the event-schema/persistence fix; approval remains gated by `decide()` prerequisites and exact revision checks. Final standards/design review: no blocking finding. Reviewer note about an outdated test comment was corrected (`tests/test_sop_review.py` now says named-column insertion).
- Graphify update was attempted after code changes but did not return output within the bounded wait; it was stopped. `graphify-out/graph.json` timestamp remains 2026-10-27 08:37:19 UTC. Graph index is stale and this is reported as a workflow limitation.
- Git status could not be collected: the bundled `git` executable in the workspace returned Access denied. No commit/push command was issued.
