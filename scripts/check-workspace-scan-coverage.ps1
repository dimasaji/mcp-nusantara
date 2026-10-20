<#
.SYNOPSIS
    Regression test untuk BLK-ACL-REPORTS-001: pemindaian workspace harus deterministik.

.DESCRIPTION
    Beberapa direktori di workspace ini dimiliki akun sandbox yang sudah dihapus,
    sehingga DACL-nya menolak dibaca bahkan oleh proses unconfined non-elevated.
    Akibatnya `git status` melaporkan "Permission denied" dan `rg` gagal dengan
    exit 2, sehingga pengumpulan bukti tidak bisa dianggap lengkap.

    Perbaikan aksesnya masih BLOCKED (butuh elevate/Administrator). Yang dijaga
    skrip ini adalah mitigasinya: blok pengecualian terdokumentasi di .gitignore
    dan .graphifyignore. Jika blok itu terhapus, atau direktori orphan baru
    muncul, tes ini GAGAL.

    Rujukan: reports/ACL-EXCLUSION-BLK-ACL-REPORTS-001-20261015.md

.OUTPUTS
    exit 0 = PASS, exit 1 = FAIL.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot
)

$ErrorActionPreference = 'Continue'

# $PSScriptRoot tidak terisi saat default parameter dievaluasi di Windows PowerShell
# 5.1, jadi root repo ditentukan di badan skrip, bukan di blok param().
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $scriptDir = $PSScriptRoot
    if ([string]::IsNullOrWhiteSpace($scriptDir)) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
    $RepoRoot = if ([string]::IsNullOrWhiteSpace($scriptDir)) { (Get-Location).Path } else { Split-Path -Parent $scriptDir }
}
Push-Location $RepoRoot
try {
    $failures = [System.Collections.Generic.List[string]]::new()

    Write-Output "REPO  : $RepoRoot"
    Write-Output "HEAD  : $(git rev-parse HEAD)"

    # 1) git status tidak boleh gagal membaca direktori
    $status = git status --porcelain 2>&1
    $statusExit = $LASTEXITCODE
    $gitWarn = @($status | Where-Object { $_ -match 'Permission denied|could not open directory' })
    Write-Output "CHECK git status: exit=$statusExit warning-permission-denied=$($gitWarn.Count)"
    foreach ($line in $gitWarn) { Write-Output "      $line" }
    if ($statusExit -ne 0 -or $gitWarn.Count -gt 0) {
        $failures.Add("git status mengembalikan $($gitWarn.Count) warning Permission denied (exit $statusExit)")
    }

    # 2) ripgrep harus menelusuri seluruh workspace tanpa error akses
    $rg = Get-Command rg -ErrorAction SilentlyContinue
    if ($null -eq $rg) {
        Write-Output 'CHECK rg: DILEWATI (rg tidak ada di PATH)'
    } else {
        foreach ($mode in @(@(), @('--hidden'))) {
            $label = if ($mode.Count) { 'rg --files --hidden' } else { 'rg --files' }
            $out = & rg --files @mode . 2>&1
            $outExit = $LASTEXITCODE
            $accessErrors = @($out | Where-Object { $_ -match 'Access is denied|os error 5|Permission denied' })
            Write-Output "CHECK $label : exit=$outExit error-akses=$($accessErrors.Count)"
            foreach ($line in ($accessErrors | Select-Object -First 5)) { Write-Output "      $line" }
            if ($accessErrors.Count -gt 0) { $failures.Add("$label melaporkan $($accessErrors.Count) error akses") }
        }
    }

    # 3) blok pengecualian harus benar-benar ada di kedua file ignore
    foreach ($file in '.gitignore', '.graphifyignore') {
        if (-not (Test-Path -LiteralPath $file)) { $failures.Add("$file tidak ada"); continue }
        $entries = @(Get-Content -LiteralPath $file | Where-Object { $_ -match '^(reports|docs|control-plane|\.dev)/' })
        Write-Output "CHECK $file : $($entries.Count) entri pengecualian"
        if ($entries.Count -eq 0) {
            $failures.Add("$file kehilangan blok pengecualian BLK-ACL-REPORTS-001")
        }
    }

    Write-Output ''
    if ($failures.Count -gt 0) {
        Write-Output "RESULT: FAIL ($($failures.Count) masalah)"
        foreach ($f in $failures) { Write-Output "  - $f" }
        Write-Output 'Tindakan: pulihkan blok pengecualian, atau perbaiki izinnya dengan elevate.'
        exit 1
    }
    Write-Output 'RESULT: PASS - pemindaian workspace deterministik, tanpa error akses.'
    exit 0
} finally {
    Pop-Location
}
