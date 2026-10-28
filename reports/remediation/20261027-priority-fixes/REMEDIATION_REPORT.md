# NUSANTARA V1 Priority Remediation Report

Date: 2026-10-28  
Scope: operator-approved priorities in `reports/audit/REMEDIATION_PLAN.md`  
Disposition: **HOLD for operational E2E; no V1 readiness claim**

## Results

| Priority | Result | Evidence and limits |
|---|---|---|
| Exclude unapproved official/review-required documents from ordinary Chat retrieval | PASS in isolated verification | `regression-4-console.txt`, `green-gate-console.txt`, `tests/test_review_publication_v1.py`, `tests/test_v1_sop_boundary.py`; final focused suite below. No live Chat query was run. |
| Bind approval to extracted content revision; invalidate stale approval | PASS in isolated verification | `green-content-version-console.txt`, `green-read-race-console.txt`, `tests/test_review_publication_v1.py`; final focused suite below. No approval was created on the live SOP. |
| SQLite backup captures committed WAL transactions and restores | PASS in isolated verification | `green-backup-console.txt`, `tests/test_sqlite_backup_wal.py`; final focused suite below. Production DBs were backed up before changes under `database-before/`; tests use isolated fixture databases. |
| Reproduce/fix SOP review HTTP 500 | PASS for proven schema failure; HOLD for sustained live availability | `review-reproduction-before.json`, `startup-diagnosis.json`, `green-event-schema/`, `review_live_probe.py` output `live-review-final-after-resume.json`. Proven cause: seven positional values were inserted into an existing eight-column `sop_review_events` table (`trial_id` nullable). `_event` now names its seven columns explicitly. The live backend `/health` returned 200; frontend proxy and review GET timed out on the first latest probe and the subsequent authenticated review GET succeeded. This establishes the observed schema error fix and an intermittent live service, not sustained service recovery or the cause of every earlier 500. |
| Exact SOP inspect → approval → retrieval → sourced Chat | HOLD | Exact live extraction captured at `live-sop-review-snapshot.json` and `live-sop-content-for-operator.md`. Revision `2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c`, source SHA `d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b`, text SHA `73a9dda458b30e86aa78f3af1d528aedf69ed967fdff59f7b5e6ed3bab0a9163`. Latest GET says extraction COMPLETE (2 pages, 4 blocks), `content_ok=true`, `can_approve=false`, approval absent. No live approval or ordinary Chat request was submitted. |

## Latest verification evidence

- Guarded focused backend suite: **74 passed, 0 failed** (`green-final-74/junit.xml`; run included review publication/replay, backup/WAL restore, SOP review, pipeline API, selected Chat, and related V1 boundaries). Pytest reported 367 deprecation warnings; no test failures.
- Control Plane test `control-plane/tests/sop-review.test.tsx`: **6 passed**, including content-check persistence after reload while the final approval button remains disabled. This test was rerun in the current session.
- Current process inspection after elevation showed port 8000 owned by PID 27168, launched from repo `.venv\Scripts\python.exe`, plus PID 30692 child; both match the service Uvicorn app/loopback/port/workers/env-file command traits. Source fix `app/knowledge/sop_review.py` timestamp is 2026-10-27 09:36:48 UTC, before these processes were inspected on 2026-10-28. This is consistent with the service running the latest source; it is not a cryptographic measurement of loaded Python bytecode.
- `live-review-final-after-resume.json`: backend health HTTP 200; Ollama HTTP 200; frontend health and review proxy timed out on that probe. A subsequent direct capture via the review route succeeded at 2026-10-28 03:41:55 UTC, with exact live content and no decision POST.
- Latest review GET shows 4 trials and 5 events (one `content_ok`, four `rating`). The earlier 2026-10-27 snapshot showed four trials and one event. The intervening actor/action source cannot be attributed from available evidence. This agent did not submit those trial/rating/content-check actions. They are not final operator approval: `approval_record_present=false`, `can_approve=false`.
- The user-authorized manual backend PID 3244 was revalidated as the port 8000 owner with Uvicorn command line before being stopped. Only PID 3244 was explicitly targeted; parent PID 9120 was not targeted and exited naturally after its child. Official service startup followed. Current service process identities are recorded in the conversation execution transcript; the earlier official restart output is in prior audit evidence.
- No commit or push was made. No approval action was sent. Test fixture approval is not live approval.

## Root cause and changes

1. Review-decision HTTP 500 was reproduced as `sqlite3.OperationalError: table sop_review_events has 8 columns but 7 values were supplied`. The existing database contains nullable `trial_id`; an unqualified positional insert required exactly seven columns. Explicitly naming the seven event columns fixes compatibility without altering schema or data. A regression first failed with this error, then passed. API regression simulates the extra live column and checks the event/value on a subsequent GET.
2. The PowerShell service lifecycle mutex opener used a signature not available on the installed PowerShell 7/.NET 10 runtime. The compatibility branch selects the supported overload while keeping the same global mutex and locking behavior. Disposable mutex probes passed on PowerShell 5.1 and 7.6.5. It does not change the mutex ACL or bypass the lock.
3. The earlier service blocker was resolved after the user authorized stopping the identified manual listener. Do not infer this proves all historical review HTTP 500 incidents shared the event-schema cause.

## Blockers and next operator action

- The latest backend `/health` is healthy, but frontend health/review proxy showed a timeout before a later successful review GET. Confirm sustained service stability before operational acceptance.
- Inspect the exact extraction in `live-sop-content-for-operator.md` against the live revision above. Only an authorized operator may explicitly decide approval. Current `can_approve=false`; no approval is present.
- After stable service and explicit approval of that exact content revision, run `CHAT_E2E_RUNBOOK.md` and retain prompt, answer, source/page/block citation, and retrieval identity as evidence. Do not use a different revision.
- No one should call this build V1-ready based on test pass count or compliance percentage alone.
