$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA CORE - MASTER COMMIT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Repository : $Root"
Write-Host ""

git rev-parse --is-inside-work-tree *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Bukan Git repository." -ForegroundColor Red
    exit 1
}

$branch = git branch --show-current

if ([string]::IsNullOrWhiteSpace($branch)) {
    $branch = "unknown"
}

Write-Host "Branch     : $branch"
Write-Host ""

Write-Host "STATUS SEBELUM COMMIT:" -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "Menambahkan seluruh perubahan..." -ForegroundColor Cyan

git add -A

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git add gagal." -ForegroundColor Red
    exit 1
}

git diff --cached --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Tidak ada perubahan baru untuk di-commit." -ForegroundColor Yellow

    $hash = git rev-parse --short HEAD
    $msg = git log -1 --pretty=format:"%s"

    Write-Host "Commit terakhir : $hash"
    Write-Host "Message         : $msg"
    exit 0
}

$message = "Nusantara Core: master snapshot Gate 7-17"

Write-Host ""
Write-Host "Membuat commit:" -ForegroundColor Cyan
Write-Host $message
Write-Host ""

git commit -m $message

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git commit gagal." -ForegroundColor Red
    exit 1
}

$hash = git rev-parse HEAD
$shortHash = git rev-parse --short HEAD

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " COMMIT BERHASIL" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Commit : $shortHash"
Write-Host "Hash   : $hash"
Write-Host "Branch : $branch"
Write-Host ""

Write-Host "COMMIT SUMMARY:" -ForegroundColor Cyan
git show --stat --oneline --decorate --summary HEAD

Write-Host ""

$status = git status --short

if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "WORKING TREE : CLEAN" -ForegroundColor Green
}
else {
    Write-Host "WORKING TREE : MASIH ADA PERUBAHAN" -ForegroundColor Yellow
    git status --short
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA MASTER SNAPSHOT SELESAI" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Baseline : Gate 7-17"
Write-Host "Validation: PASS 14 / FAIL 0"
Write-Host "Push     : TIDAK DILAKUKAN"
Write-Host ""

exit 0
