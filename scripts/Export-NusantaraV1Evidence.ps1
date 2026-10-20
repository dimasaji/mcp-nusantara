param([string]$EvidenceDirectory)
. "$PSScriptRoot/../service/local-services.ps1"
if (-not $EvidenceDirectory) { $EvidenceDirectory = Join-Path $script:Repository ('artifacts/NCP-V1-AUTOSTART-001/status-' + (Get-Date -Format yyyyMMdd-HHmmss)) }
New-Item -ItemType Directory -Path $EvidenceDirectory -Force | Out-Null
$task = Get-ScheduledTask -TaskName $script:LocalConfig.taskName -ErrorAction SilentlyContinue
$taskEvidence = @{installed=($null -ne $task);rebootVerification='HOLD'}
if ($task) {
    $info = Get-ScheduledTaskInfo -TaskName $script:LocalConfig.taskName -ErrorAction Stop
    $taskEvidence.name = $task.TaskName
    $taskEvidence.state = [string]$task.State
    $taskEvidence.user = $task.Principal.UserId
    $taskEvidence.runLevel = [string]$task.Principal.RunLevel
    $taskEvidence.logonType = [string]$task.Principal.LogonType
    $taskEvidence.lastRunTime = $info.LastRunTime.ToString('o')
    $taskEvidence.lastTaskResult = $info.LastTaskResult
    Export-ScheduledTask -TaskName $script:LocalConfig.taskName | Set-Content (Join-Path $EvidenceDirectory 'installed-task.xml') -Encoding Unicode
}
$boot = (Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).LastBootUpTime
$record = [pscustomobject]@{capturedAt=(Get-Date).ToUniversalTime().ToString('o');bootTime=$boot.ToUniversalTime().ToString('o');
    contract='NCP-V1-AUTOSTART-001';runtime=(Get-LocalStatus);task=$taskEvidence}
$record | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $EvidenceDirectory 'system.json') -Encoding UTF8
Write-Output (Join-Path $EvidenceDirectory 'system.json')
