$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path $PSScriptRoot
$root = Split-Path $scriptDir -Parent

Write-Host "=== NUSANTARA V1 RESTART ==="
& "$scriptDir\Stop-NusantaraV1.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Stop script exited with code $LASTEXITCODE. Continuing anyway."
}
Start-Sleep -Seconds 2
& "$scriptDir\Start-NusantaraV1.ps1" $args
exit $LASTEXITCODE