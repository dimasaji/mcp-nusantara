# NUS-V1-WEIP-20261009 v1.1.0 — scoped implementation
Date: 2026-10-09 (Asia/Jakarta)
Disposition: PARTIAL_VERIFIED. Isolated implementation and fixture verification available; not production-ready.
V1 HOLD. V2 DEFERRED. Active-store integration NOT AUTHORIZED.

## Changes
Only new application/test files:
- app/knowledge/web_evidence.py: owner-declared source registry and exact HTTPS URL allowlist; DNS-pinned acquisition reusing existing TLS transport; bounded DNS/caller deadline, bytes, rate, redirect/retry controls; API/web parsing, optional PDF parser, SHA-256/provenance; isolated single-writer staging, quarantine, audit chain, review and approval-bound pure V1 request projection.
- tests/test_web_evidence_pipeline.py: 53 isolated acquisition/security/lifecycle/compatibility cases.
Additional files are baseline, test harness/results, exact new-file patch and reports in this new evidence directory. No existing application/test/configuration files were edited. No dependencies installed or declarations changed.

No route registrations, ingestion commands, model invocations or production-source registrations were added. Registry starts empty unless entries are explicitly supplied. Example.org entries occur only in fixtures. Verification references are owner declarations, not independently authenticated government attestation.

## Architecture
Standalone caller -> SourceRegistry -> EvidenceFetcher -> parser/provenance -> StagingStore -> REVIEW_REQUIRED.
Explicit local reviewer record may produce APPROVED_FOR_INGESTION if source/scope/dates/version/integrity checks pass.
to_v1_request produces a DocumentIngestRequest only; it does not call a store or ingest. INGESTED transitions are blocked.
Existing /v1 -> Hermes -> KnowledgeEngine -> canonical RAG -> configured SQLite store is unchanged.
Compatibility test explicitly writes only a temporary fixture SQLite store, with synthetic 768-dimensional embedding; no native worker.

## Baseline and preservation
HEAD: 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab
Branch: codex/fullroot-control-20261007
Working tree was dirty: 3260 status entries recorded in BASELINE.json, with inaccessible-directory warnings retained.
Known default database: data/knowledge/nusantara_knowledge.db (5 documents, embeddings in chunks).
Production database: data/knowledge/production_knowledge.db (6 documents, different schema).
Actual effective DB path of active V1 process remains NOT_VERIFIED; no config/secret access or path switch was performed.
CHANGE_AUDIT.json records zero changed pre-existing baseline files and zero removed pre-existing status entries, including active database and sidecar byte hashes.
Active listener observed after tests: PID 36084, parent 33220, start 2026-10-09T15:19:07.716904+07:00, consistent with earlier read-only observation. No process operations or application requests were issued.
Final source disk fingerprint: sha256:a5fa86373e8a50ec52d4aed47a82ec8775745e8d6c9012f7dc4190b7947d094c. Addition of a new app module changes disk fingerprint; this is not an assertion that the live process loaded it.

## Actual commands and results
- Baseline: guarded stdin pytest.main on tests/test_source_fetcher.py: 7 PASS, exit 0. Initial guard startup failed because replacing Popen broke asyncio import; corrected to guard Popen.__init__. No application defect implied.
- .venv/Scripts/python.exe -B docs/reports/weip-20261009T102239Z/verify.py focused
  Initial runner attempts failed before test execution: pytest capture outside allowed directory, then default logging outside directory. Both protections remained in place; capture/logs redirected to new run directories. Failure notes/available guard evidence retained.
  First completed run: 49 PASS; after DNS/conflict/audit hardening: 53 PASS, 0 FAIL, 0 SKIP, exit 0.
- .venv/Scripts/python.exe -B docs/reports/weip-20261009T102239Z/verify.py regression
  138 PASS, 0 FAIL, 0 SKIP, 6 deselected, exit 0.
  Deselected: actual_v2 callback, dev endpoint, cross-consumer metadata, V2-tagged empty case, bootstrap owner layers and dotenv-reading owner case. These are not PASS or SKIP; the suite is deliberately scoped.
- compile(source, filename, 'exec') for both new Python files: PASS; no .pyc written.
- git diff --check -- app/knowledge/web_evidence.py tests/test_web_evidence_pipeline.py: exit 0. Files are untracked; exact additions are separately captured in NEW_FILES.patch.

JUnit files and guards.json retain executed results. Guards restrict SQLite to per-run temporary paths, block real network except stdlib socketpair, block subprocess/model startup, block active data and user .env reads, and restrict writes to the new run directory. Final completed guards report zero violations.
Warnings: existing datetime.utcnow deprecations; no existing code was changed to suppress them.
No real network acquisition, government source verification, native model or browser/runtime tests were performed.

## Gates
| Gate | Result |
|---|---|
| Baseline/preservation | PASS_SCOPED |
| Registry/exact allowlist | PASS_SCOPED, fixture records only |
| API/web/PDF acquisition controls | PASS_SCOPED with mock transport |
| API/web parsing and provenance | PASS_SCOPED |
| PDF text extraction | Fixture adapter PASS; native parser NOT_VERIFIED / unavailable |
| Staging/quarantine/version conflicts | PASS_SCOPED |
| Security negative tests | PASS_SCOPED; not full production security acceptance |
| V1 schema/request/document/chunk compatibility | PASS_SCOPED in temporary SQLite |
| Active integration | NOT_AUTHORIZED / NOT_RUN |
| Runtime/deployment activation | NOT_AUTHORIZED / NOT_RUN |
| Overall V1 acceptance | HOLD |

## Limitations and next gates
- pypdf is not installed. Default PDF parse failure is quarantined. Native PDF extraction/resource-safety validation remains open; installing into the shared runtime environment was deliberately avoided.
- PDF byte-token checks are conservative, not proof that all active/obfuscated PDF features are detected. No embedded code is executed. Parser isolation/resource hardening requires separate assessment before production use.
- HTTPS/DNS pinning and hashes do not certify source authority or document correctness. No real approved government source or official oracle was invented.
- Query-bearing and percent-encoded URLs are currently rejected conservatively. Specific real-source URL requirements need review before broadening this policy.
- Single-writer local staging only. Registry/approval actor identities are DECLARED_NOT_AUTHENTICATED; audit hashes detect accidental/tamper changes, not a malicious writer who can rewrite/recompute the ledger. Existing operator authentication/approval governance must be bound before production integration.
- No automatic approval is implemented. All parsed documents require review; missing validity dates and unresolved versions cannot be approved/projected.
- V1 compatibility preserves provenance in DocumentIngestRequest and persisted DocumentInfo. Existing canonical retrieval constructs evidence metadata from chunks; propagation/enforcement of document provenance during real retrieval remains an integration gate. No retrieval/grounding/trust behavior was changed.
- Source approval, real-source acquisition, parser readiness, source policy enforcement, live integration, security, memory, oracle and deployment acceptance gates remain open.

## Rollback
No existing source hunks need reversal. Verify hashes in CHANGE_AUDIT.json and remove only the two newly added application/test files if rollback is explicitly desired, provided they have no subsequent edits or references. Preserve this evidence and all pre-existing user changes; no reset/restore/clean.
No database rollback is required because active DB/sidecar hashes were unchanged by this work.
