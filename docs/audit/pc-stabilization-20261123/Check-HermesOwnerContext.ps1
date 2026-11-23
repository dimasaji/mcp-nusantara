# Runs the existing initialize-only ACP probe. No authenticate or task execution.
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\dmaza\mcp-starter'
$taskOutput = Join-Path $repo '.tmp-build\pc-stabilization-20261123'
$previousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $repo 'backend'
    $raw = & (Join-Path $repo '.venv\Scripts\python.exe') -B -c 'import json; from app.developer_core.hermes_acp_connection import probe; print(json.dumps(probe()))'
    if ($LASTEXITCODE -ne 0) { throw 'Hermes probe process failed.' }
    $parsed = $raw | ConvertFrom-Json
    $principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
    $parsed | Add-Member -NotePropertyName elevated_administrator -NotePropertyValue ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) -Force
    $name = 'HERMES_OWNER_PROBE_' + [guid]::NewGuid().ToString('N') + '.json'
    New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
    $parsed | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskOutput $name) -Encoding UTF8
    $parsed | ConvertTo-Json -Depth 6
    Write-Output ('Saved: ' + (Join-Path $taskOutput $name))
} finally {
    $env:PYTHONPATH = $previousPythonPath
}
