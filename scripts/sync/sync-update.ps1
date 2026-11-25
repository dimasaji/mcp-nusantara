#!/usr/bin/env pwsh
# sync-update.ps1 — Nusantara V1 controlled sync update
# Per contract Phase 13:
#   - Require clean working tree
#   - Require approved canonical branch
#   - Require no divergence
#   - Perform fast-forward only
#   - Validate dependency changes
#   - Run smoke tests
#   - Report result
#   - MUST NOT: force push, reset hard, delete data, upload secrets,
#     auto-merge when diverged, auto-deploy production
$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    Write-Error "ERROR: not inside a git repository"
    exit 1
}

Push-Location $repoRoot

$canonicalBranch = $env:SYNC_CANONICAL_BRANCH -ne $null ? $env:SYNC_CANONICAL_BRANCH : "origin/codex/fullroot-control-20261007"
$approved = [bool]::Parse($env:SYNC_APPROVED)

Write-Host "=== NUSANTARA V1 SYNC UPDATE ==="
Write-Host "Repository: $repoRoot"
Write-Host "Canonical branch: $canonicalBranch"
Write-Host ""

# 1. Require clean working tree
Write-Host "--- Precondition: clean working tree ---"
$status = git status --short
if ($status) {
    Write-Host "BLOCKED: working tree is dirty. Commit or stash changes first."
    $status
    exit 1
}
Write-Host "OK: working tree clean"

# 2. Require approved canonical branch
Write-Host "--- Precondition: canonical branch approved ---"
if (-not $approved) {
    Write-Host "BLOCKED: SYNC_APPROVED=1 not set. Canonical branch merge requires repository owner approval."
    Write-Host "Set SYNC_APPROVED=1 only after owner confirms canonical branch."
    exit 1
}
Write-Host "OK: canonical branch approved"

# 3. Require no divergence
Write-Host "--- Precondition: no divergence ---"
git fetch origin
$div = git rev-list --left-right --count "HEAD...$canonicalBranch" 2>$null
$parts = $div -split " "
$ahead = $parts[0]
$behind = $parts[1]
Write-Host "Ahead: $ahead, Behind: $behind"
if ($ahead -ne 0 -or $behind -ne 0) {
    Write-Host "BLOCKED: divergence detected (ahead=$ahead behind=$behind). Resolve via reconciliation branch + PR, not fast-forward."
    exit 1
}
Write-Host "OK: no divergence"

# 4. Perform fast-forward only
Write-Host "--- Sync: fast-forward only ---"
$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch"
git pull --ff-only origin $canonicalBranch
Write-Host "OK: fast-forward complete"

# 5. Validate dependency changes
Write-Host "--- Validate: dependency changes ---"
$changed = git diff --name-only HEAD@{1} HEAD 2>$null
$depChanged = $changed | Where-Object { $_ -match 'requirements-lock\.txt|pyproject\.toml|frontend/package-lock\.json|frontend/package\.json' }
if ($depChanged) {
    Write-Host "NOTICE: dependency manifest changed. Review before installing."
    Write-Host "Do NOT copy virtualenv or node_modules between environments."
    Write-Host "Install from manifest/lockfile on each environment separately."
} else {
    Write-Host "OK: no dependency manifest changes"
}

# 6. Run smoke tests
Write-Host "--- Smoke tests ---"
if (Test-Path "tests/test_v1_smoke.py" -and Test-Path ".venv/bin/python") {
    & .venv/bin/python -m pytest tests/test_v1_smoke.py -q || Write-Warning "WARNING: smoke tests failed"
} else {
    Write-Host "SKIP: tests/test_v1_smoke.py or .venv not found"
}

Write-Host ""
Write-Host "=== SYNC UPDATE COMPLETE ==="
Write-Host "New HEAD: $(git rev-parse HEAD)"

Pop-Location
