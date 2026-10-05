$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "NUSANTARA FINAL GIT CLEANUP" -ForegroundColor Cyan
Write-Host "===================================================================="

# 1. Fix .gitignore
$gitignore = ".\.gitignore"
$content = Get-Content $gitignore -Raw

$exceptions = @(
    "scripts/nusantara_developer_core.py",
    "scripts/nusantara_claude_workflow.ps1"
)

foreach ($rule in $exceptions) {
    if ($content -notmatch "(?m)^" + [regex]::Escape($rule) + "$") {
        Add-Content -Path $gitignore -Value "`r`n$rule"
        Write-Host "[GITIGNORE] Added: $rule" -ForegroundColor Green
    }
}

# 2. Stage official source files
Write-Host ""
Write-Host "[1] Staging official source..." -ForegroundColor Cyan

git add .gitignore
git add --force .\scripts\nusantara_developer_core.py
git add .\scripts\nusantara_claude_workflow.ps1

# 3. Explicitly keep runtime directories outside Git
Write-Host ""
Write-Host "[2] Protecting runtime directories..." -ForegroundColor Cyan

git reset -- .developer_staging 2>$null
git reset -- data 2>$null

# 4. Show staged changes
Write-Host ""
Write-Host "[3] STAGED CHANGES" -ForegroundColor Cyan
git status --short

# 5. Commit
Write-Host ""
Write-Host "[4] COMMIT" -ForegroundColor Cyan

git diff --cached --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "Tidak ada perubahan staged. Tidak ada commit baru." -ForegroundColor Yellow
}
else {
    git commit -m "Nusantara Developer Core one-command workflow"

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "COMMIT FAILED" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "COMMIT SUCCESS" -ForegroundColor Green
}

# 6. Verify repository
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "FINAL GIT STATUS" -ForegroundColor Cyan
Write-Host "===================================================================="

$status = git status --short

if ($status) {
    Write-Host $status

    Write-Host ""
    Write-Host "REPOSITORY : NOT CLEAN" -ForegroundColor Red
    Write-Host "Perubahan di atas harus diperiksa sebelum melanjutkan." -ForegroundColor Yellow
    exit 1
}
else {
    Write-Host "Working tree clean." -ForegroundColor Green
    Write-Host ""
    Write-Host "REPOSITORY : CLEAN" -ForegroundColor Green
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "NUSANTARA GIT CHECKPOINT : PASS" -ForegroundColor Green
Write-Host "===================================================================="

git log -1 --oneline
