# BACKEND_REGRESSION_REPORT

Status: `PARTIAL`
Checked at: `2026-11-23T00:25:36Z`

## Baseline dan hasil akhir

- Baseline `/data/tmp/opencode/fix_full_pytest2.txt`: `89 failed, 1512 passed, 45 skipped, 30 errors`.
- Setelah perbaikan grounding `/data/tmp/opencode/remediation_full_after_grounding.txt`: `77 failed, 1524 passed, 45 skipped, 30 errors`.
- Setelah perbaikan definisi dokumen `/data/tmp/opencode/remediation_full_after_openwebui.txt`: `73 failed, 1528 passed, 45 skipped, 30 errors`.
- Delta: 16 failure diperbaiki, 0 failure/error baru.

## Perbaikan

- 12 failure `tests/test_ncp_v1_chat_contract.py` (klaim absensi kontak dengan klaim tambahan atau tanpa bukti `full_document_text`) kini PASS.
- 4 failure `tests/test_openwebui_adapt.py::test_topic_definition_skips_retrieval_even_with_selected_document` kini PASS.

## Regression terpilih

- `/data/tmp/opencode/grounding_fix_targeted_final.txt`: `69 passed`.
- `/data/tmp/opencode/openwebui_fix_targeted.txt`: `147 passed, 1 failed`.
- Satu failure tersisa pada `tests/test_v1_langgraph.py::test_existing_grounding_rejects_missing_evidence_and_unsupported_claim[True-None]` adalah kontrak wrapper yang memang menolak hasil ungrounded; percobaan melonggarkan wrapper menabrak test tersebut dan sudah di-revert.

## Failure/error tersisa

- 38 `tests/test_runtime_authorization.py`: `ActorError: WINDOWS_REQUIRED` — BLOCKED.
- 4 `tests/test_web_evidence_pipeline.py`: manifest historis missing — BLOCKED.
- 4 `tests/test_provider_identity.py`: rute/identitas V2 tidak mounted — OUT_OF_SCOPE V1.
- 4 `tests/test_audit_regressions.py`: endpoint `/v2/dev-payload` — OUT_OF_SCOPE V1.
- 3 `tests/test_langchain_hardening.py`, 3 `tests/test_langchain_e2e.py`: retrieval/provider tidak tersedia pada fixture — BLOCKED.
- 3 `tests/test_phase3_metrics_integration.py`, 3 `tests/test_runtime_verification.py`, 1 `tests/test_session_memory.py`, 1 `tests/test_control_plane_readonly.py`: rute V2/metrics atau bukti historis — OUT_OF_SCOPE/BLOCKED.
- 2 `tests/test_phase4_v1_chat_runtime.py`: request tanpa admin token menghasilkan 404; auth tidak dilonggarkan — BY_DESIGN.
- 2 `tests/test_configuration_integration.py`: contract conflict top-k dan artifact historis missing — BLOCKED.
- 1 `tests/test_sop_source_pages.py`: source-before historis missing — BLOCKED.
- 1 `tests/test_review_publication_v1.py`: expectations top-k/grouping — BLOCKED oleh keputusan kontrak.
- 30 errors `tests/test_control_plane_attestation_binding.py`: bukti/attestation historis dan lingkungan Windows — BLOCKED/OUT_OF_SCOPE.

## Statik

- `git diff --check`: PASS.
- Ruff `app/hermes/agent.py`: 21 sebelum dan 21 sesudah; tidak ada temuan baru.
- Ruff seluruh repo: 5684 temuan baseline.
- Mypy seluruh repo: 1114 temuan baseline.
