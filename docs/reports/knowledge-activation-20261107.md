# Knowledge activation and chat stability — 7 November 2026

Baseline: `9de8e2c71ca242e064c2fef8b7230d609c5d39a1`, branch `codex/fullroot-control-20261007`.
Work branch: `codex/knowledge-activation-20261107`.

## Scope and acceptance

Finish the broken V1 operator path: reviewed source and metadata → explicit approval → active Knowledge → authenticated new chat → search → numbered selection → grounded follow-up. No automatic approval, new UI workflow, model replacement, V2 enablement or production data migration.

Acceptance:
1. Source, completed PDF extraction, checked content, valid metadata, ready index and no open problems gate approval; manual chat trials are optional.
2. An approved document is `Aktif`, searchable by operator chat, remains so after reopening storage, and remains inaccessible to public chat.
3. New operator chats and history send the existing operator credential even without document selection; public requests stay unauthenticated. Existing public/operator session isolation remains.
4. `/cari SOP <query>` lists unique documents on actual newlines. A valid result number selects a document and preserves follow-up context; invalid numbers preserve the result list. Empty queries clear stale search results.
5. Retrieval failure is reported as unavailable rather than a successful empty search. The original failure stage remains available in internal retrieval receipts.
6. PIAK-03 fixture tests work from a fresh checkout, without ignored local artifacts.
7. Historical archive checksums remain byte-exact across operating systems, without changing recorded hashes.

## Workflow evidence

### Graphify

CLI initially absent. Inspected the existing graph using vocabulary expansion and bounded adjacency traversal; relevant owners were SOPReview, V1 knowledge boundary and review UI. Installed CLI, then queried `sop review approval knowledge search retrieval metadata`; graph references were cross-checked against current source because the graph included historical snapshots. Ran `graphify update .` after code changes; final result recorded below.

### Diagnosis

- Approval repro: `test_approval_without_manual_trials_activates_chat_and_survives_restart` failed: `can_approve=True` but status was `Menunggu penilaian percobaan...`.
- Hypotheses: stale status rules vs failed approval persistence vs unavailable index. Status branch inspection and the persistent public review/retrieval repro isolated the stale status rules. Approval readiness and status now share the same requirements.
- Search repro: `test_search_result_number_selects_document_and_preserves_followup_scope` failed on literal `\\n`; numeric selection was nested inside `/cari` and therefore unreachable. Previous automatic first-active-document selection also narrowed search arbitrarily and tried to mutate request types it did not own; removed it so the existing approved catalog boundary supplies candidates.
- Operator repro: UI test failed because the initial chat request lacked `X-Admin-Token`, despite the existing operator session namespace. Chat/history now consistently use the current credential.
- Existing RAG receipt tests reproduced swallowed embedding and semantic-store exceptions. Removed the broad lexical fallback so genuine failures produce the existing `RETRIEVAL_UNAVAILABLE` response rather than misleading missing-knowledge answers.
- Fixture failure: pipeline regression depended on an ignored `artifacts/` path. Preserved the historical fixture text from the tracked backend-safe test capture in `tests/fixtures/piak03-extracted.txt`; changed only the fixture location, preserving expected behavior. This is historical extracted text, not a fresh verification of the original PDF or its current legal validity.

### TDD

Public seams follow the previously agreed V1 ingestion/review/retrieval and operator chat UI scope. Captured failing approval, search and operator-auth tests before fixing their behavior; existing failing retrieval receipt tests served as the RAG red stage. Fixture embedding/inference/OCR avoid launching external models. Tests exercise real temporary SQLite persistence, the actual review/retrieval interfaces and the HTTP router. These checks do not prove native Docling OCR or model quality on real scanned documents.

### Codebase design

Publication ownership stays in SOPReview. `approval_requirements` now contains actual mandatory conditions, including index readiness; obsolete case/rating keys are no longer approval prerequisites. Trial records, failure reports and revision bindings are preserved. Search reuses Knowledge and existing service context persistence; no replacement search engine or new memory storage. Authentication remains in the existing transport and backend boundary. No schema migration.

Compatibility: consumers treating `case:*` and `all_trials_reviewed` as mandatory approval requirement keys must adopt the revised contract. `required_cases` remains available for optional diagnostics. Failed diagnostic ratings still create blocking problems; additional review/trial changes still invalidate an earlier approval binding.

## Validation

- Backend: 157 passed across 15 Knowledge, PDF tool, review, metadata, publication, scope, grounding, dialogue and retrieval-profile test modules.
- Frontend full suite: 208 passed across 27 files. The initially failing archive checksum test was traced to CRLF-versus-LF checkout conversion: all 35 mismatches exactly match their original recorded hashes when represented with CRLF. `.gitattributes` now pins those 35 historical text files individually to CRLF. Recorded hashes, archive content and assertions are unchanged. No broad binary or source-file conversion rule was added.
- TypeScript and Vite production build: passed (444 modules).
- Browser: attempted all three `e2e/chat-settings.spec.ts` viewport scenarios. Default Playwright browser was absent; download failed with truncated ZIP. Retried with installed `/usr/bin/chromium`; launch is blocked by `socket() failed: Operation not permitted`. Thus browser assertions did not run; no browser PASS is claimed.
- Graph: `graphify update .` completed AST extraction and rebuilt outputs (30,899 nodes, 74,833 edges), with a pre-existing syntax error in `patch_embedding_identity.py`. Installed version 0.9.103 rewrote the older graph extensively and reduced its historical node set from 43,827. Restored the original tracked graph/cache rather than commit an unrelated graph migration; **committed graph remains stale** for these changes. No semantic regeneration was run. This is a workflow limitation.
- Ruff: existing style violations remain in the touched legacy modules; broad formatting/refactoring is outside this behavior fix. No claim of a clean repository-wide lint/type result.
- Windows services, local Ollama inference, IndoBERT worker, native OCR on CAPIL PDFs, current production DB and port 5180 are not connected to this cloud checkout. Their live status is unverified. No production SOP is automatically approved.

## Review

Independent Standards review found an oversized-number conversion bug; fixed by bounding digit count before conversion and covered by a red/green regression. Independent Spec review found lost explicit-scope selection, post-ranking selection scope, and mandatory-rerating UI wording. All were fixed and re-reviewed with no remaining blockers in the reviewed scope; the seven search regressions passed. Standards re-review additionally passed 38 tests across search, review and public-access boundaries.

This change is not a claim that the complete Nusantara release is production-ready. Browser/native OCR/model checks and stale graph remain explicit limits.
