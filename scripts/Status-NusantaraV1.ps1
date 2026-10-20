$ErrorActionPreference = 'Stop'
# Read-only: delegates to the existing service owner. No state is changed.
& "$PSScriptRoot/../service/nusantara-service.ps1" -Action status
exit $LASTEXITCODE
