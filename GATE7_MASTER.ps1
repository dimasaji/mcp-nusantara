$ErrorActionPreference = "Stop"
Set-Location "C:\Users\dmaza\mcp-starter"

$path = ".\app\api\routes.py"
$backup = ".\app\api\routes.py.bak_gate7_final"

Copy-Item $path $backup -Force
$src = Get-Content $path -Raw

# Pastikan import time
if ($src -notmatch '(?m)^import time\s*$') {
    $src = [regex]::Replace(
        $src,
        '(from __future__ import annotations\r?\n)',
        '$1import time' + [Environment]::NewLine,
        1
    )
}

# Pastikan timer tersedia
if ($src -notmatch 'started\s*=\s*time\.perf_counter\(\)') {
    $src = [regex]::Replace(
        $src,
        '(health\s*=\s*await\s+provider\.health_check\(\))',
        '$1' + [Environment]::NewLine + '        started = time.perf_counter()',
        1
    )
}

Set-Content $path $src -Encoding UTF8

python -m py_compile $path

if ($LASTEXITCODE -ne 0) {
    Copy-Item $backup $path -Force
    Write-Host "SYNTAX ERROR - BACKUP DIKEMBALIKAN" -ForegroundColor Red
    exit 1
}

Write-Host "routes.py : SYNTAX OK" -ForegroundColor Green

.\service\nusantara-service.ps1 restart

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "=== HEALTH ===" -ForegroundColor Cyan
Invoke-RestMethod "http://127.0.0.1:8000/v1/health/detail" |
    ConvertTo-Json -Depth 8

Write-Host ""
Write-Host "=== GATE 7 TEST ===" -ForegroundColor Cyan

$body = @{
    session_id = "gate7-final"
    user_input = "Bagaimana cara cek status KTP-el?"
    model = "llama3.2:1b"
    stream = $false
} | ConvertTo-Json

$r = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/v1/chat" `
    -ContentType "application/json" `
    -Body $body

$r | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== VERDICT ===" -ForegroundColor Cyan

if ($r.grounding.grounded -eq $true) {
    Write-Host "GROUNDING : PASS" -ForegroundColor Green
} else {
    Write-Host "GROUNDING : FAIL" -ForegroundColor Red
}

if ($r.provider_status -eq "evidence_fast_path") {
    Write-Host "FAST PATH : PASS" -ForegroundColor Green
} else {
    Write-Host "FAST PATH : $($r.provider_status)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Backup: $backup" -ForegroundColor Gray
