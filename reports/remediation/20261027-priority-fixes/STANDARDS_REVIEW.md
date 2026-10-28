# Independent Standards review of priority remediation

27 October 2026. Reviewer performed source/document/Git reads only: no tests, SQL connections, model calls, service changes, operator approvals, or product edits. This file is the only reviewer output written.

## Baseline and scope

Verified HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`. This is an uncommitted remediation, so `git diff HEAD` includes pre-existing user changes and cannot alone identify ownership. Reviewed the before/after copies of SOPReview and DocumentTools under `source-before/`, current changes to the three backup entrypoints, removed review-GET enrollment, the new `sqlite_backup.py`, and related tests. `baseline.json` records the eleven tracked changes already present before this task. No commit-range change is implied by HEAD remaining constant.

Read commands included native Git `rev-parse HEAD`, `diff --stat HEAD -- <scoped targets>`, and `diff --no-index -- <source-before path> <current path>`. The no-index diff exits 1 when differences exist. New untracked helper/tests were read explicitly because Git's ordinary diff does not include their content.

Standards sources: AGENTS.md; `docs/NUSANTARA_DEVELOPMENT_WORKFLOW.md`; `docs/development-principles.md` (security/trust before release, provider abstraction, meaningful integration tests, unchanged architecture); `docs/architecture-decisions.md` (ADR-003/007/009/010/015); FINAL Architecture Contract; Knowledge RAG Contract; Trust Policy Approval Contract; and the operator-approved remediation plan. No root CODING_STANDARDS.md or CONTRIBUTING.md was found by the explicit filename check. Tool-enforced style warnings are not counted as review findings.

Graphify query was attempted first and failed with the known `uv trampoline failed to canonicalize script path`. Parent's saved `graph-context.json` provides current-owner seeds and adjacent links for SOPReview, DocumentTools and V1KnowledgeBoundary; every conclusion below was confirmed against current source rather than historical graph copies.

## Open findings at this review snapshot

### STD-01 P1 — successful request replay bypasses current approval and content revision

- Requirement/rule: priority 1/2; FR-05/07 and Integrity; development-principles §2 requires important results to pass current trust/policy checks before release.
- Evidence: `app/api/routes.py:1180-1181` returns `reservation['answer']` immediately when MemoryEngine reports SUCCEEDED. The route's current pilot precheck at `:1075` only iterates `request.document_ids`. An unscoped request has no IDs there, so a cached source-bearing response is returned without invoking the updated retrieval gate after its source is reprocessed or approval revoked. Public evidence fields at `:145-151` have no extraction version, and projection `:219-223` discards internal version metadata.
- Impact: fixing fresh retrieval alone does not establish approval/version safety for replay. Checking only current Aktif is insufficient if the old answer came from revision A and revision B was independently approved.
- Recommendation: record trusted source/version bindings when retrieval actually returns evidence; persist them privately alongside cached responses; validate exact identity and current activation before replay and final release. Fail closed on source-bearing legacy cache without bindings; preserve ordinary evidence-empty conversational replay and the explicit version-bound operator trial path. Do not infer a new version after generation, which could relabel an old answer.
- Projection caveat: `/chat/history` at `routes.py:1029-1033` copies the entire turn/answer, so any new private binding must be explicitly excluded there as well as in immediate/replay responses.
- Status: static integration defect; parent notified and preparing a focused regression. This reviewer did not run a reproducer.

### STD-02 P1 — unscoped retrieval returns initial indexed text instead of approved extraction

- Requirement/rule: priority 2 and sourced Chat E2E; FR-04/05/08; ADR-007 evidence tracking and development-principles §2 support-by-evidence invariant.
- Evidence: `app/security/v1_knowledge.py:50-51` calls raw `KnowledgeEngine.search_knowledge` and returns its items after checking Aktif. The canonical index is created from initial PDF text at `app/knowledge/engine.py:250-288`; Docling reprocessing updates `document_extractions` and does not rewrite that indexed text. Only selected-document branch `v1_knowledge.py:44` hydrates `review.evidence` for the content-bound review version.
- Impact: after approving a corrected Docling extraction B, generic/unscoped Chat can still receive the initial pypdf text A while merely checking that B is active. The approved content/version and actual prompt evidence can diverge even though selected-document tests pass.
- Recommendation: hydrate every review-gated approved candidate through its exact approved extraction/version before model use and bind that actual returned identity. Add an unscoped positive regression where indexed text and approved extracted content differ; keep the expected answer from an independent source oracle.
- Status: concrete source-path mismatch; no claim that a particular operational answer was observed wrong by this reviewer.

### STD-03 P1 — extraction read can return new blocks labeled with an old version during reprocessing

- Requirement/rule: priority 2; FR-04/05 Integrity; immutable content identity in the approved remediation plan.
- Evidence: `DocumentTools.inspect` first captures `detail = _identity(...)`, then calls status and performs `_row(...)`. The current `_row` at `app/knowledge/document_tools.py:64-65` selects the latest row by stable source anchor; it does not pin a completed extraction for the captured content version. `inspect` at `:104` overlays `version=detail['version_id']` onto whichever payload was read. A completed reprocess between those reads can therefore supply payload B labeled A. Pinning only job ID is not sufficient when a captured QUEUED row becomes COMPLETE while the captured detail version still represents the preceding completed payload.
- Impact: a review display or retrieval read can misrepresent content identity under concurrency; approval-to-content binding must be enforced when materializing the payload, not only when computing detail earlier.
- Recommendation: pin the intended row/job and, before returning any COMPLETE payload, recompute `extracted_version(row['version'], payload)` and require it to equal the requested/captured content version. Reject and require reload on mismatch. A final pre-release source-version check also prevents generation from escaping a concurrent revocation.
- Status: source race demonstrated by interleaving the explicit read sequence; parent notified to add deterministic synchronization-based coverage. No concurrent test executed by reviewer.

### STD-04 P2 — filtering after top-k can hide an approved SOP behind staged candidates

- Requirement/rule: priority 1 and the requested approval→retrieval E2E; FR-07; workflow standards require behavior through the caller interface.
- Evidence: `app/security/v1_knowledge.py:50` obtains only the requested/default top-k across all indexed documents; `:51` then removes candidates whose review is not Aktif. With top_k=1 and an unapproved candidate ranked first, the result is empty even if an approved SOP is the next relevant item. No bounded refill or eligible-document restriction is present in this path.
- Impact: a correctly approved document can remain undiscoverable in mixed staged/active corpora. Filtering returned evidence is safe from direct prompt disclosure but does not satisfy the retrieval acceptance behavior.
- Recommendation: restrict candidate acquisition to eligible sources before scoring/top-k, or implement bounded refill while preserving scope and budgets. Test a mixed corpus where the highest-ranked item is pending and the next item is approved.
- Status: algorithmic integration defect; no live corpus query performed by reviewer.

## Positive controls and preserved scope

The new source anchor versus extracted-content hash correctly avoids rewriting old review events. Changed content naturally selects a new event/trial/approval version. Current code also blocks activation when latest extraction is queued/failed/incomplete and rejects stale review mutation versions. Historical extraction lookup is operator-only and current SOPReview._check still rejects an old revision for current Chat/trials; the separate historical read facility is not itself an activation bypass. UTF content is hashed deterministically through sorted JSON and UTF-8, rather than platform-default text decoding of log output.

All three existing backup entrypoints now delegate to SQLite's online backup API rather than copying an open WAL main file. The helper opens source read-only, checks snapshot integrity, closes connections, flushes the temporary file, and only then publishes the backup. Timestamp microseconds reduce collisions; Windows rename refuses overwrite. It does not claim portable POSIX non-overwrite or power-loss directory durability beyond the stated Windows target. No blocking backup defect was found in the inspected source. Parent evidence reports three WAL-restore tests green; reviewer has not rerun them.

The reviewer did not bypass or alter the existing lifecycle mutex. The live proxy500/backend ConnectionRefused observation and managed startup ACL block remain operational evidence from the primary agent, not a fabricated code root cause or readiness PASS.

Heuristic only: `is_pilot` now also means “requires publication review” for all uploads/official metadata. This is a possible Mysterious Name, not a hard violation or reason to expand a focused fix into a rename/refactor. Shared SQLite backup behavior improves locality; no second Core/Hermes or speculative registry was introduced.

## Review outcome

## Round 2 final review

The primary auditor requested a final read-only review of the mutex fallback and evidence report. Windows PowerShell parser validation found zero syntax errors. Reflection exposed exactly one `OpenExisting(string, MutexRights)` overload, and the implementation selects that overload by signature while keeping the same global mutex and `Synchronize | Modify` rights. It does not bypass the lock or alter its ACL. The supported start attempt passed the overload-resolution stage but service health remained HOLD.

STD-01 through STD-04 are closed on the source snapshot reviewed after remediation: retrieval eligibility is applied before ranking, approved extracted evidence is used, cached and fresh response paths validate private source-version bindings, and the WAL-safe backup helper is used by all three existing entrypoints. `regression-4-console.txt` records 73 passed tests. No new blocking code defect was identified in the focused changes.

Operational acceptance remains HOLD. `live-review-after-mutex-fix.json` records a one-time backend/frontend/Ollama/review HTTP200 for the pending SOP; a subsequent detail request timed out and later backend health was unavailable. The revision has no operator trial or approval. This does not prove sustained service recovery, answer sourcing in live Chat, or the cause of an earlier historical incident. Startup/review GETs may perform incidental schema/lease writes; backups were taken before diagnostics. No approval, ACL change, lock bypass, or commit was made.

Four open findings at this source snapshot: three P1 and one P2. Worst issue within Standards: source identity/activation is not yet enforced at all response materialization/replay paths (STD-01–03). Preserve this initial snapshot and record re-review resolutions after the primary agent's fixes and evidence; do not count overlapping Spec findings as additional independent bugs.

## Round 2 cross-runtime mutex addendum

This addendum supersedes the initial open-findings outcome for the current inspected remediation. STD-01 through STD-04 are closed on the current source snapshot: replay and fresh responses check private retrieval-time version bindings; history excludes the private field; generic retrieval hydrates the approved extraction and applies eligibility before top-k; complete extraction reads verify the payload's computed content version. The recorded focused regression XML contains 73 cases and zero failures. These are isolated verification results, not sustained live acceptance.

Latest review scope was limited to `service/local-services.ps1`, `probe_mutex_overload.ps1`, `LIVE_SERVICE_BLOCKER.md`, and the related evidence claims. Read-only PowerShell parser inspection found zero errors in both scripts. No production mutex was acquired, no service action/test probe was run, and no ACL/process/database was changed by this reviewer.

### Lock invariants

The cross-runtime selection prefers the exact `OpenExisting(string, MutexRights)` signature where available and otherwise invokes the exact one-string overload. It does not bind the rights enum to `NamedWaitHandleOptions`. Both production branches retain `Global\NUSANTARA-V1-Lifecycle`; acquisition still uses the existing timeout, abandoned ownership is handled, actions run only after acquisition, and finally releases/disposes the handle. A denied open still throws. No alternate production lock, ACL rewrite or unsynchronized action path was introduced. No blocking control-flow defect was found in this change.

One wording qualification is required for accuracy: the .NET 10 one-argument overload uses its runtime access contract, not an exactly synchronize/modify-only handle. [Official .NET 10 Windows source](https://raw.githubusercontent.com/dotnet/runtime/v10.0.0/src/libraries/System.Private.CoreLib/src/System/Threading/Mutex.Windows.cs) combines MAXIMUM_ALLOWED with the required synchronize/modify-state bits and passes that mask to OpenMutex; the [one-argument entrypoint](https://raw.githubusercontent.com/dotnet/runtime/v10.0.0/src/libraries/System.Private.CoreLib/src/System/Threading/Mutex.cs) preserves the supplied name without explicit NamedWaitHandleOptions. Thus the fallback does not bypass ACLs, but comments/reports should say runtime-default access requiring synchronize/modify rather than asserting exactly minimal granted rights. This is an evidence/comment precision issue, not a reason to discard the compatibility fallback.

### Probe and operational evidence

`probe_mutex_overload.ps1` creates a unique disposable probe mutex, selects the runtime's supported signature, acquires/releases it and disposes both handles. A passing run establishes overload selection and acquire/release on that same-user probe object. It does not establish rights on an existing differently owned/restricted lifecycle mutex, exercise contention/abandonment, or prove live-service readiness. This reviewer verified syntax, not a runtime acquire/release result.

`LIVE_SERVICE_BLOCKER.md` appropriately separates observed listener/PID traits from unproven process provenance. The listener on port8000 may match uvicorn/host/port yet fail the managed owner matcher because its command line does not prove repository/configuration ownership. Refusing to replace such a listener is a preserved safety condition, not evidence that the mutex fix failed. Operator verification before stopping/adopting that process is appropriate; the report does not authorize either action automatically.

The remediation report correctly retains HOLD for sustained service recovery, historical review500 causality and real operator-approved SOP Chat E2E. The one-time health/review200 and subsequent timeout cannot be converted to sustained PASS. Prefer the phrase “currently reproduced proxy500” over “original500” unless a correlated historical trace exists; also distinguish no deliberate content/approval migration from incidental schema/lease writes that ordinary startup/review GET can perform. These reporting clarifications were sent to the primary agent.

Final Standards conclusion for the inspected changes: **zero remaining blocking findings from round one and no new blocking mutex defect; operational acceptance remains HOLD**. The initial four-findings paragraph above is retained as review history, not the current outcome.
