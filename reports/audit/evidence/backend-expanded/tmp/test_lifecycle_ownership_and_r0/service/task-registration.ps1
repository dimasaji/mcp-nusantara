param([switch]$Uninstall, [switch]$PlanOnly, [System.Management.Automation.PSCredential]$Credential)
. "$PSScriptRoot/local-services.ps1"
$name = $script:LocalConfig.taskName
$supervisor = Join-Path $PSScriptRoot 'nusantara-supervisor.ps1'
$shell = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
$arguments = "-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$supervisor`""
$existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($existing) {
    if (@($existing.Actions).Count -ne 1 -or $existing.Actions[0].Execute -ne $shell -or $existing.Actions[0].Arguments -ne $arguments) {
        throw 'Task name conflict: existing task is not owned by this repository. Nothing changed.'
    }
}
if ($Uninstall) {
    if ($PlanOnly) { Write-Output "Would unregister owned task: $name"; return }
    Initialize-LocalState
    'disabled' | Set-Content (Join-Path $script:StateDirectory 'monitor-state')
    if ($existing) { Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction Stop }
    Write-Output 'Autostart removed; existing Backend, Frontend and Ollama left running.'
    return
}
$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
if ($Credential) { $user = $Credential.UserName }
$action = New-ScheduledTaskAction -Execute $shell -Argument $arguments -WorkingDirectory $script:Repository
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = 'PT45S'
# Passwordless noninteractive local logon, user token, never SYSTEM/Highest.
$logonType = if ($Credential) { 'Password' } else { 'S4U' }
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType $logonType -RunLevel Limited
if ($existing -and ($existing.Principal.LogonType -ne $logonType -or $existing.Principal.RunLevel -ne 'Limited')) {
    throw 'Existing owned task has a different logon policy. Explicit uninstall/reinstall is required.'
}
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
    -Description 'NCP-V1-AUTOSTART-001: repository-owned fixed-port services; no automatic process termination.'
Initialize-LocalState
$xml = Export-ScheduledTask -InputObject $task
$xml | Set-Content (Join-Path $script:StateDirectory 'autostart-plan.xml') -Encoding Unicode
if ($PlanOnly) { Write-Output (Join-Path $script:StateDirectory 'autostart-plan.xml'); return }
# Do not silently enable a second legacy supervisor.
$conflicts = @(Get-ScheduledTask | Where-Object {
    $commands = @($_.Actions | ForEach-Object {
        if ($_.PSObject.Properties['Arguments']) { [string]$_.Arguments }
    }) -join ' '
    $_.TaskName -ne $name -and $_.State -ne 'Disabled' -and
    ($commands -match 'nusantara-supervisor|nusantara-service|Start-NusantaraV1')
})
if ($conflicts.Count) { throw 'Another enabled NUSANTARA startup task exists; migration requires explicit owner approval.' }
Save-RuntimePaths
if (-not $existing) {
    if ($Credential) {
        # Supplied only by the installing human. Never serialize credentials into repo/evidence.
        Register-ScheduledTask -TaskName $name -InputObject $task -User $user -Password $Credential.GetNetworkCredential().Password -ErrorAction Stop | Out-Null
    } else {
        Register-ScheduledTask -TaskName $name -InputObject $task -ErrorAction Stop | Out-Null
    }
}
'enabled' | Set-Content (Join-Path $script:StateDirectory 'monitor-state')
'running' | Set-Content (Join-Path $script:StateDirectory 'desired-state')
Start-ScheduledTask -TaskName $name -ErrorAction Stop
Get-ScheduledTask -TaskName $name -ErrorAction Stop | Select-Object TaskName,State,@{n='RunLevel';e={$_.Principal.RunLevel}},@{n='LogonType';e={$_.Principal.LogonType}}
