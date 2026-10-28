param([int]$Port = 5180)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop)
$results = foreach ($listener in $listeners) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($process.ParentProcessId)" -ErrorAction SilentlyContinue
    $command = [string]$process.CommandLine
    [pscustomobject]@{
        port = $Port
        localAddress = $listener.LocalAddress
        pid = $process.ProcessId
        parentPid = $process.ParentProcessId
        parentName = $parent.Name
        name = $process.Name
        executable = $process.ExecutablePath
        commandMentionsRepo = $command.IndexOf($repo,[StringComparison]::OrdinalIgnoreCase) -ge 0
        viteEntrypoint = $command -match 'control-plane[\\/]node_modules[\\/]vite[\\/]bin[\\/]vite\.js'
        hostLoopback = $command -match '--host\s+127\.0\.0\.1'
        port5180 = $command -match '--port\s+5180'
        startedAt = $process.CreationDate
    }
}
@($results) | ConvertTo-Json -Depth 4
