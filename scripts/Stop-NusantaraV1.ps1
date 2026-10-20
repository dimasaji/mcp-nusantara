param([switch]$AllowStop)
& "$PSScriptRoot/../service/nusantara-service.ps1" stop -AllowStop:$AllowStop
