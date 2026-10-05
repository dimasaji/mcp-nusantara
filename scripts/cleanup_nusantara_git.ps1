$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "NUSANTARA GIT REPOSITORY CLEANUP" -ForegroundColor Cyan
Write-Host "===================================================================="

$gitignore = Join-Path $ROOT ".gitignore"

if (-not (Test-Path $gitignore)) {
    New-Item -ItemType File -Path $gitignore -Force | Out-Null
}

$rules = @(
    ".developer_staging/",
    "data/",
    ".env",
    ".venv/",
    "venv/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    "tools/*/.venv/"
)

$current = Get-Content $gitignore -ErrorAction SilentlyContinue

foreach ($rule in $rules) {
    if ($current -notcontains $rule) {
        Add-Content -Path $gitignore -Value $rule
        Write-Host "[ADD IGNORE] $rule" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[1] Runtime protection" -ForegroundColor Cyan

foreach ($path in @(".developer_staging","data",".venv","venv")) {
    if (Test-Path $path) {
        if (git check-ignore $path 2>$null) {
            Write-Host "[OK] $path ignored" -ForegroundColor Green
        }
        else {
            Write-Host "[WARN] $path NOT ignored" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "[2] Staging source/documentation" -ForegroundColor Cyan

$paths = @(
    ".claude/skills/developer-core",
    ".claude/skills/markitdown",
    "app/developer_core",
    "docs/DEVELOPER_CORE_OPERATIONALIZATION.md",
    "docs/markitdown",
    "scripts/nusantara_developer_core.py",
    "scripts/cleanup_nusantara_git.ps1",
    "scripts/nusantara_claude_workflow.ps1",
    "tools"
)

foreach ($path in $paths) {
    if (Test-Path $path) {
        git add -- $path
        Write-Host "[STAGE] $path" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[3] Remove runtime from index" -ForegroundColor Cyan

git reset -- .developer_staging 2>$null
git reset -- data 2>$null

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "GIT STATUS" -ForegroundColor Cyan
Write-Host "===================================================================="

git status --short

Write-Host ""
Write-Host "Cleanup preparation selesai." -ForegroundColor Green
Write-Host "Tidak ada git clean / penghapusan file otomatis." -ForegroundColor Green
Write-Host ""

$answer = Read-Host "Commit staged changes sekarang? (Y/N)"

if ($answer -match "^[Yy]$") {
    git diff --cached --quiet

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Tidak ada perubahan staged." -ForegroundColor Yellow
        exit 0
    }

    git commit -m "Nusantara Developer Core workflow and Claude Code integration"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "COMMIT FAILED" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "COMMIT SUCCESS" -ForegroundColor Green
}

Write-Host ""
Write-Host "FINAL STATUS" -ForegroundColor Cyan
git status --short
