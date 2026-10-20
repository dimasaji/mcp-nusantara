# Nusantara-Git-Safe.ps1
# Safe Git audit and explicitly selected staging/commit/push for Nusantara.
# Default action is READ-ONLY. No reset, clean, checkout, pull, or force-push.
[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$RemoteName = "origin",
    [string[]]$StagePaths = @(),
    [string]$CommitMessage = "",
    [switch]$Fetch,
    [switch]$Stage,
    [switch]$Commit,
    [switch]$Push
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$GitArgs)
    & git -C $script:Root @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed (exit $LASTEXITCODE): git $($GitArgs -join ' ')"
    }
}

function Get-GitText {
    param([Parameter(Mandatory)][string[]]$GitArgs)
    $output = & git -C $script:Root @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed (exit $LASTEXITCODE): git $($GitArgs -join ' ')"
    }
    return (($output | Out-String).Trim())
}

$script:Root = (Resolve-Path -LiteralPath $RepoRoot).Path
$inside = Get-GitText -GitArgs @("rev-parse", "--show-toplevel")
if ([IO.Path]::GetFullPath($inside) -ne [IO.Path]::GetFullPath($script:Root)) {
    throw "RepoRoot must be the Git repository root. Detected root: $inside"
}

Write-Host "`n=== NUSANTARA GIT SAFE ===" -ForegroundColor Cyan
Write-Host "Repository : $script:Root"
Write-Host "Mode       : $(if ($Push) {'AUDIT + EXPLICIT STAGE/COMMIT/PUSH'} elseif ($Commit) {'AUDIT + EXPLICIT STAGE/COMMIT'} elseif ($Stage) {'AUDIT + EXPLICIT STAGE'} else {'READ-ONLY AUDIT'})"

$branch = Get-GitText -GitArgs @("branch", "--show-current")
$head = Get-GitText -GitArgs @("rev-parse", "HEAD")
$subject = Get-GitText -GitArgs @("log", "-1", "--format=%s")
$remoteUrl = Get-GitText -GitArgs @("remote", "get-url", $RemoteName)

Write-Host "`n--- Identity ---" -ForegroundColor Yellow
Write-Host "Branch     : $branch"
Write-Host "HEAD       : $head"
Write-Host "Last commit: $subject"
Write-Host "Remote     : $RemoteName -> $remoteUrl"

if ($Fetch) {
    Write-Host "`nFetching remote metadata only (does not merge or change working files)..." -ForegroundColor Yellow
    Invoke-Git -GitArgs @("fetch", $RemoteName)
}

Write-Host "`n--- Status ---" -ForegroundColor Yellow
Invoke-Git -GitArgs @("status", "--short", "--branch", "--untracked-files=all")

Write-Host "`n--- Tracked diff summary ---" -ForegroundColor Yellow
Invoke-Git -GitArgs @("--no-pager", "diff", "--stat")

Write-Host "`n--- Staged diff summary ---" -ForegroundColor Yellow
Invoke-Git -GitArgs @("--no-pager", "diff", "--cached", "--stat")

Write-Host "`n--- Whitespace check (tracked diff) ---" -ForegroundColor Yellow
& git -C $script:Root diff --check
$checkExit = $LASTEXITCODE
if ($checkExit -eq 0) {
    Write-Host "PASS: no diff --check findings." -ForegroundColor Green
} else {
    Write-Warning "git diff --check found issues. Review output above before committing."
}

$untrackedOutput = & git -C $script:Root ls-files --others --exclude-standard
if ($LASTEXITCODE -ne 0) { throw "Could not enumerate untracked files." }
$untracked = @($untrackedOutput | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
Write-Host "`nUntracked non-ignored file count: $($untracked.Count)"

if ($Commit -and -not $Stage) {
    throw "For safety, -Commit must be combined with -Stage and explicit -StagePaths."
}

if ($Stage -or $Commit -or $Push) {
    if (($Stage -or $Commit) -and $StagePaths.Count -eq 0) {
        throw "For safety, -Stage/-Commit/-Push requires explicit -StagePaths with individual file paths. No automatic 'git add .' is allowed."
    }

    $blockedExact = @(".", "..", "*", "**", "app", "tests", "scripts", "reports", "data", "backups")
    $blockedPattern = '(?i)(^|[\\/])\.env($|\.)|(^|[\\/])backups?([\\/]|$)|(^|[\\/])reports([\\/]|$)|\.bak([.-]|$)|\.tmp$|~$|\.pyc$|__pycache__'
    $validated = New-Object System.Collections.Generic.List[string]

    foreach ($candidate in $StagePaths) {
        $path = $candidate.Trim()
        if ([string]::IsNullOrWhiteSpace($path)) { throw "Empty StagePaths entry is not allowed." }
        if ($blockedExact -contains $path -or $path -match '^\.[\\/].*' -or $path -match '(^|[\\/])\.\.([\\/]|$)') {
            throw "Unsafe/broad path rejected: '$path'. Provide individual project files only."
        }
        if ($path -match $blockedPattern) {
            throw "Sensitive/temporary path rejected: '$path'. Do not stage secrets, backups, reports, temp files, or caches."
        }
        if ([IO.Path]::IsPathRooted($path)) {
            throw "Use repository-relative paths, not absolute paths: '$path'."
        }
        $full = [IO.Path]::GetFullPath((Join-Path $script:Root $path))
        if (-not $full.StartsWith($script:Root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Path escapes repository root: '$path'."
        }
        $validated.Add($path)
    }

    $validated = @($validated | Select-Object -Unique)
    Write-Host "`n--- Explicitly selected files ---" -ForegroundColor Yellow
    $validated | ForEach-Object { Write-Host "  $_" }

    if ($Stage) {
        foreach ($path in $validated) {
            Invoke-Git -GitArgs @("add", "--", $path)
        }
        Write-Host "`nSelected paths staged. Review the staged diff before committing." -ForegroundColor Green
        Invoke-Git -GitArgs @("--no-pager", "diff", "--cached", "--stat")
        Invoke-Git -GitArgs @("status", "--short")
    }

    if ($Commit) {
        if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
            throw "-Commit requires -CommitMessage."
        }
        $staged = Get-GitText -GitArgs @("diff", "--cached", "--name-only")
        if ([string]::IsNullOrWhiteSpace($staged)) {
            throw "No staged changes found. Use -Stage with explicit -StagePaths first."
        }
        Write-Host "`nAbout to create a local commit with the staged changes shown above." -ForegroundColor Yellow
        $confirmation = Read-Host "Type COMMIT to continue"
        if ($confirmation -cne "COMMIT") { throw "Commit cancelled by user." }
        Invoke-Git -GitArgs @("commit", "-m", $CommitMessage)
    }
}

if ($Push) {
    if ([string]::IsNullOrWhiteSpace($branch)) { throw "Detached HEAD detected; refusing to push." }
    Write-Host "`nAbout to push branch '$branch' to '$RemoteName' (no force push)." -ForegroundColor Yellow
    $confirmation = Read-Host "Type PUSH to continue"
    if ($confirmation -cne "PUSH") { throw "Push cancelled by user." }
    Invoke-Git -GitArgs @("push", $RemoteName, $branch)
}

Write-Host "`nCompleted. No reset, clean, checkout, pull, rebase, or force-push was performed." -ForegroundColor Green
