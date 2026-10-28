param(
    [string]$Repository = 'C:\Users\dmaza\mcp-starter',
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$python = Join-Path $Repository '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Python backend tidak ditemukan.' }
$installer = Join-Path $PSScriptRoot 'install_patch.py'
if ($Apply) {
    & $python $installer --root $Repository --apply
} else {
    & $python $installer --root $Repository
}
if ($LASTEXITCODE -ne 0) { throw 'Patch dihentikan. Jangan paksa overwrite.' }
