param([switch]$PlanOnly)
# Installs the Windows Task Scheduler autostart. Requires an elevated (Administrator) PowerShell.
# Delegates to the existing installer; use -PlanOnly to review without registering anything.
$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/../service/install-nusantara-task.ps1" -PlanOnly:$PlanOnly
exit $LASTEXITCODE
