# Independent Spec review

27 October 2026. Scope: the operator-approved four-priority remediation, not a new V1/V2 design. This reviewer read `reports/audit/EXECUTIVE_AUDIT_SUMMARY.md` and `REMEDIATION_PLAN.md` first, then the Code Review skill, saved graph context, current implementation and relevant tests. No tests, database access, service actions, credentials, source edits, commit or push were performed by this reviewer. Only this review report was written.

Baseline: HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; the preflight records eleven preexisting tracked modifications. Current task source is compared with the saved `source-before/` and baseline metadata where available. Findings below concern incomplete acceptance paths, including unchanged callers affected by the new review/version rules; they do not attribute all HEAD differences to this task. Graphify query was attempted and failed with `uv trampoline failed to canonicalize script path`. The read-only fallback `graph-context.json` identifies SOPReview, DocumentTools and V1KnowledgeBoundary and their extracted caller links; current source was then checked directly.

## Requirement evidence already addressed

- New pipeline uploads are classified as review-gated without requiring GET review enrollment (`sop_review.py:252-270`), and GET review no longer enrolls them. Public/nonlocal-provider knowledge denial remains intact.
- PDF review identity now binds extracted blocks/text/pages and parser/configuration, separate from the original-source anchor (`sop_review.py:94-135`). Prior version events are retained, not rewritten. PDF content confirmation/activation requires COMPLETE extraction. Selected-document evidence uses the version-bound extraction path. The new test changes extraction, verifies old approval is absent/inactive, then approves the replacement.
- Three existing backup entrypoints use online SQLite backup, integrity verification, closed temporary snapshot and fsync. The restore test uses a literal committed WAL row and restores a standalone file. It covers all three entrypoints; no unsafe change to a live database is part of this test.
- Primary auditor reports 47 relevant tests PASS in `regression-2`; this reviewer did not rerun them. Passing selected-document tests do not cover the ordinary unscoped/replay paths below.

## SP-01 P1 Unscoped Chat returns source text that was not the approved extraction

**Requirement:** operator priority 2, “Approval harus terikat pada versi isi ekstraksi; perubahan isi membatalkan approval lama”; remediation step 3 requires review/trial/approval/evidence/citation to bind the substantive extraction identity.

**Evidence:** `app/security/v1_knowledge.py:50-51` calls `engine.search_knowledge` and returns original RAG items after checking only current `review.detail(...)[status] == Aktif`. `app/knowledge/engine.py:288` indexed the initial pypdf/source text; `DocumentTools._convert` stores replacement extraction in `document_extractions`, without rewriting that RAG source. `DocumentTools.evidence` is used only by the selected/pilot branch at boundary `:44`. Therefore, after a different extraction is reviewed and approved, ordinary Chat without `document_ids` can consume the old indexed text while the gate checks approval of the replacement. The returned unscoped evidence is not bound to the extraction version checked by that gate.

**Impact:** the source actually used by Chat can differ from the source the operator approved, despite a correct new review version ID. This is a source-verified caller gap, not a runtime test by this reviewer.

**Recommendation/test:** after candidate discovery, resolve every review-gated item to the current approved extraction through the existing review/evidence owner, preserving document scope and version; never substitute old initial extraction text. Extend the changed-content test with an unscoped `V1KnowledgeBoundary` and assert that after replacement approval its evidence contains the new literal and current version, not the initial PDF text.

## SP-02 P1 Cached Chat replies bypass current approval/content-version checks

**Requirement:** priorities 1 and 2: unapproved official documents cannot enter ordinary Chat, and changed content invalidates prior approval.

**Evidence:** `app/api/routes.py:1179-1180` immediately returns `reservation['answer']` for a SUCCEEDED idempotency result before executing the agent/retrieval gate. `app/memory/engine.py:79-83` replay identity compares question and document IDs, not extracted-content version or current approval. The outer route checks explicit selected document activation at `routes.py:1074-1075`, but ordinary unscoped requests have no selected IDs to check. An old unscoped reply can therefore replay after its source becomes unapproved/reprocessing. Even selected requests can replay an old-version answer after the replacement version is approved because document ID/question/request ID remain unchanged; the new scoped version at `:1089-1090` is not part of replay identity.

**Impact:** cached source-bearing content can escape invalidation, so selected fresh retrieval tests alone cannot establish the publication invariant. No replay was executed by this reviewer.

**Recommendation/test:** validate current publication/version authorization for cached source-bearing results before returning them; deny stale/unknown bindings without redispatching a completed provider request or rewriting audit history. Exercise the actual Chat route for an unscoped cached answer followed by revocation/reprocessing, and for replacement approval under the same request ID; require safe conflict/stale response rather than the old answer.

## SP-03 P2 Post-top-k filtering can hide approved sources

**Requirement:** operator priority 1 plus the required E2E “approval → retrieval → jawaban Chat bersumber”; remediation step 2 explicitly requires approved documents to remain retrievable.

**Evidence:** the same `v1_knowledge.py:50-51` requests ranked top-k candidates first, then removes unapproved sources. When k high-scoring pending documents precede an approved source, the result is empty even though approved relevant knowledge exists. This is a deterministic source-level path, not proof of a particular live query failing.

**Impact:** the newly closed gate can make ordinary approved knowledge appear missing. It also performs candidate acquisition on pending documents, rather than restricting the search universe first.

**Recommendation/test:** apply approved eligibility before ranking/top-k through the existing scoped query interface, retaining supported caller filters and bounded query behavior. A fixture with k=1, an unapproved higher-scoring source and an approved lower-scoring relevant source must return only the approved source.

## Runtime and operational acceptance remain HOLD

The actual proxy review HTTP500 is reproduced while backend port8000 refuses connection; restored database review requests returned200. This establishes a current proxy/backend availability failure, not the root of every historical review500. Managed `run-backend` is blocked by the ACL on `Global\NUSANTARA-V1-Lifecycle`; bypassing the lock or changing its ACL is not an acceptance fix. No claim of operational E2E PASS is supported yet. Keep substantive operator approval distinct from fixture decisions and do not infer V1 readiness from 47 passing isolated tests or audit percentages.

An additional recovery concern needs a bounded test if addressed: malformed saved COMPLETE extraction JSON makes `_extraction_state` raise (`sop_review.py:119-124`), while the process endpoint reaches that same detail path through `DocumentTools._identity` (`document_tools.py:114`). Its “process ulang” instruction may be unreachable for such a record. Current restored SOP responses were200, so this is not asserted as their historical500 cause and is not counted among the three blocking findings above.

## Review result

Spec axis: **three open findings** (two P1, one P2) in the source snapshot reviewed. Worst issue within this axis: ordinary Chat/replay can use content outside the currently approved extraction identity. Positive fixes and restore evidence remain valuable, but full priority-1/2 and operational E2E PASS require the missing paths above to be addressed and retested. Final disposition is subject to the primary auditor's subsequent changes and verification.

## Round 2 final review

The primary auditor requested a final read-only review after the later changes. This reviewer inspected the current V1KnowledgeBoundary, cached/fresh response paths in `routes.py`, the mutex fallback, `REMEDIATION_REPORT.md`, `regression-4-console.txt`, and `live-review-after-mutex-fix.json`. No tests, DB/service actions or product writes were performed by this reviewer.

Round-one findings are **closed on the inspected source snapshot**:

- **SP-01:** ordinary unscoped candidates now resolve through `review.evidence` to the approved extraction, with private retrieval-time source-version bindings.
- **SP-02:** cached SUCCEEDED answers now pass `knowledge.validate_response`; fresh output is checked before publication and its private source bindings are persisted. This checks approval/content identity without redispatching the provider for stale cached answers.
- **SP-03:** eligible source IDs are selected before the existing bounded document-scope ranking/top-k calls, including catalogs above20 documents.

`regression-4-console.txt` records **73 passed, 0 failed**. This is focused isolated verification, not whole-project/runtime readiness. The backup entrypoints and restore proof remain within the approved V1 scope. No additional blocking code defect was identified in this final source review.

The report correctly keeps **HTTP500 recovery and live SOP E2E HOLD**. The after-mutex probe records backend/frontend/Ollama health200 and one authenticated review200 for revision `2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c`, but the SOP is pending with zero current trials/events. A transient200 does not establish sustained recovery, operator approval or sourced Chat. Selecting the exact MutexRights overload on the same global lock is not an ACL change or lock bypass; it does not prove why every historical startup/review failed.

Two reporting clarifications were sent to the primary auditor: describe the **currently reproduced proxy500**, not the “original” historical500, unless a correlated historical trace exists; and distinguish no deliberate content/approval migration from incidental schema/lease writes that normal startup and review GET may perform. The corrupted-payload recovery observation above remains an unproven separate edge case, not a diagnosis of the stored SOP or a new blocking finding.

Final Spec result: **0 open blocking findings from round one; live operational acceptance remains HOLD**, awaiting stable supported service operation and an explicit human decision for the exact reviewed revision. No percentage or synthetic reviewer decision substitutes for those gates.

### Round 2 follow-up: cross-runtime mutex and listener blocker

The later `Invoke-WithLifecycleLock` implementation was inspected again. It selects the exact `(string, MutexRights)` overload when exposed and otherwise the single-string overload; both branches open the same `Global\NUSANTARA-V1-Lifecycle` name, then retain WaitOne/release/dispose. No alternate lock name, unconditional execution without acquisition, or ACL mutation is introduced. `probe_mutex_overload.ps1` tests acquire/release on a separate unique test mutex; the primary auditor reports successful Windows PowerShell5.1 and PowerShell7.6.5 executions. This supports the narrow overload compatibility fix, not proof of healthy service startup.

The updated `LIVE_SERVICE_BLOCKER.md` records port8000 PID3244 with a repository-venv parent, but a command that does not match the supervisor's expected launch signature and an unverified working directory/configuration. Calling it **unrecognized by the configured owner matcher and unresponsive at the observation time** is supported. Calling it proven foreign, safe to terminate, or the cause of an earlier historical500 is not. The updated remediation report correctly retains HOLD, distinguishes transient200 from sustained recovery, and does not claim a lock bypass or process termination.

One operational approval prerequisite remains important: `live-sop-review-snapshot.json` explicitly records `live_detail_capture=false` and `content_preview_source=native-sop/extraction.json`. The offline native preview proves successful extraction of the original PDF, but its equality to the exact stored extraction bound by live revision `2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c` has not been established by this snapshot. Before asking for or submitting approval of that live revision, fetch its exact extraction/review content or verify matching canonical content-version fingerprints. An offline preview alone is not sufficient authorization evidence for the live revision. This is an additional clarification of the existing operational HOLD, not a newly observed code regression.

Follow-up conclusion: no new blocking code finding from this source review; supported-runtime recovery, exact live-content review/approval and the final live sourced-Chat E2E remain HOLD. No tests, DB/service calls or product edits were performed by this reviewer.
