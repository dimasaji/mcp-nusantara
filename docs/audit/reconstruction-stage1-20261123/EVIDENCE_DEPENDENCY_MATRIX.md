# Evidence dependency matrix

Baseline: `eb3fe6a7893eeec3e5a2de85863cb609261e5152`; branch `codex/restructure-20261123`.
Audit UTC: 2026-11-23T09:41:24.647757+00:00.

Static references only. Missing references can be fixture/partial/dynamic paths; do not delete or fabricate evidence.

| Evidence path literal | Present | Consumers |
| --- | --- | --- |
| `.dev/MDA_R1_OFFICIAL_CLOSURE_20261007_143016.json` | NOT_FOUND_AT_LITERAL_PATH | `backend/app/core/control_plane_projection.py` |
| `.dev/MDA_R2_IMPLEMENTATION_CHECKPOINT.json` | NOT_FOUND_AT_LITERAL_PATH | `backend/app/core/control_plane_projection.py` |
| `.dev/PROJECT_STATE.json` | YES | `developer.py`, `tests/test_developer_control.py` |
| `.dev/TASKS.json` | YES | `developer.py` |
| `.dev/checkpoints/r1-local-001-20261007/BASELINE.json` | YES | `tests/test_configuration_integration.py` |
| `.dev/checkpoints/r2-20261007/FINAL_OWNER_ACCEPTANCE_RECORD.json` | YES | `backend/app/core/control_plane_projection.py` |
| `.dev/checkpoints/r2-20261007/health-gate/runtime-verification.json` | YES | `backend/app/core/control_plane_projection.py` |
| `.dev/checkpoints/r2-20261007/health-gate/source-before/app/api/routes.py` | YES | `tests/test_provider_identity.py` |
| `.dev/checkpoints/r2-20261007/source-before` | YES | `tests/test_provider_identity.py` |
| `.dev/control_report.json` | NOT_FOUND_AT_LITERAL_PATH | `developer.py` |
| `.dev/repo_inventory.json` | NOT_FOUND_AT_LITERAL_PATH | `developer.py` |
| `.dev/state.json` | NOT_FOUND_AT_LITERAL_PATH | `tests/test_developer_control.py` |
| `.dev/test-` | NOT_FOUND_AT_LITERAL_PATH | `developer.py` |
| `artifacts/NCP-V1-AUTOFIX-HUMAN-001/20261019-104353/browser-baseline` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/verify_ncp_autofix_ui.cjs` |
| `artifacts/NCP-V1-AUTOSTART-001/live-` | NOT_FOUND_AT_LITERAL_PATH | `scripts/Test-NusantaraV1Connection.ps1`, `scripts/Test-NusantaraV1Execution.ps1`, `scripts/Uninstall-NusantaraAutoStart.ps1`, `scripts/validate_nusantara_master.ps1` |
| `artifacts/NCP-V1-AUTOSTART-001/test-` | NOT_FOUND_AT_LITERAL_PATH | `tests/local-services-contract.ps1` |
| `artifacts/backend-deep` | YES | `scripts/verify_backend_deep.py` |
| `artifacts/chat-p0-20261019` | NOT_FOUND_AT_LITERAL_PATH | `scripts/verify_chat_p0_canary.py`, `tools/verification/verify_chat_p0.cjs` |
| `artifacts/control-plane-four-20261019` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/verify_control_plane_four.cjs` |
| `artifacts/control-plane-four-20261019/harness-error.json` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/verify_control_plane_four.cjs` |
| `artifacts/docling-main-chat` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/main-chat-docling-live.spec.ts` |
| `artifacts/docling-main-chat/answers.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/main-chat-docling-live.spec.ts` |
| `artifacts/docling-main-chat/main-` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/main-chat-docling-live.spec.ts` |
| `artifacts/docling-ui` | YES | `frontend/e2e/docling-live.spec.ts` |
| `artifacts/docling-ui/answers.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/docling-live.spec.ts` |
| `artifacts/docling-ui/citation-` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/docling-live.spec.ts` |
| `artifacts/docling-ui/extraction-` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/docling-live.spec.ts` |
| `artifacts/docling-ui/screenshots.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/docling-live.spec.ts` |
| `artifacts/docling-ui/tmp` | YES | `scripts/run_docling_browser.py`, `scripts/run_search_eval.py`, `scripts/serve_laya_local.py`, `scripts/serve_v1_completion_isolated.py`, `scripts/staging_drill.py`, `scripts/start-nusantara.bat` |
| `artifacts/evidence-runs` | YES | `scripts/refresh_v1_evidence.py`, `scripts/release_check.py`, `scripts/repair_gate10_memory.py`, `scripts/repair_gate10_memory_v2.py`, `scripts/repair_gate14_runtime.py`, `scripts/restart-nusantara.bat`, `scripts/restore_e2e_final.py`, `scripts/restore_e2e_runner.py`, `scripts/runtime_class_truth.py`, `scripts/runtime_e2e_lite.py`, `scripts/runtime_e2e_truth.py`, `scripts/runtime_object_truth.py`, `scripts/runtime_truth.py`, `scripts/runtime_truth_c.py` |
| `artifacts/frontend-four-20261019` | NOT_FOUND_AT_LITERAL_PATH | `scripts/verify_control_plane_four.py`, `scripts/verify_development_workflow.py`, `scripts/verify_docker_runtime.py`, `scripts/verify_docling_live.py` |
| `artifacts/knowledge-duplicate` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/knowledge-duplicate-live.spec.ts` |
| `artifacts/knowledge-duplicate/history-` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/knowledge-duplicate-live.spec.ts` |
| `artifacts/knowledge-duplicate/result.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/knowledge-duplicate-live.spec.ts` |
| `artifacts/knowledge-human` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/knowledge-human-live.spec.ts` |
| `artifacts/knowledge-human/compare-` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/knowledge-human-live.spec.ts` |
| `artifacts/knowledge-human/mobile-` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/knowledge-human-live.spec.ts` |
| `artifacts/knowledge-human/result.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/knowledge-human-live.spec.ts` |
| `artifacts/knowledge-human/start-` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/knowledge-human-live.spec.ts` |
| `artifacts/knowledge-pipeline-runtime` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/verify_knowledge_pipeline_live.cjs` |
| `artifacts/knowledge-upload-entry` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/inspect_knowledge_mobile.cjs`, `tools/verification/reproduce_knowledge_upload.cjs`, `tools/verification/verify_knowledge_upload_entry.cjs` |
| `artifacts/merge-20261022/control-plane-` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/chat-settings.spec.ts` |
| `artifacts/ncp-v1-ui` | YES | `frontend/e2e/operator-contract.spec.ts` |
| `artifacts/ncp-v1-ui-followup-20261019` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/operator-followup.spec.ts` |
| `artifacts/ncp-v1-ui-followup-20261019/browser-results.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/playwright.followup.config.ts` |
| `artifacts/ncp-v1-ui-followup-20261019/playwright` | NOT_FOUND_AT_LITERAL_PATH | `frontend/playwright.followup.config.ts` |
| `artifacts/ncp-v1-ui-local-20261019` | YES | `frontend/e2e/operator-design.spec.ts` |
| `artifacts/ncp-v1-ui-local-20261019/browser-results.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/playwright.operator.config.ts` |
| `artifacts/ncp-v1-ui-local-20261019/playwright` | NOT_FOUND_AT_LITERAL_PATH | `frontend/playwright.operator.config.ts` |
| `artifacts/ncp-v1-ui-local-20261019/reference/dist` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/operator-followup.spec.ts` |
| `artifacts/nusantara-e2e-20261016-1018` | YES | `scripts/Start-V1CompletionTest.ps1`, `scripts/Status-NusantaraV1.ps1`, `scripts/Stop-NusantaraV1.ps1`, `scripts/Test-NusantaraEvidenceScoreContract.ps1`, `scripts/Test-NusantaraStartup.ps1`, `scripts/start_windows.ps1`, `scripts/status-nusantara.bat`, `scripts/stop-nusantara.bat`, `tools/verification/check_v1_isolated_upload.cjs` |
| `artifacts/nusantara-e2e-20261016-1018/fixture.pdf` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/check_v1_isolated_upload.cjs` |
| `artifacts/nusantara-e2e-20261016-1018/isolated-runtime/knowledge/source-documents` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/verify_knowledge_upload_entry.cjs` |
| `artifacts/nusantara-e2e-20261016-1018/live-` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/check_v1_completion_live.cjs` |
| `artifacts/sop-conversation` | YES | `scripts/verify_sop_conversation.py` |
| `artifacts/sop-conversation/browser-` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/verify_sop_conversation_ui.cjs` |
| `artifacts/sop-integration` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/verify_sop_chat_ui.cjs` |
| `artifacts/v1-review-e2e` | YES | `tests/serve_v1_review_fixture.py` |
| `artifacts/v1-review-e2e/browser-results.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/playwright.review.config.ts` |
| `artifacts/v1-review-e2e/history-pass.png` | NOT_FOUND_AT_LITERAL_PATH | `frontend/e2e/review-execution.spec.ts` |
| `artifacts/v1-review-e2e/playwright-output` | NOT_FOUND_AT_LITERAL_PATH | `frontend/playwright.review.config.ts` |
| `artifacts/v1-review-e2e/vite-cache` | NOT_FOUND_AT_LITERAL_PATH | `frontend/playwright.review.config.ts` |
| `artifacts/v1-six` | NOT_FOUND_AT_LITERAL_PATH | `scripts/verify_v1_dialogue_and_documents.py`, `scripts/verify_v1_operational_data.py`, `scripts/verify_v1_recovery_rag.py`, `scripts/verify_v1_recovery_runtime.py`, `scripts/verify_v1_six.py`, `scripts/verify_v1_sop_source.py`, `scripts/wire_v2_chat_hermes.py` |
| `artifacts/v1-verification` | YES | `tools/verification/verify_v1_review_live.cjs` |
| `artifacts/v1-verification/rea` | NOT_FOUND_AT_LITERAL_PATH | `tools/verification/check_rea_mcp.cjs` |
| `docs/reports/human-console-recovery-20261009T200537/OWNER_DECISION.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/normal-inspection-preview-20261008-01a11b73` | YES | `tests/inspection_preview_isolated_runner.py` |
| `docs/reports/openrouter-workflow-20261009T184538/IMPLEMENTATION_REPORT.json` | YES | `frontend/src/engineering-evidence.ts`, `frontend/tests/engineering-console.test.tsx` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185424/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185424/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185632/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185632/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185646/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185646/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185807/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185807/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185830/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185830/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185852/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-185852/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-190056/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/regression-20261009-190056/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/stage1-20261009-184852/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/stage1-20261009-184852/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/stage1-final-20261009-184945/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/stage1-final-20261009-184945/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/stage1-fixed-20261009-184918/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/stage1-fixed-20261009-184918/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/workflow-20261009-185310/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/openrouter-workflow-20261009T184538/workflow-20261009-185310/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/r2-a7-runtime-attestation-20261008/main.py.before` | YES | `tests/test_runtime_attestation.py` |
| `docs/reports/r2-a8-remediation-20261008/PROFILE_BEFORE.json` | YES | `tests/test_runtime_verification.py` |
| `docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json` | YES | `frontend/src/engineering-console.tsx`, `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/EXECUTION_RESULTS.json` | YES | `frontend/src/engineering-console.tsx`, `frontend/src/engineering-evidence.ts`, `frontend/tests/engineering-console.test.tsx` |
| `docs/reports/v1-remaining-20261009T182840/regression-20261009-183245/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/regression-20261009-183245/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/regression-20261009-183418/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/regression-20261009-183418/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/targeted-20261009-183120/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/targeted-20261009-183120/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/targeted-20261009-183201/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/targeted-20261009-183201/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/targeted-20261009-183345/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/v1-remaining-20261009T182840/targeted-20261009-183345/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/BASELINE.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/CHANGE_AUDIT.json` | YES | `frontend/src/engineering-console.tsx`, `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/IMPLEMENTATION_REPORT.md` | YES | `frontend/src/engineering-console.tsx`, `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/SCOPED_CHANGES.patch` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/regression-20261009-174852/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/regression-20261009-174852/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/targeted-20261009-174413/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/targeted-20261009-174413/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/targeted-20261009-174735/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/targeted-20261009-174735/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/targeted-20261009-174841/guards.json` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/weip-completion-20261009T104250Z/targeted-20261009-174841/results.xml` | YES | `frontend/src/engineering-evidence.ts` |
| `docs/reports/x/current-test-run.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/tests/verification-pages.test.tsx` |
| `docs/reports/x/python-results.xml` | NOT_FOUND_AT_LITERAL_PATH | `frontend/tests/verification-pages.test.tsx` |
| `docs/reports/x/results-bundle.json` | NOT_FOUND_AT_LITERAL_PATH | `frontend/tests/verification-pages.test.tsx` |
| `reports/CONFIGURATION_BASELINE_20261006.json` | YES | `tests/test_configuration_integration.py` |
| `reports/configuration/CONFIGURATION_PROGRESS.json` | YES | `tests/test_configuration_integration.py` |
| `reports/remediation/20261027-priority-fixes/database-before/0/source-documents/` | YES | `tests/test_capil01_knowledge.py`, `tests/test_docling_layout.py`, `tests/test_executable_skills_native.py` |
| `reports/repro/diag_worker_stderr.py` | YES | `tests/test_indobert_worker_proxy_env.py` |
| `reports/repro/search_probe_b01.json` | YES | `tests/test_v1_search_candidate_window.py` |
| `reports/security_test_report.json` | YES | `scripts/automated_regression.py` |
