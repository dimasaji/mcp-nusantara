$ErrorActionPreference = "Stop"

$Root = "C:\Users\dmaza\mcp-starter"
$ControlPlane = Join-Path $Root "control-plane"
$ReportDir = Join-Path $Root "docs\reports"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Report = Join-Path $ReportDir "CONTROL_PLANE_FINAL_ACCEPTANCE_$Timestamp.md"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA CONTROL PLANE - FINAL ACCEPTANCE CHECK" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Set-Location $Root

$Branch = (git branch --show-current).Trim()
$Head = (git rev-parse HEAD).Trim()

Write-Host ""
Write-Host "Repository : $Root"
Write-Host "Branch     : $Branch"
Write-Host "HEAD       : $Head"

Set-Location $ControlPlane

if (-not (Test-Path ".\package.json")) {
    throw "control-plane/package.json tidak ditemukan."
}

Write-Host ""
Write-Host "[1] Frontend build..." -ForegroundColor Yellow

npm run build

if ($LASTEXITCODE -ne 0) {
    throw "Frontend build FAILED."
}

Write-Host "BUILD : PASS" -ForegroundColor Green

Write-Host ""
Write-Host "[2] Control Plane UI..." -ForegroundColor Yellow

try {
    $Ui = Invoke-WebRequest `
        -Uri "http://127.0.0.1:5173/" `
        -Method GET `
        -TimeoutSec 10

    if ($Ui.StatusCode -eq 200) {
        $UiStatus = "AVAILABLE"
        Write-Host "UI : AVAILABLE" -ForegroundColor Green
    }
    else {
        $UiStatus = "NOT_VERIFIED"
        Write-Host "UI : NOT_VERIFIED" -ForegroundColor Yellow
    }
}
catch {
    $UiStatus = "NOT_VERIFIED"
    Write-Host "UI : NOT_VERIFIED" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "[3] Evidence API..." -ForegroundColor Yellow

try {
    $Start = Get-Date

    $Evidence = Invoke-WebRequest `
        -Uri "http://127.0.0.1:8000/v1/control-plane/snapshot" `
        -Method GET `
        -TimeoutSec 10

    $Latency = [math]::Round(((Get-Date) - $Start).TotalMilliseconds)

    if ($Evidence.StatusCode -eq 200) {
        $EvidenceStatus = "AVAILABLE"
        Write-Host "Evidence API : AVAILABLE" -ForegroundColor Green
        Write-Host "HTTP         : $($Evidence.StatusCode)"
        Write-Host "Latency      : $Latency ms"
    }
    else {
        $EvidenceStatus = "NOT_VERIFIED"
    }
}
catch {
    $EvidenceStatus = "NOT_VERIFIED"
    Write-Host "Evidence API : NOT_VERIFIED" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "[4] Human Acceptance" -ForegroundColor Yellow

$System   = Read-Host "SYSTEM completed?   (Y/N)"
$Evidence = Read-Host "EVIDENCE completed? (Y/N)"
$Test     = Read-Host "TEST completed?     (Y/N)"
$Review   = Read-Host "REVIEW completed?   (Y/N)"
$Decision = Read-Host "DECISION completed? (Y/N)"

if (
    $System -eq "Y" -and
    $Evidence -eq "Y" -and
    $Test -eq "Y" -and
    $Review -eq "Y" -and
    $Decision -eq "Y"
) {
    $AcceptanceStatus = "COMPLETE"
}
else {
    $AcceptanceStatus = "INCOMPLETE"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " FINAL RESULT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Human Acceptance : $AcceptanceStatus"
Write-Host "Control Plane    : $UiStatus"
Write-Host "Evidence API     : $EvidenceStatus"
Write-Host "Frontend Build   : PASS"

Set-Location $Root

New-Item -ItemType Directory -Force $ReportDir | Out-Null

@"
# Control Plane Final Acceptance

Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz")

## Repository

- Root: ``$Root``
- Branch: ``$Branch``
- HEAD: ``$Head``

## Human Acceptance

| Stage | Result |
|---|---|
| SYSTEM | $(if ($System -eq "Y") {"COMPLETE"} else {"INCOMPLETE"}) |
| EVIDENCE | $(if ($Evidence -eq "Y") {"COMPLETE"} else {"INCOMPLETE"}) |
| TEST | $(if ($Test -eq "Y") {"COMPLETE"} else {"INCOMPLETE"}) |
| REVIEW | $(if ($Review -eq "Y") {"COMPLETE"} else {"INCOMPLETE"}) |
| DECISION | $(if ($Decision -eq "Y") {"COMPLETE"} else {"INCOMPLETE"}) |

Overall Human Acceptance: **$AcceptanceStatus**

## Technical Verification

- Control Plane UI: **$UiStatus**
- Evidence API: **$EvidenceStatus**
- Frontend Build: **PASS**

## Scope

Read-only Control Plane UI acceptance only.

No authentication, credential delivery, R2 authorization,
runtime execution, model operation, RAG mutation, database mutation,
or production operation was authorized by this script.
"@ | Set-Content -Path $Report -Encoding UTF8

Write-Host ""
Write-Host "REPORT:" -ForegroundColor Cyan
Write-Host $Report -ForegroundColor Green
Write-Host ""

if ($AcceptanceStatus -eq "COMPLETE") {
    Write-Host "CONTROL PLANE UI ACCEPTANCE = COMPLETE" -ForegroundColor Green
}
else {
    Write-Host "CONTROL PLANE UI ACCEPTANCE = INCOMPLETE" -ForegroundColor Yellow
}
