$ErrorActionPreference = "Stop"

$ROOT = "C:\Users\dmaza\mcp-starter"
$SUPERVISOR = "$ROOT\service\nusantara-supervisor.ps1"
$TASKNAME = "Nusantara AI Service"

$PowerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

Write-Host ""
Write-Host "=========================================="
Write-Host " INSTALL NUSANTARA AI SERVICE"
Write-Host "=========================================="
Write-Host ""

if (-not (Test-Path $SUPERVISOR)) {
    Write-Host "ERROR: Supervisor tidak ditemukan:"
    Write-Host $SUPERVISOR
    exit 1
}

$Action = New-ScheduledTaskAction `
    -Execute $PowerShell `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$SUPERVISOR`""

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask `
    -TaskName $TASKNAME `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Force | Out-Null

Write-Host ""
Write-Host "TASK BERHASIL DIPASANG"
Write-Host "Nama    : $TASKNAME"
Write-Host "Trigger : Saat Windows Login"
Write-Host ""

Start-ScheduledTask -TaskName $TASKNAME

Write-Host "Nusantara AI Service sedang dijalankan..."
Write-Host ""