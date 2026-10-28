param($Action,[switch]$AllowStop,[switch]$NoOllama)
@{action=$Action;allowStop=[bool]$AllowStop;noOllama=[bool]$NoOllama} | ConvertTo-Json | Set-Content "$PSScriptRoot/probe.json"
exit 7
