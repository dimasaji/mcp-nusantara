param(
    [Parameter(Mandatory=$true)]
    [string]$InputPath,

    [Parameter(Mandatory=$false)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$Root = "C:\Users\dmaza\mcp-starter"
$Python = Join-Path $Root "tools\markitdown\.venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "MarkItDown belum terpasang. Jalankan setup terlebih dahulu."
}

if (-not (Test-Path $InputPath)) {
    throw "File input tidak ditemukan: $InputPath"
}

$InputFull = (Resolve-Path $InputPath).Path

if ($OutputPath) {
    $OutputFull = [System.IO.Path]::GetFullPath(
        (Join-Path (Get-Location).Path $OutputPath)
    )
    $OutputDir = Split-Path $OutputFull -Parent
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

    $Result = & $Python -m markitdown $InputFull
    if ($LASTEXITCODE -ne 0) {
        throw "Konversi gagal. Periksa format file dan pesan error."
    }

    $Result | Set-Content -LiteralPath $OutputFull -Encoding utf8
    Write-Host "Markdown tersimpan: $OutputFull" -ForegroundColor Green
} else {
    & $Python -m markitdown $InputFull
    if ($LASTEXITCODE -ne 0) {
        throw "Konversi gagal."
    }
}
