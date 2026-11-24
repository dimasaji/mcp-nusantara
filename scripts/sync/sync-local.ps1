[CmdletBinding()]
param(
  [string]$Repo = (Get-Location).Path,
  [string]$Remote = "origin",
  [string]$Branch,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message, [int]$Code) {
  Write-Error $Message
  exit $Code
}

$inside = & git -C $Repo rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0 -or $inside -ne "true") {
  Fail "not a git repository: $Repo" 2
}

$current = & git -C $Repo rev-parse --abbrev-ref HEAD
if ($LASTEXITCODE -ne 0) {
  Fail "cannot resolve current branch" 2
}
if ([string]::IsNullOrWhiteSpace($Branch)) {
  $Branch = $current
}
if ($Branch -eq "HEAD") {
  Fail "detached HEAD is not supported" 2
}

$url = & git -C $Repo remote get-url $Remote 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($url)) {
  Fail "remote not configured: $Remote" 2
}
if ($url -notmatch "dimasaji/mcp-nusantara") {
  Fail "unexpected remote URL: $url" 2
}

$dirty = & git -C $Repo status --porcelain
if ($LASTEXITCODE -ne 0) {
  Fail "cannot read working tree status" 2
}
if ($dirty) {
  Fail "working tree is not clean" 2
}

$before = & git -C $Repo rev-parse HEAD
if ($LASTEXITCODE -ne 0) {
  Fail "cannot resolve local commit" 2
}

if ($DryRun) {
  Write-Output "DRY-RUN repo=$Repo remote=$Remote branch=$Branch before=$before"
  exit 0
}

& git -C $Repo fetch $Remote --prune
if ($LASTEXITCODE -ne 0) {
  Fail "fetch failed" 5
}

$ref = "$Remote/$Branch"
$remoteCommit = & git -C $Repo rev-parse --verify --quiet "refs/remotes/$ref"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteCommit)) {
  Fail "remote branch not found: $ref" 2
}

if ($before -eq $remoteCommit) {
  Write-Output "SYNCED repo=$Repo branch=$Branch commit=$before"
  exit 0
}

& git -C $Repo merge-base --is-ancestor $before $remoteCommit
if ($LASTEXITCODE -eq 0) {
  & git -C $Repo merge --ff-only $remoteCommit
  if ($LASTEXITCODE -ne 0) {
    Fail "fast-forward failed" 6
  }
  $after = & git -C $Repo rev-parse HEAD
  Write-Output "FAST-FORWARD branch=$Branch before=$before after=$after"
  exit 0
}

& git -C $Repo merge-base --is-ancestor $remoteCommit $before
if ($LASTEXITCODE -eq 0) {
  Fail "LOCAL_AHEAD branch=$Branch local=$before remote=$remoteCommit push requires approval" 3
}

Fail "DIVERGED branch=$Branch local=$before remote=$remoteCommit manual reconciliation required" 4
