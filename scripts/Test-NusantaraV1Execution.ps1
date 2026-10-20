param([string]$OutputRoot='artifacts/v1-continuation')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) '.venv/Scripts/python.exe'
$OutputRoot=Join-Path $OutputRoot ('run-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,10))
Write-Host "Run output: $OutputRoot"
$tests = @(
 'tests/test_provider_failure.py', 'tests/test_runtime_identity.py',
 'tests/test_v1_operator_control.py', 'tests/test_v1_response_projection.py',
 'tests/test_v1_chat_rag_regression.py', 'tests/test_hermes_v1_conversation.py',
 'tests/test_v1_langgraph.py', 'tests/test_evidence_registry.py',
 'tests/test_evidence_decision_api.py', 'tests/test_control_plane_readonly.py',
 'tests/test_approval_persistence.py', 'tests/test_retrieval_evidence_persistence.py',
 'tests/test_effective_rag_profile.py', 'tests/test_runtime_authorization.py',
 'tests/test_control_plane_attestation_binding.py', 'tests/test_phase4_v1_trust_integration.py',
 'tests/test_runtime_verification.py', 'tests/test_runtime_attestation.py',
 'tests/test_configuration_contract.py', 'tests/test_configuration_integration.py', 'tests/test_v1_current_ui_contract.py',
 'tests/test_v1_review_execution_api.py', 'tests/test_v1_operational_data.py',
 'tests/test_v1_stage_budget.py', 'tests/test_v1_execution_evidence.py',
 'tests/test_developer_core_engine_contract.py', 'tests/test_v1_targeted_boundaries.py'
)
New-Item -ItemType Directory -Force $OutputRoot | Out-Null
$env:R2_CPLANE_ISOLATED_EVIDENCE=Join-Path (Resolve-Path $OutputRoot) 'attestation-isolated.json'
& $python -m pytest @tests "--junitxml=$OutputRoot/regression.xml" -q --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
New-Item -ItemType Directory -Force (Join-Path $OutputRoot 'isolated') | Out-Null
& $python tests/run_evidence_tests_isolated.py (Join-Path $OutputRoot 'isolated')
exit $LASTEXITCODE
