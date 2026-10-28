param([switch]$AllowStop, [switch]$NoOllama)
$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/../service/nusantara-service.ps1" restart -AllowStop:$AllowStop -NoOllama:$NoOllama
exit $LASTEXITCODE
