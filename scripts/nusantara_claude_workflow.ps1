param(
    [Parameter(Mandatory=$true)]
    [string]$Task
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "NUSANTARA CLAUDE CODE CONTROLLED WORKFLOW" -ForegroundColor Cyan
Write-Host "===================================================================="
Write-Host "TASK : $Task" -ForegroundColor Yellow
Write-Host ""

function Run-Step {
    param([string]$Name,[string]$Script)
    Write-Host "[$Name]" -ForegroundColor Cyan
    if (-not (Test-Path $Script)) { Write-Host "MISSING: $Script" -ForegroundColor Red; exit 1 }
    python $Script
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $Script" -ForegroundColor Red; exit 1 }
    Write-Host "PASS: $Name" -ForegroundColor Green
    Write-Host ""
}

Run-Step "DEVELOPER CORE" ".\scripts\nusantara_developer_core.py"
python .\app\developer_core\context_router.py "$Task"
Run-Step "CLAUDE CODE CONTEXT" ".\app\developer_core\claude_code_integration.py"

$contextFile=".\data\developer_core\claude_code_context.json"
if (-not (Test-Path $contextFile)) { Write-Host "BLOCKED: context tidak ditemukan." -ForegroundColor Red; exit 1 }

$context=Get-Content $contextFile -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "CONTROL STATE" -ForegroundColor Cyan
Write-Host "===================================================================="
Write-Host "Role              : $($context.role)"
Write-Host "Change ID         : $($context.change_id)"
Write-Host "Approval          : $($context.approval_status)"
Write-Host "Allowed Files     : $(@($context.allowed_files).Count)"
Write-Host "Write Mode        : $($context.write_mode)"
Write-Host ""
Write-Host "SECURITY" -ForegroundColor Yellow
Write-Host "Production Write  : $($context.execution.production_write)"
Write-Host "Shell Execution   : $($context.execution.shell_execution)"
Write-Host "Automatic Patch   : $($context.execution.automatic_patch)"
Write-Host "Fail-Closed       : $($context.fail_closed)"

if ($context.execution.production_write -eq $true -or $context.execution.shell_execution -eq $true -or $context.execution.automatic_patch -eq $true -or $context.fail_closed -ne $true) {
    Write-Host ""
    Write-Host "DEVELOPER CORE : BLOCKED" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "CLAUDE CODE TASK CONTEXT" -ForegroundColor Green
Write-Host "===================================================================="
Write-Host ""
Write-Host $Task
Write-Host ""
Write-Host "Context siap untuk Claude Code." -ForegroundColor Green
Write-Host "Human approval tetap diperlukan sebelum Controlled Write." -ForegroundColor Yellow
Write-Host ""
Write-Host "Production Write : BLOCKED" -ForegroundColor Green
Write-Host "Shell Execution  : BLOCKED" -ForegroundColor Green
Write-Host "Automatic Patch  : BLOCKED" -ForegroundColor Green
Write-Host "Fail-Closed      : ENABLED" -ForegroundColor Green
Write-Host ""
Write-Host "DEVELOPER CORE : READY" -ForegroundColor Green



