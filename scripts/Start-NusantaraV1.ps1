param([switch]$NoOllama)
& "$PSScriptRoot/../service/nusantara-service.ps1" start -NoOllama:$NoOllama
exit $LASTEXITCODE
