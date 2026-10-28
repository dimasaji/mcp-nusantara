# NUSANTARA V1 — Blocker Closure Update

**Date:** 2026-10-10 (Asia/Jakarta)  
**V1 decision:** V1_HOLD

## Closed in this continuation

- **Evidence Registry evidence package:** the prior current-test-run.json was invalid because its hashes for the isolated test runner and Registry test file were stale. The current suite was run in a new isolated directory and the current test manifest was rebuilt with result and source hashes. The old manifest was preserved in the run directories.
- **AC15 test reference:** the declared test name no longer existed. The criterion text and meaning were preserved; its test links now point to three existing tests that cover blocker reasons, package identity changing with evidence, and test-result hash binding. Original requirements file copy: $oldReq (SHA-256 $oldReqHash). Current requirements file SHA-256: $requirementsHash.
- **Official collector validation:** collect_review_package() returns 15/15 VALID, zero blockers, and pass_allowed=true for the declared Evidence Completion Registry criteria. This applies only to that offline evidence workflow. It does not certify V1 runtime or product acceptance; untime_status remains NOT_VERIFIED.

### Verification and hashes

- Command: .\.venv\Scripts\python.exe -B .\tests\run_evidence_tests_isolated.py docs/reports/nus-evidence-completion-20261010/runs/blocker-closure-20261010-02
- Result: exit 0; **19 passed, 0 failed, 0 errors, 0 skipped**. Includes Registry, decision API, and isolation/descriptor guard tests.
- UI evidence reused without rerunning because all relevant source hashes still match: **17 passed**; typecheck reused at exit 0. These refer to unchanged frontend source hashes and remain scoped evidence, not runtime verification.
- Current test manifest: $testManifest (SHA-256 $testHash).
- Python JUnit: $(Join-Path docs/reports/nus-evidence-completion-20261010/runs/blocker-closure-20261010-02 'python-results.xml') (SHA-256 $xmlSha).
- Results bundle: $(Join-Path docs/reports/nus-evidence-completion-20261010/runs/blocker-closure-20261010-02 'results-bundle.json') (SHA-256 $manifestSha).
- Registry package: $packagePath, package ID $(@{schema_version=1; evidence=System.Object[]; criteria=System.Object[]; blockers=System.Object[]; package_id=evp_sha256_19bf808c764987e8372b98e7a45f44137a4bca31298de6d7ace3a63ebcf9c079; generated_at=10/10/2026 16:43:23; read_scope=MANIFEST_DECLARED_OFFLINE_ARTIFACTS_ONLY; runtime_status=NOT_VERIFIED; pass_allowed=True}.package_id), file SHA-256 $packageHash.
- Official collector: 17/17 declared evidence records validate; all 15 criteria VALID; pass_allowed=true.
- The venv still emits its known missing-base-interpreter warning; despite that warning, the test runner and collector exited 0.

## Open V1 blockers only

| Blocker | Status | Evidence and cause |
|---|---|---|
| CC-01 HTTP regression | BLOCKED | Existing transcript shows Windows socketpair fallback stalls at ccept before route dispatch. No HTTP test result exists. Environment was unchanged; the blocked HTTP test was not repeated. See uns/cc01-http-followup-20261010-02/console-transcript.txt in the prior closure run directory. |
| Docker/runtime attestation | BLOCKED / NOT_VERIFIED | Read-only docker ps --format '{{.Names}}' exited 1: permission denied on 
pipe:////./pipe/dockerDesktopLinuxEngine. Candidate logs, internal port-8000 attestation, and credentials could not be inspected. No credentials were read. |
| CC-06 candidate search/chat | NOT_VERIFIED | Candidate diagnostics and model/cache state remain inaccessible through Docker. Earlier scoped offline tests do not prove the candidate model or request path. |
| CC-06 official-source governance | HOLD | Official Tangerang and Immigration references were found as review leads, but source snapshot authority, jurisdiction, effective date, oracle assertion, and ingestion approval are not settled. No knowledge facts were ingested or promoted. |
| CC-05 memory governance | HOLD | Consent, session ownership, retention, and read/NO-MEMORY policy still need owner decision. No memory implementation was changed. |
| Symlink security | NOT_VERIFIED | Previous targeted Windows test skipped because symlink creation lacked privilege. Local symlink evaluation being enabled does not establish process creation privilege or test the security behavior. Test and guard were not weakened. |
| Production target/deployment | HOLD | No named production target or production deployment authorization is present. No deployment was attempted. |

## Human actions required

1. Provide the authorized environment access needed to read the candidate Docker engine and use the candidate's internal attestation route with existing credentials through its approved secure mechanism.
2. Approve the exact official source snapshots and jurisdiction/scope for the unresolved Tangerang and passport oracle assertions before ingestion.
3. Decide the V1 memory consent/session/retention policy.
4. Name the production target and provide deployment authorization if deployment acceptance is required.
5. Provide a Windows test environment/process with symbolic-link creation privilege to complete the symlink security test.

The Registry currently permits a PASS decision **for the Evidence Completion package** (package ID shown above). The previous PASS response was for an older package ID and was never recorded through the authenticated Registry. It cannot be reused for this package. An authenticated decision would require the authorized live Control Plane; it is unavailable while runtime access is blocked. V1 remains V1_HOLD regardless of that package's eligibility.

No runtime code, model/RAG policy, database, active index, credentials, container, volume, /v2, or production resource was changed. No previously valid CC-01 pure or CC-06 offline results were rerun.
