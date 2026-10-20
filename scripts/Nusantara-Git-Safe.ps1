#requires -Version 5.1
<#
.SYNOPSIS
    Safe Git operations for the Nusantara repository.
.DESCRIPTION
    Defaults to a read-only audit. Operations that modify Git state are explicit.
    Never runs reset, clean, checkout, pull, rebase, or force-push.
.EXAMPLE
    .\Nusantara-Git-Safe.ps1
.EXAMPLE
    .\Nusantara-Git-Safe.ps1 -Action Audit -Fetch
.EXAMPLE
    .\Nusantara-Git-Safe.ps1 -Action Stage -Paths "app/api/routes.py","tests/test_provider_identity.py"
.EXAMPLE
    .\Nusantara-Git-Safe.ps1 -Action Commit -Message "test: verify provider identity"
.EXAMPLE
    .\Nusantara-Git-Safe.ps1 -Action Push
#>
[CmdletBinding(SupportsShouldProcess = $false)]
param(
    [ValidateSet("Audit", "Fetch", "Stage", "Unstage", "Commit", "Push")]
    [string]$Action = "Audit",

    [string]$RepoRoot = (Get-Location).Path,

    [string]$Remote = "origin",

    [string[]]$Paths = @(),

    [string]$Message = "",

    [switch]$Fetch,

    [switch]$AllowProtectedFiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section {
    param([Parameter(Mandatory)][string]$Title)
    Write-Host ""
    Write-Host ("--- {0} ---" -f $Title) -ForegroundColor Cyan
}

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$GitArgs)
    & git -C $script:Repo @GitArgs
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw ("Git command failed (exit {0}): git {1}" -f $code, ($GitArgs -join " "))
    }
}

function Get-GitText {
    param([Parameter(Mandatory)][string[]]$GitArgs)
    $result = & git -C $script:Repo @GitArgs
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw ("Git command failed (exit {0}): git {1}" -f $code, ($GitArgs -join " "))
    }
    return (($result | Out-String).Trim())
}

function Confirm-Action {
    param(
        [Parameter(Mandatory)][string]$Prompt,
        [Parameter(Mandatory)][string]$Expected
    )
    $answer = Read-Host $Prompt
    if ($answer -cne $Expected) {
        throw "Action cancelled. Confirmation text did not match."
    }
}

function Test-RepoRelativePath {
    param([Parameter(Mandatory)][string]$Path)

    $p = $Path.Trim()
    if ([string]::IsNullOrWhiteSpace($p)) { throw "Empty path is not allowed." }
    if ([IO.Path]::IsPathRooted($p)) { throw "Use repository-relative paths only: $p" }
    if ($p -match '(^|[\\/])\.\.([\\/]|$)') { throw "Parent-directory paths are not allowed: $p" }
    if ($p -match '^[.][\\/]?$' -or $p -match '^[*?]') { throw "Broad/wildcard paths are not allowed: $p" }

    # Refuse secrets, caches, backups, generated artifacts, and temporary reports by default.
    $blocked = '(?i)(^|[\\/])\.env($|\.)|(^|[\\/])secrets?([\\/]|$)|(^|[\\/])backups?([\\/]|$)|(^|[\\/])reports([\\/]|$)|\.bak([.-]|$)|\.tmp$|\.pyc$|(^|[\\/])__pycache__([\\/]|$)|(^|[\\/])\.venv([\\/]|$)|(^|[\\/])venv([\\/]|$)'
    if (-not $AllowProtectedFiles -and $p -match $blocked) {
        throw "Protected/temporary path refused: $p. Review it separately; do not override casually."
    }

    $full = [IO.Path]::GetFullPath((Join-Path $script:Repo $p))
    $rootWithSep = $script:Repo.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($rootWithSep, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes repository root: $p"
    }

    return $p
}

# Resolve and verify repository root.
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git executable not found. Install Git for Windows or fix PATH."
}
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
    throw "Repository directory does not exist: $RepoRoot"
}
$script:Repo = (Resolve-Path -LiteralPath $RepoRoot).Path
$repoTop = Get-GitText -GitArgs @("rev-parse", "--show-toplevel")
$repoTopFull = [IO.Path]::GetFullPath($repoTop).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
$repoArgFull = [IO.Path]::GetFullPath($script:Repo).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
if (-not $repoTopFull.Equals($repoArgFull, [StringComparison]::OrdinalIgnoreCase)) {
    throw "RepoRoot must be the repository root. Git detected: $repoTop"
}

$branch = Get-GitText -GitArgs @("branch", "--show-current")
if ([string]::IsNullOrWhiteSpace($branch)) {
    throw "Detached HEAD detected. Refusing branch-sensitive operation."
}
$head = Get-GitText -GitArgs @("rev-parse", "HEAD")
$subject = Get-GitText -GitArgs @("log", "-1", "--format=%s")

$remoteUrl = Get-GitText -GitArgs @("remote", "get-url", $Remote)
$remotePushUrl = Get-GitText -GitArgs @("remote", "get-url", "--push", $Remote)

Write-Host "NUSANTARA GIT SAFE" -ForegroundColor Green
Write-Host ("Repository : {0}" -f $script:Repo)
Write-Host ("Action     : {0}" -f $Action)
Write-Host ("Branch     : {0}" -f $branch)
Write-Host ("HEAD       : {0}" -f $head)
Write-Host ("Last commit: {0}" -f $subject)
Write-Host ("Remote URL : {0}" -f $remoteUrl)
if ($remotePushUrl -ne $remoteUrl) {
    Write-Warning "Push URL differs from fetch URL: $remotePushUrl"
}

if ($Fetch -and $Action -ne "Fetch") {
    Write-Warning "-Fetch requested: only remote metadata will be fetched; no merge/rebase occurs."
    Invoke-Git -GitArgs @("fetch", $Remote)
}

switch ($Action) {
    "Audit" {
        Write-Section "Working tree"
        Invoke-Git -GitArgs @("status", "--short", "--branch", "--untracked-files=all")

        Write-Section "Unstaged tracked diff"
        Invoke-Git -GitArgs @("--no-pager", "diff", "--stat")

        Write-Section "Staged diff"
        Invoke-Git -GitArgs @("--no-pager", "diff", "--cached", "--stat")

        Write-Section "Whitespace check"
        & git -C $script:Repo diff --check
        $checkCode = $LASTEXITCODE
        if ($checkCode -eq 0) {
            Write-Host "PASS: no tracked-diff whitespace findings." -ForegroundColor Green
        } else {
            Write-Warning "git diff --check found findings. Review before commit."
        }

        Write-Section "Remote tracking status"
        $upstream = & git -C $script:Repo rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>$null
        if ($LASTEXITCODE -eq 0 -and $upstream) {
            Write-Host ("Upstream: {0}" -f (($upstream | Out-String).Trim()))
            Invoke-Git -GitArgs @("rev-list", "--left-right", "--count", ("HEAD...{0}" -f (($upstream | Out-String).Trim())))
        } else {
            Write-Host "No upstream configured for this branch. This is not necessarily an error."
        }

        Write-Section "Audit complete"
        Write-Host "Audit is read-only, except when -Fetch is supplied."
    }

    "Fetch" {
        Write-Section "Fetch remote metadata"
        Invoke-Git -GitArgs @("fetch", $Remote)
        Write-Host "Fetch complete. No files were merged into the working tree." -ForegroundColor Green
        Invoke-Git -GitArgs @("status", "--short", "--branch")
    }

    "Stage" {
        if ($Paths.Count -eq 0) {
            throw "Stage requires explicit individual paths via -Paths. 'git add .' is intentionally not supported."
        }
        $validated = @($Paths | ForEach-Object { Test-RepoRelativePath -Path $_ } | Select-Object -Unique)
        Write-Section "Paths selected for staging"
        $validated | ForEach-Object { Write-Host ("  {0}" -f $_) }
        Confirm-Action -Prompt "Type STAGE to stage only these paths" -Expected "STAGE"
        foreach ($p in $validated) {
            Invoke-Git -GitArgs @("add", "--", $p)
        }
        Write-Section "Staged result"
        Invoke-Git -GitArgs @("--no-pager", "diff", "--cached", "--stat")
        Invoke-Git -GitArgs @("status", "--short")
        Write-Host "Review the full staged diff before committing." -ForegroundColor Yellow
    }

    "Unstage" {
        if ($Paths.Count -eq 0) {
            throw "Unstage requires explicit paths via -Paths."
        }
        $validated = @($Paths | ForEach-Object { Test-RepoRelativePath -Path $_ } | Select-Object -Unique)
        Write-Section "Paths selected for unstaging"
        $validated | ForEach-Object { Write-Host ("  {0}" -f $_) }
        Confirm-Action -Prompt "Type UNSTAGE to unstage only these paths (working files remain unchanged)" -Expected "UNSTAGE"
        foreach ($p in $validated) {
            Invoke-Git -GitArgs @("restore", "--staged", "--", $p)
        }
        Invoke-Git -GitArgs @("status", "--short")
    }

    "Commit" {
        if ([string]::IsNullOrWhiteSpace($Message)) {
            throw "Commit requires -Message."
        }
        $stagedNames = Get-GitText -GitArgs @("diff", "--cached", "--name-only")
        if ([string]::IsNullOrWhiteSpace($stagedNames)) {
            throw "Nothing is staged. Run Stage with explicit paths first."
        }
        Write-Section "Review staged summary"
        Invoke-Git -GitArgs @("--no-pager", "diff", "--cached", "--stat")
        Write-Host "`nStaged file names:"
        $stagedNames -split "`r?`n" | ForEach-Object { Write-Host ("  {0}" -f $_) }
        Confirm-Action -Prompt "Type COMMIT to create a local commit from the staged snapshot" -Expected "COMMIT"
        Invoke-Git -GitArgs @("commit", "-m", $Message)
        Write-Host "Local commit created. Push is a separate explicit action." -ForegroundColor Green
    }

    "Push" {
        # Avoid accidentally pushing staged/unstaged/untracked work as if it were committed.
        $status = Get-GitText -GitArgs @("status", "--porcelain", "--untracked-files=all")
        if (-not [string]::IsNullOrWhiteSpace($status)) {
            Write-Warning "Working tree is not clean. Uncommitted changes will not be pushed, but review them before proceeding."
            Write-Host $status
            Confirm-Action -Prompt "Type PUSH-COMMITTED-ONLY to push existing commits only" -Expected "PUSH-COMMITTED-ONLY"
        } else {
            Confirm-Action -Prompt "Type PUSH to push branch '$branch' to '$Remote' (no force push)" -Expected "PUSH"
        }

        # Fetch first to prevent an accidental non-fast-forward attempt; does not merge.
        Invoke-Git -GitArgs @("fetch", $Remote)
        $remoteRef = "{0}/{1}" -f $Remote, $branch
        $remoteExists = & git -C $script:Repo show-ref --verify --quiet ("refs/remotes/{0}" -f $remoteRef)
        if ($LASTEXITCODE -eq 0) {
            $counts = Get-GitText -GitArgs @("rev-list", "--left-right", "--count", ("{0}...{1}" -f $remoteRef, "HEAD"))
            $parts = $counts -split '\s+'
            if ($parts.Count -ge 2 -and [int]$parts[0] -gt 0) {
                throw "Remote branch has commits absent locally. Push refused to avoid overwriting remote history. Review divergence manually; no merge/rebase was performed."
            }
        } else {
            Write-Warning "Remote branch $remoteRef was not found; this may be the first push."
        }

        Invoke-Git -GitArgs @("push", $Remote, $branch)
        Write-Host "Push complete." -ForegroundColor Green
        Invoke-Git -GitArgs @("status", "--short", "--branch")
    }
}

Write-Host "`nFinished. No reset, clean, checkout, pull, rebase, or force-push was run." -ForegroundColor Green
