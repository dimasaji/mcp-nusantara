param([int]$ProcessId = 3244)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId"
$parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($process.ParentProcessId)" -ErrorAction SilentlyContinue
foreach ($item in @($process,$parent)) {
    if (-not $item) { continue }
    $command = [string]$item.CommandLine
    [pscustomobject]@{
        pid = $item.ProcessId
        name = $item.Name
        executable = $item.ExecutablePath
        repoInCommand = $command.IndexOf($repo,[StringComparison]::OrdinalIgnoreCase) -ge 0
        venvInCommand = $command -match '\\.venv\\Scripts\\python\.exe'
        uvicornApp = $command -match 'uvicorn\s+app\.main:app'
        loopbackHost = $command -match '--host\s+127\.0\.0\.1'
        port8000 = $command -match '--port\s+8000'
        workers1 = $command -match '--workers\s+1'
        envFileFlag = $command -match '--env-file'
    }
}
