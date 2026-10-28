# Targeted remediation: checksum representation and approval reuse

Date: 2026-10-09, Asia/Jakarta. Scope narrowed by the latest owner instruction after the preceding governance task was interrupted. This report covers the completed two-file remediation, not completion of the earlier broad governance contract.

## Changes

- app/knowledge/web_evidence.py: added a checksum verification function within the existing WEIP module, reusing its SHA-256 helper. Extended the existing approval principal/validation rather than creating a second engine. A timezone-aware injectable clock controls document validity, approval expiry and approval timestamp. Each pure request projection rechecks current authorization through the trusted-host callback; rejects expiry at or after the deadline, revocation, missing/invalid consent state, purpose mismatch, unavailable authorizer, changed content/version/binding and changed authorization terms. Consent is not requested again from a human for each reuse. Missing expiry, provenance reference or supported conditions fails closed. Default production authorizer remains absent and denies access.
- tests/test_web_evidence_pipeline.py: added 25 targeted offline cases and explicitly extended mock authorizer fixtures with scope, expiry, provenance reference and APPROVED state. These identities are synthetic fixtures in temporary staging, not fabricated real owner approvals. Includes exact expiry boundary tests at one microsecond before, at, and after expiry; metadata versus content changes; all four actual read-only KTP fixtures; invalid representation; unavailable/untrusted/rejected authorization; reference/clock/version/raw-byte failures.

Before, the last verified WEIP approval did not recheck expiry, revocation or purpose on each projection. After, eligibility is rechecked for each use and unsupported/unproven validity is denied. This does not connect the module to runtime KnowledgeEngine or grant active ingestion.

## Checksum representation

The deterministic representation is: decode UTF-8 with optional BOM; normalize CRLF to LF; extract text after the single literal `## Isi Sumber` heading followed by two LF characters; trim surrounding whitespace; SHA-256 UTF-8 encoded text. Internal whitespace is preserved. The marker must be unique and content nonempty. No manifest digest or document bytes were changed.

All four manifest hashes match this representation. The corresponding full Markdown byte hashes are different:

| ID | Full-file SHA-256 | Normalized content SHA-256 matching manifest |
|---|---|---|
| TNG-KTPEL-001 | 8aebcdbf09964b9bdf082d8fd67b7b1ebce78655d1a5cf81cca1ef178bc561df | 39aa82acb367f1f1fee4b83233cb7f4e9ecf2b208dda98c25850320edd4a6190 |
| TNG-KTPEL-002 | 7d200fe47c6929a34025ee609107c5c8a94b60d54c51c3091197bd5bb42a31c0 | 0696c46d84889489c10be150d380e65e81bd92c8ce5e1d1b9064a8320a11e8de |
| TNG-KTPEL-003 | f065256d89d89f9d27909effab5eb8166ba19a31662bd26046fcb515ee54b23b | c3a59093d3b9e8709752888fdc6701dde94e6a236b05c9e09e6b12616013a890 |
| TNG-KTPEL-004 | 2f7dc22f56ac05dbdedd9769821a927720a35ff8c00c1fcfbb6bff6962aa50cc | 198cc4a4daeb0d28b4fba3cba0d7f5aa6b6a1306f9c0e5007195804e9259adf7 |

Metadata and outer whitespace are excluded from the content checksum. Their changes can leave this checksum unchanged; therefore it is not full-file integrity assurance. WEIP consent remains bound separately to raw content hash, parsed hash, metadata and version. Matching checksum is NOT source authentication or usage authorization. The initial FIXTURE_VERIFICATION.json preserves the full-file comparison and alternative digest evidence; its full-file INTEGRITY_FAIL is distinct from the now-tested normalized-content match. No live source or historical acquisition cause was authenticated.

## Actual verification

Commands from repository root:
- `.venv/Scripts/python.exe -B docs/reports/weip-governance-closure-20261009T181812/verify.py targeted`: exit 0; 25 PASS, 0 FAIL, 0 SKIP, 69 deselected. XML: targeted-20261009-182256/results.xml.
- Same runner with `regression`: first exit 1; 178 PASS, 1 FAIL, 0 SKIP, 6 deselected. WinError 5 replacing a temporary staging file in the legacy-approval rejection test. Traceback remains in regression-20261009-182327/results.xml. No weakened checks or source change followed.
- Repeat with `regression`: exit 0; 179 PASS, 0 FAIL, 0 SKIP, 6 deselected; 62 existing datetime.utcnow deprecation warnings. XML: regression-20261009-182347/results.xml. The cause of the first Windows file replacement failure remains unestablished; the repeat does not erase it.
- Scoped git diff --check: exit 0. Both source files compiled in memory without bytecode output. Finalize helper: exit 0, no unexpected source changes or fixture/manifest changes.

Regression includes all 94 WEIP tests plus source-fetcher, effective-RAG-profile and configuration-contract tests. Six excluded cases are NOT_RUN: actual_v2, dev_endpoint, consumers_correlation, empty_result, bootstrap_layers, owner_reads. Deselected is not PASS or SKIP.

Guard permits read-only access to only the four explicitly named KTP files and their manifest. Other data/.env reads are blocked; SQLite is restricted to per-run temporary DBs; external subprocess/model startup and real network are blocked. All runs recorded zero guard violations. Actual V1 temporary-store compatibility remains fixture-based. No active DB/WAL/SHM access, runtime operation, production integration, provider call, dependency installation or native PDF activation occurred.

## Preservation and remaining gates

CHANGE_AUDIT.json records before/after source hashes and unchanged fixture/manifest hashes. Only the two authorized source/test files changed among inspected application/test/Console baselines. Engineering Console and historical reports were preserved. Exact task hunks are in SCOPED_CHANGES.patch; do not use broad restore/reset or delete pre-existing modules to undo them. New artifacts are confined to this ongoing unique report directory. No additional general audit was performed after the narrowed instruction; graph cache query/update was not run.

The representation and approval-reuse behavior are VERIFIED_SCOPED offline. This improves WEIP-06 and WEIP-09 implementation/test evidence, but does not close either broader source-authenticity/production-identity gate automatically. Other WEIP gate dispositions remain unchanged.

Owner inputs still needed: document-specific usage approval tied to exact version and purpose; an independently trustworthy source/provenance baseline; approved production operator identity/authority integration. Document paths are now explicitly available for inspection and need not be supplied again. Native PDF isolation, temporary-adapter transaction/failure rollback, and active integration approval remain separate open gates. WEIP-COMP-DB-01 remains REVIEW_REQUIRED; no active sidecar finding was rechecked or resolved here.

WEIP PARTIAL / REVIEW_REQUIRED. V1 FAIL / HOLD. V2 DEFERRED. Active knowledge-store integration NOT_AUTHORIZED. STOP after targeted remediation and evidence.
