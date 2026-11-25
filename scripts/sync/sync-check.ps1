#!/usr/bin/env pwsh
# sync-check.ps1 — Nusantara V1 sync status check (read-only)
# Per contract Phase 13: no force push, no reset hard, no delete, no secrets upload,
# no auto-merge when diverged, no production auto-deploy.
$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    Write-Error "ERROR: not inside a git repository"
    exit 1
}

Push-Location $repoRoot

$canonicalBranch = $env:SYNC_CANONICAL_BRANCH -ne $null ? $env:SYNC_CANONICAL_BRANCH : "origin/codex/fullroot-control-20261007"

Write-Host "=== NUSANTARA V1 SYNC CHECK ==="
Write-Host "Repository: $repoRoot"
Write-Host "Host: $(hostname)"
Write-Host ""

Write-Host "--- Git state ---"
$currentBranch = git branch --show-current
$headSha = git rev-parse HEAD
Write-Host "Current branch: $currentBranch"
Write-Host "HEAD SHA: $headSha"
Write-Host "Canonical branch: $canonicalBranch"

try {
    $canonicalSha = git rev-parse $canonicalBranch -ErrorAction Stop
} catch {
    $canonicalSha = "NOT FOUND"
}
Write-Host "Canonical SHA: $canonicalSha"

Write-Host ""
Write-Host "--- Working tree ---"
git status --short
$status = git status --short
if (-not $status) {
    Write-Host "Working tree: CLEAN"
} else {
    Write-Host "Working tree: DIRTY (uncommitted changes above)"
}

Write-Host ""
Write-Host "--- Remote fetch ---"
git fetch origin 2>$null || Write-Warning "WARNING: fetch failed (check network/remote)"

Write-Host ""
Write-Host "--- Divergence vs canonical ---"
if ($canonicalSha -eq "NOT FOUND") {
    Write-Host "Cannot compute divergence: canonical branch not found locally"
} else {
    $div = git rev-list --left-right --count "HEAD...$canonicalBranch" 2>$null
    $parts = $div -split " "
    $ahead = $parts[0]
    $behind = $parts[1]
    Write-Host "Ahead of canonical: $ahead"
    Write-Host "Behind canonical: $behind"
    if ($ahead -eq 0 -and $behind -eq 0) {
        Write-Host "Status: SYNCHRONIZED"
    } elseif ($ahead -eq 0) {
        Write-Host "Status: LOCAL BEHIND"
    } elseif ($behind -eq 0) {
        Write-Host "Status: LOCAL AHEAD"
    } else {
        Write-Host "Status: DIVERGED"
    }
}

Write-Host ""
Write-Host "=== SYNC CHECK COMPLETE ==="

Pop-Location
