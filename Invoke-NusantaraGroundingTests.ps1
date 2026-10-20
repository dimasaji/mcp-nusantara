[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

try {
    $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
} catch {
    Write-Error "Folder repository tidak ditemukan: $RepoRoot"
    exit 2
}

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot "pyproject.toml"))) {
    Write-Error "pyproject.toml tidak ditemukan. Jalankan script dari root repo atau gunakan -RepoRoot."
    exit 2
}

$groundingFile = Join-Path $RepoRoot "app\knowledge\grounding.py"
$agentFile = Join-Path $RepoRoot "app\hermes\agent.py"
$conversationTest = Join-Path $RepoRoot "tests\test_hermes_v1_conversation.py"

foreach ($requiredFile in @($groundingFile, $agentFile, $conversationTest)) {
    if (-not (Test-Path -LiteralPath $requiredFile)) {
        Write-Error "File wajib tidak ditemukan: $requiredFile"
        exit 2
    }
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportDir = Join-Path $RepoRoot "artifacts\grounding\$timestamp"
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$reportPath = Join-Path $reportDir "grounding-test-report.txt"

# Run existing focused tests. This script does not modify application source.
$testFiles = @($conversationTest)

$dedicatedTests = Get-ChildItem -LiteralPath (Join-Path $RepoRoot "tests") `
    -Recurse -File -Filter "*grounding*.py" |
    Where-Object { $_.FullName -ne $conversationTest } |
    Sort-Object FullName

foreach ($test in $dedicatedTests) {
    $testFiles += $test.FullName
}
$testFiles = $testFiles | Select-Object -Unique

$pythonVersion = & python --version 2>&1
$header = @(
    "NUSANTARA V1 - GROUNDING TEST RUN"
    "Waktu      : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
    "Repository : $RepoRoot"
    "Python     : $pythonVersion"
    "Test files :"
)
$header += $testFiles | ForEach-Object { "  - $_" }
$header += @(
    ""
    "Catatan: script ini hanya menjalankan tes; tidak mengubah kode aplikasi."
    "------------------------------------------------------------"
    ""
)

$header | Set-Content -LiteralPath $reportPath -Encoding UTF8
$header | ForEach-Object { Write-Host $_ }

Push-Location $RepoRoot
try {
    & python -m pytest @testFiles -q 2>&1 |
        Tee-Object -FilePath $reportPath -Append
    $pytestExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($pytestExitCode -eq 0) {
    $summary = "HASIL: PASS - pytest selesai tanpa kegagalan."
    Write-Host "`n$summary" -ForegroundColor Green
} else {
    $summary = "HASIL: FAIL - pytest exit code $pytestExitCode. Periksa laporan."
    Write-Host "`n$summary" -ForegroundColor Red
}
$summary | Add-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host "Laporan: $reportPath"
exit $pytestExitCode
