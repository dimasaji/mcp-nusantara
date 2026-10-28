# WEIP completion — scoped implementation, acceptance REVIEW_REQUIRED

Contract: NUS-V1-WEIP-20261009 v1.1.0. Date: 2026-10-09, Asia/Jakarta.
V1 HOLD; V2 DEFERRED; active-store integration NOT_AUTHORIZED.
Overall completion: PARTIAL / REVIEW_REQUIRED. Implementation stopped after the final preservation check found missing active-store sidecars. No repair, restoration, or additional application changes were performed after this finding.

## Implemented changes

Continued the existing module; no replacement pipeline or dependency installation.
Changed application/test files only:
- app/knowledge/web_evidence.py
- tests/test_web_evidence_pipeline.py

Nine failing reproduction cases demonstrated six gaps: unbounded outstanding DNS resolver threads per fetcher; deadline expiry accepted after a final read; malformed HTTP exception detail escaping; non-integer/unbounded acquisition budgets; direct parser input bypassing the acquisition byte cap and in-process native PDF fallback; approval based solely on caller-declared reviewer identity.

Fixes bound pending DNS to one resolver per fetcher, validate bounded numeric budgets, check response/read deadlines, cancel/close deadline connections and clean timers, sanitize HTTP protocol failures, cap parser input, and quarantine default PDF extraction. Native parsing is deliberately blocked even if an in-process parser later becomes available. An injected PDF callable is an offline fixture seam and does not prove process isolation.

Approval now fails closed without a trusted host authorizer. Its principal must match reviewer and exact document payload; failed authorization leaves staging in REVIEW_REQUIRED. Legacy declared-only approval cannot export. Production identity integration is not wired or claimed. Registry metadata explicitly identifies owner-declared source assurance; neither HTTPS nor an approval reference authenticates official source authority.

## Actual verification

Commands executed from repository root:
1. `.venv/Scripts/python.exe -B docs/reports/weip-completion-20261009T104250Z/verify.py targeted`
   - Initial reproduction, targeted-20261009-174413: exit 1, 9 FAIL, 0 ERROR, 0 SKIP, 53 deselected. Preserved.
   - First fix verification, targeted-20261009-174735: exit 0, 9 PASS, 0 FAIL, 0 SKIP, 53 deselected.
   - Final expanded verification, targeted-20261009-174841: exit 0, 16 PASS, 0 FAIL, 0 SKIP, 53 deselected.
2. `.venv/Scripts/python.exe -B docs/reports/weip-completion-20261009T104250Z/verify.py regression`
   - regression-20261009-174852: exit 0, 154 PASS, 0 FAIL, 0 ERROR, 0 SKIP, 6 deselected; 62 existing datetime.utcnow deprecation warnings.
   - Includes all 69 WEIP cases, source-fetcher, effective-RAG-profile, and configuration-contract regression. Re-execution was justified by the module changes.
   - Excluded selection: actual_v2, dev_endpoint, consumers_correlation, empty_result, bootstrap_layers, owner_reads. These six cases are NOT_RUN, not PASS or SKIP.
3. Git executable `C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe`, arguments `diff --check -- app/knowledge/web_evidence.py tests/test_web_evidence_pipeline.py`: exit 0. These files are untracked, so this is not a substitute for the exact before/after diff in SCOPED_CHANGES.patch.
4. `.venv/Scripts/python.exe -B docs/reports/weip-completion-20261009T104250Z/finalize.py`: exit 1, preservation discrepancy detected; syntax compile of both changed files passed without bytecode writes. HEAD/branch/status and all baseline hashes are recorded in CHANGE_AUDIT.json.

Every test run reports zero guard violations: network blocked except stdlib socketpair, subprocess startup blocked, database connections restricted to per-run temporary SQLite, active data/.env reads blocked, writes restricted to the new evidence run directory. No live provider, government acquisition, application chat, model control, deployment, or native worker test was performed. Historical results in weip-20261009T102239Z were inspected as historical evidence, not presented as new tests.

## Preservation finding WEIP-COMP-DB-01

Baseline HEAD and final HEAD: 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab. Branch: codex/fullroot-control-20261007.
Only two baseline application/test file hashes changed, as authorized. No baseline Git status entry disappeared. No unrelated baseline source/test/contract hash changed.

The baseline nusantara_knowledge.db-shm and nusantara_knowledge.db-wal files were absent at the final check; `after: null` means missing, not a new checksum. The .db hash remained equal:
`51c5445a43cac61c7763d6aa24bcbb1401c0491ca83a2601e0e5814751325625`.
The production database, its sidecars, and recorded backup hashes also remained equal.

This is an unattributed filesystem discrepancy, not evidence that the WEIP patch deleted sidecars. Guards and executed commands show no task operation against the active database. They cannot attribute independent process/filesystem activity. Sidecar disappearance can accompany SQLite connection cleanup, but that explanation is PLAUSIBLE only and is not established here. Unchanged main-db bytes do not prove unchanged logical state or explain sidecar removal. Do not certify the active database and all sidecars as unchanged.

Runtime observation was read-only: listener 127.0.0.1:8000 PID 36084, parent 33220, start 2026-10-09T15:19:07.716904+07:00; executable C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe. These match the historical observation. The first sandbox process query returned Access denied; subsequent authorized read-only inventory succeeded. No runtime operation or application request occurred. Actual effective active-process database path remains NOT_VERIFIED.

Final disk app-Python fingerprint:
`sha256:0600d86dc183eb21052085c53ef5a26e3b273d27676c8f56e5af2c3bce06fc7b`.
Algorithm and file hashes are in CHANGE_AUDIT.json. This is a scoped disk fingerprint, not proof of the running process's loaded code/dependency closure or equality to historical fingerprint algorithms.

## Gate status

| Gate | Status | Evidence / remaining limit |
|---|---|---|
| WEIP-01 Source registry/allowlist | PASS | Fixture registry and URL rejection tests; real official authority remains separately unverified. |
| WEIP-02 API fetcher | PASS | Mock API acquisition/JSON/timeout tests; real official API NOT_RUN. |
| WEIP-03 Web/PDF acquisition | PASS | Mock MIME, size, redirect, retry tests; no real source acquisition. |
| WEIP-04 SSRF/DNS | PASS | Non-public/mixed/rebinding/redirect rejection and bounded-DNS regression; live TLS behavior NOT_RUN. |
| WEIP-05 Parsing/resources | REVIEW_REQUIRED | API/web and PDF fail-closed controls tested. pypdf/PyPDF2/fitz unavailable; native extraction/resource isolation NOT_RUN. |
| WEIP-06 Provenance | PASS | Hash, metadata, binding and explicit owner-declared assurance tests; source authority not attested. |
| WEIP-07 Versions/expiry/conflict | PASS | Existing and new version/metadata/expiry tests passed. |
| WEIP-08 Staging/quarantine/audit | PASS | Isolated directory and tamper/lifecycle tests; single writer only, not tamper-proof against a privileged malicious writer. |
| WEIP-09 Approval | REVIEW_REQUIRED | Default deny, principal/binding/legacy rejection PASS offline; trusted production authorizer and approved official fixture absent. |
| WEIP-10 V1 adapter | REVIEW_REQUIRED | Pure projection, document/chunk/provenance/dedup compatibility PASS in temporary SQLite with synthetic embeddings. Whole-ingestion failure rollback/compensation not demonstrated. |
| WEIP-11 Active store | NOT_AUTHORIZED | No active integration. Preservation finding WEIP-COMP-DB-01 remains REVIEW_REQUIRED. |
| WEIP-12 Crawling/deployment/V2 | DEFERRED | Not executed or implemented. |

## Exact remaining human gates

1. Official fixture selection: owner chose A twice but supplied no local file path or approval reference. Official fixture verification NOT_RUN. Provide both identifiers; existing manifest entries were not silently selected or promoted. Source records/URLs still require independent authority and validity review.
2. Preservation attribution: review WEIP-COMP-DB-01 through existing read-only evidence before accepting the preservation gate. No delete/revert/restore/checkpoint or service restart is authorized by this report.
3. Native PDF: separately approve a supported resource-limited isolation plan and dependency/environment changes if required. Until then native extraction stays blocked, with failed candidates quarantined.
4. Production approval: bind the authorizer to an approved operator authentication system before production promotion. Fixture principals are not real operator proof.
5. Active integration: requires explicit target database/schema, source/trust rules, compatibility and failure rollback evidence, backup/recovery and operator approval. Passing temporary compatibility does not grant this permission.

## Evidence and rollback

BASELINE.json, full .before snapshots, exact SCOPED_CHANGES.patch, per-run results.xml/guards.json and CHANGE_AUDIT.json are retained in this unique report directory. Helpers and test artifacts are additional files in this new directory only; historical reports were not overwritten.

If local code rollback is later requested, verify current hashes against CHANGE_AUDIT.json and manually reverse only SCOPED_CHANGES.patch hunks in the two named files. Preserve all earlier contents and subsequent changes; do not delete the pre-existing modules or restore a broad Git revision. Do not touch database sidecars to make the audit appear unchanged.

The scoped tests passed, but full WEIP completion and the preservation claim remain REVIEW_REQUIRED. V1 HOLD. V2 DEFERRED. STOP for owner review; no runtime activation.
