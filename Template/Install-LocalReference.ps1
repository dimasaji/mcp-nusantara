#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter()]
    [string]$RepoPath = 'C:\Users\dmaza\mcp-starter',
    [Parameter()]
    [ValidatePattern('^[a-zA-Z0-9_-]+$')]
    [string]$DestinationName = 'ncp-v1-ui-local-20261019'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-Payload {
    param([Parameter(Mandatory = $true)][string]$BasePath)
    $manifestFile = Join-Path $BasePath 'checksums.json'
    if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) {
        throw 'checksums.json tidak ditemukan. Ekstrak paket lengkap ke folder baru.'
    }
    $manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.format -ne 'nusantara-ui-local-v1') { throw 'Format paket tidak dikenali.' }
    $baseFull = [System.IO.Path]::GetFullPath($BasePath).TrimEnd('\', '/')
    $basePrefix = $baseFull + [System.IO.Path]::DirectorySeparatorChar
    foreach ($entry in $manifest.files) {
        $relative = [string]$entry.path
        if ([string]::IsNullOrWhiteSpace($relative) -or [System.IO.Path]::IsPathRooted($relative)) {
            throw 'Path payload tidak valid.'
        }
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $baseFull $relative))
        if (-not $candidate.StartsWith($basePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'Path payload keluar dari folder paket.'
        }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw ('Payload hilang: ' + $relative)
        }
        $actual = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash
        if ($actual -ne [string]$entry.sha256) { throw ('Hash tidak cocok: ' + $relative) }
    }
    return $manifest
}

$packageManifest = Test-Payload -BasePath $PSScriptRoot
if (-not (Test-Path -LiteralPath $RepoPath -PathType Container)) {
    throw 'Folder repo tidak ditemukan. Sesuaikan parameter -RepoPath.'
}
$repoFull = (Resolve-Path -LiteralPath $RepoPath).Path
$frontendPackage = Join-Path $repoFull 'control-plane\package.json'
if (-not (Test-Path -LiteralPath $frontendPackage -PathType Leaf)) {
    throw 'control-plane\package.json tidak ditemukan. Tidak ada berkas aplikasi yang diubah.'
}
$artifactsPath = Join-Path $repoFull 'artifacts'
if (Test-Path -LiteralPath $artifactsPath) {
    $item = Get-Item -LiteralPath $artifactsPath -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw 'Folder artifacts bukan direktori biasa. Pilih penempatan manual yang sesuai.'
    }
} else {
    New-Item -ItemType Directory -Path $artifactsPath | Out-Null
}
$destination = Join-Path $artifactsPath $DestinationName
if (Test-Path -LiteralPath $destination) {
    throw ('Tujuan sudah ada dan tidak ditimpa: ' + $destination + '. Gunakan -DestinationName dengan nama baru bila perlu.')
}

$stagePath = Join-Path $artifactsPath ('.ncp-ui-stage-' + [Guid]::NewGuid().ToString('N'))
try {
    New-Item -ItemType Directory -Path $stagePath | Out-Null
    foreach ($entry in $packageManifest.files) {
        $sourceFile = Join-Path $PSScriptRoot ([string]$entry.path)
        $targetFile = Join-Path $stagePath ([string]$entry.path)
        $targetParent = Split-Path -Parent $targetFile
        if (-not (Test-Path -LiteralPath $targetParent)) {
            New-Item -ItemType Directory -Path $targetParent | Out-Null
        }
        Copy-Item -LiteralPath $sourceFile -Destination $targetFile
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'checksums.json') -Destination (Join-Path $stagePath 'checksums.json')
    $null = Test-Payload -BasePath $stagePath
    Move-Item -LiteralPath $stagePath -Destination $destination
} catch {
    if (Test-Path -LiteralPath $stagePath) {
        Remove-Item -LiteralPath $stagePath -Recurse -Force
    }
    throw
}

Write-Host ''
Write-Host ('Paket referensi siap: ' + $destination) -ForegroundColor Green
Write-Host 'Frontend utama belum diubah. Tidak ada layanan, model, port, atau token yang diubah.'
Write-Host ''
Write-Host 'Buka Codex lokal pada repo ini, lalu tempel:' -ForegroundColor Cyan
Write-Host ('Baca artifacts/' + $DestinationName + '/INSTRUKSI-CODEX-LOKAL.md. Terapkan tampilan dashboard yang saya setujui ke Control Plane lokal yang sudah ada. Selesaikan implementasi, pengujian, verifikasi browser, evidence, dan handover dalam satu proses sesuai instruksi itu.')
