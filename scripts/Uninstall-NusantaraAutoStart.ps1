# Removes the Windows Task Scheduler autostart only. Does not touch app, data, or config.
# Requires an elevated (Administrator) PowerShell.
$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/../service/install-nusantara-task.ps1" -Uninstall
exit $LASTEXITCODE
