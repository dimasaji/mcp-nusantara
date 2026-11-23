$ErrorActionPreference = "Continue"

$ROOT = Split-Path $PSScriptRoot -Parent

Set-Location $ROOT

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA AI VALIDATION SUITE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "[1] PYTHON COMPILE" -ForegroundColor Yellow

python -m compileall app

if ($LASTEXITCODE -eq 0) {
    Write-Host "COMPILE: PASS" -ForegroundColor Green
}
else {
    Write-Host "COMPILE: FAIL" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2] HEALTHCHECK" -ForegroundColor Yellow

python scripts\production_healthcheck.py

Write-Host ""
Write-Host "[3] API CONTRACT" -ForegroundColor Yellow

python scripts\test_api_contract.py

Write-Host ""
Write-Host "[4] E2E REGRESSION" -ForegroundColor Yellow

python scripts\test_e2e_nusantara.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " VALIDATION COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan