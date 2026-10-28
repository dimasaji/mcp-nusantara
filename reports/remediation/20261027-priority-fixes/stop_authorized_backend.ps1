param([int]$TargetPid = 3244, [int]$ExpectedParentPid = 9120)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$process = Get-CimInstance Win32_Process -Filter "ProcessId=$TargetPid"
$listener = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction Stop | Where-Object { $_.OwningProcess -eq $TargetPid })
$command = [string]$process.CommandLine
$checks = [ordered]@{
    processId = [int]$process.ProcessId
    processName = [string]$process.Name
    executable = [string]$process.ExecutablePath
    creationDate = [string]$process.CreationDate
    parentProcessId = [int]$process.ParentProcessId
    ownsPort8000 = ($listener.Count -gt 0)
    uvicornApp = ($command -match 'uvicorn\s+app\.main:app')
    loopbackHost = ($command -match '--host\s+127\.0\.0\.1')
    port8000Argument = ($command -match '--port\s+8000')
    parentMatchesPreviouslyObserved = ([int]$process.ParentProcessId -eq $ExpectedParentPid)
}
if ($process.Name -ne 'python.exe' -or -not $checks.ownsPort8000 -or -not $checks.uvicornApp -or -not $checks.loopbackHost -or -not $checks.port8000Argument) {
    throw 'PID identity/port checks failed; no process was stopped.'
}

# Recheck PID creation time and the port binding immediately before the one-PID stop.
$creation = $process.CreationDate
$current = Get-CimInstance Win32_Process -Filter "ProcessId=$TargetPid"
$currentListener = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction Stop | Where-Object { $_.OwningProcess -eq $TargetPid })
if ($current.CreationDate -ne $creation -or $currentListener.Count -eq 0) {
    throw 'PID identity or port ownership changed during verification; no process was stopped.'
}

[pscustomobject]$checks | ConvertTo-Json -Depth 4
Stop-Process -Id $TargetPid -ErrorAction Stop
Start-Sleep -Seconds 2
$stillRunning = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
$remainingListeners = @(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue)
$parentStillRunning = [bool](Get-Process -Id $ExpectedParentPid -ErrorAction SilentlyContinue)
[pscustomobject]@{
    stoppedPidStillRunning = [bool]$stillRunning
    port8000RemainingPids = @($remainingListeners | ForEach-Object { $_.OwningProcess })
    parentPid9120StillRunning = $parentStillRunning
} | ConvertTo-Json -Depth 4
if ($stillRunning) { throw "PID $TargetPid remains running after stop request." }
