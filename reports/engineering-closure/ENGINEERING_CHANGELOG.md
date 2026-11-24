# Engineering Changelog — WP-03

- Branch: `codex/engineering-closure-20261124`
- Work package: evidence-driven remediation of inherited regression IDs.
- Status: 59 inherited IDs fixed; 3 external blockers remain; no new IDs.

## Application/code changes

- `backend/app/core/control_plane_projection.py`
  - Reads `frontend/evidence-sources.json` and `frontend/CPLANE_OWNER_AUTHORIZATION.json`.
  - Keeps R2/R3/RAG evidence as `NOT_VERIFIED` when pinned artifacts are absent or mismatched.
- `backend/app/core/evidence_registry.py`
  - Path canonicalization for the requirements manifest source.
- `backend/app/knowledge/engine.py`
  - Blank native PDF pages fall back to OCR pipeline text; `source_page_count` records original page count.
- `backend/app/knowledge/sop_review.py`
  - SOP review detail exposes `source_page_count`.

## Test and fixture changes

- `tests/run_evidence_tests_isolated.py`
  - Allows read-only imports from interpreter/site-packages roots while preserving active-data and write isolation.
- `tests/fixtures/v1-current-contract/source-contract.json`
  - Reconciles historical pins to authoritative restored git blobs and adds canonical backend path pins.
- `tests/test_audit_regressions.py`
  - Mounts archived V2 routes on a local app for intentionally disabled V2 endpoints.
- `tests/test_phase3_metrics_integration.py`
  - Rewrites V2 metrics fixture to use a local app.
- `tests/test_session_memory.py`
  - Uses a local app for opt-in V2 chat memory.
- `tests/test_provider_identity.py`
  - Aligns baseline paths, session-id pattern and authorized public fields while keeping the remaining AST surface pinned.
- `tests/test_runtime_attestation.py`
  - Compares named handlers, normalizes authorized request-id and document-tools additions, and keeps subprocess import-path fix.
- `tests/test_runtime_verification.py`
  - Asserts V1 routing and absence of active `/v2` paths.
- `tests/test_configuration_integration.py`
  - Uses a 3-document RAG fixture with `chunk_size=2000`; restores R1/config pins.
- `tests/test_control_plane_readonly.py`
  - Accepts honest `NOT_VERIFIED` projection for absent/mismatched R2/R3 evidence and keeps warning assertions.
- `tests/test_evidence_finalization.py`, `tests/test_evidence_registry.py`, `tests/test_evidence_runner_subprocess.py`, `tests/v1_execution_fixture.py`
  - Canonicalized evidence paths.
- `tests/test_web_evidence_pipeline.py`
  - Synthetic KTPEL fixture checksum coverage.
- `tests/test_sop_source_pages.py`
  - Scanned-PDF/OCR page-count fixture.
- `tests/test_langchain_e2e.py`
  - Per-test optional flag isolation.
- `tests/test_v1_langgraph.py`
  - Correct expectation for safe ungrounded rejection.

## Restored / fixture artifacts

- `developer.py`
- `.dev/MDA_R1_OFFICIAL_CLOSURE_20261007_143016.json`
- `.dev/MDA_R2_IMPLEMENTATION_CHECKPOINT.json`
- `.dev/checkpoints/r2-20261007/FINAL_OWNER_ACCEPTANCE_RECORD.json`
- `.dev/checkpoints/r2-20261007/source-before/app/api/routes.py`
- `.dev/checkpoints/r2-20261007/health-gate/source-before/app/api/routes.py`
- `.dev/checkpoints/r2-20261007/source-before/app/api/v2_routes.py`
- `.dev/checkpoints/r1-local-001-20261007/BASELINE.json`
- `docs/reports/r2-a7-runtime-attestation-20261008/main.py.before`
- `docs/reports/r2-a8-remediation-20261008/PROFILE_BEFORE.json`
- `reports/CONFIGURATION_BASELINE_20261006.json`
- `reports/configuration/CONFIGURATION_PROGRESS.json`
- `data/knowledge/official_sources/ktp_el/manifest.json`
- `data/knowledge/official_sources/ktp_el/tng-ktpel-001.md` … `tng-ktpel-004.md`

KTPEL content is explicitly `fixture_only`, `source_authentication=NOT_VERIFIED`, and `usage_authorization=NOT_AUTHORIZED`.

## Reports

- `reports/engineering-closure/FULL_REGRESSION_CLOSURE_REPORT.md`
- `reports/engineering-closure/INDOBERT_RUNTIME_REPORT.md`
- `reports/engineering-closure/RAG_ENGINE_ACCEPTANCE_REPORT.md`
- `reports/engineering-closure/DOCKER_FULLSTACK_ACCEPTANCE_REPORT.md`
- `reports/engineering-closure/KNOWLEDGE_E2E_ACCEPTANCE_REPORT.md`
- `reports/engineering-closure/PERFORMANCE_AND_RELIABILITY_REPORT.md`
- `reports/engineering-closure/PC_VPS_ACCEPTANCE_CHECKLIST.md`
- `reports/engineering-closure/V1_ENGINEERING_CLOSURE_REPORT.md`
- `reports/engineering-closure/evidence/WP-03/*`

## Non-changes

- No production deploy, merge or force push.
- No active DB, model, volume or port change.
- No real secret, PII, SOP upload or operator credential injection.
- No test deletion, threshold lowering, or systematic skip added for mandatory V1 IDs.
