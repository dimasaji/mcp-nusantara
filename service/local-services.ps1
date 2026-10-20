# Shared lifecycle implementation. Never reads .env; Uvicorn loads it privately.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:Repository = Split-Path $PSScriptRoot -Parent
$script:LocalConfig = Get-Content (Join-Path $script:Repository 'config/local-services.json') -Raw | ConvertFrom-Json
$script:StateDirectory = Join-Path $script:Repository 'data/service-v1'
if ($script:LocalConfig.host -ne '127.0.0.1' -or $script:LocalConfig.backendPort -ne 8000 -or $script:LocalConfig.frontendPort -ne 5180) {
    throw 'NCP-V1-AUTOSTART-001 requires loopback ports 8000 and 5180.'
}
function Initialize-LocalState {
    New-Item -ItemType Directory -Path $script:StateDirectory -Force | Out-Null
}
function Get-ServicePort([string]$Name) {
    if ($Name -eq 'backend') { return [int]$script:LocalConfig.backendPort }
    return [int]$script:LocalConfig.frontendPort
}
function Get-ServiceProcesses([string]$Name) {
    $port = Get-ServicePort $Name
    @(Get-CimInstance Win32_Process | Where-Object {
        $line = $_.CommandLine
        if (-not $line -or $line.IndexOf($script:Repository, [StringComparison]::OrdinalIgnoreCase) -lt 0) { return $false }
        if ($Name -eq 'backend') {
            $pythonCommand = '^"?' + [regex]::Escape((Join-Path $script:Repository '.venv\Scripts\python.exe')) + '"?\s+'
            return $_.Name -eq 'python.exe' -and $line -match $pythonCommand -and $line -match '\buvicorn\s+app\.main:app\b' -and
                $line -match ('--port\s+' + $port + '(\s|$)') -and $line -match '--host\s+127\.0\.0\.1(\s|$)'
        }
        $viteCommand = [regex]::Escape((Join-Path $script:Repository 'control-plane')) + '[\\/].*vite[\\/]bin[\\/]vite\.js'
        return $_.Name -eq 'node.exe' -and $line -match $viteCommand -and
            $line -match ('--port\s+' + $port + '(\s|$)') -and $line -match '--host\s+127\.0\.0\.1(\s|$)'
    })
}
function Get-PortListeners([int]$Port) {
    # Enumerate first: do not mistake permission/query failures for a free port.
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq $Port })
}
function Test-Http([string]$Uri) {
    try {
        $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -eq 200
    } catch { return $false }
}
function Get-LocalStatus {
    $items = @()
    foreach ($name in @('backend','frontend')) {
        $port = Get-ServicePort $name
        $owners = @(Get-ServiceProcesses $name)
        $ownerIds = @($owners | ForEach-Object { $_.ProcessId })
        $listeners = @(Get-PortListeners $port)
        $owned = $listeners.Count -gt 0
        foreach ($listener in $listeners) {
            if ($listener.LocalAddress -ne $script:LocalConfig.host -or $listener.OwningProcess -notin $ownerIds) { $owned = $false }
        }
        $path = if ($name -eq 'backend') { '/health' } else { '/' }
        $healthy = $owned -and (Test-Http "http://127.0.0.1:$port$path")
        $verdict = if ($healthy) { 'PASS' } elseif ($listeners.Count -or $owners.Count) { 'HOLD' } else { 'STOPPED' }
        $items += [pscustomobject]@{service=$name;port=$port;status=$verdict;owned=$owned;healthy=$healthy;pids=@($owners | ForEach-Object { $_.ProcessId })}
    }
    [pscustomobject]@{checkedAt=(Get-Date).ToUniversalTime().ToString('o');repository=$script:Repository;services=$items;
        proxyHealthy=(Test-Http "http://127.0.0.1:$($script:LocalConfig.frontendPort)/health");
        ollamaHealthy=(Test-Http "http://127.0.0.1:$($script:LocalConfig.ollamaPort)/api/version");ollamaMode=$script:LocalConfig.ollamaMode}
}
function Get-RuntimePaths {
    $saved = Join-Path $script:StateDirectory 'runtime.json'
    if (Test-Path $saved) { return Get-Content $saved -Raw | ConvertFrom-Json }
    $node = (Get-Command node.exe -ErrorAction Stop).Source
    [pscustomobject]@{python=(Join-Path $script:Repository '.venv/Scripts/python.exe');node=$node}
}
function Save-RuntimePaths {
    Initialize-LocalState
    $runtime = Get-RuntimePaths
    foreach ($binary in @($runtime.python,$runtime.node)) {
        if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw "Missing executable: $binary" }
    }
    $runtime | ConvertTo-Json | Set-Content (Join-Path $script:StateDirectory 'runtime.json') -Encoding UTF8
}
function Resume-LocalMonitor {
    $monitor = Join-Path $script:StateDirectory 'monitor-state'
    if ((Test-Path $monitor) -and (Get-Content $monitor -Raw).Trim() -eq 'enabled') {
        $task = Get-ScheduledTask -TaskName $script:LocalConfig.taskName -ErrorAction SilentlyContinue
        if ($task -and $task.State -ne 'Running') {
            $expected = Join-Path (Join-Path $script:Repository 'service') 'nusantara-supervisor.ps1'
            if (($task.Actions.Arguments -join ' ').Contains($expected)) { Start-ScheduledTask -TaskName $script:LocalConfig.taskName }
        }
    }
}
function Start-LocalService([string]$Name) {
    $port = Get-ServicePort $Name
    $owners = @(Get-ServiceProcesses $Name)
    $listeners = @(Get-PortListeners $port)
    if ($listeners.Count -or $owners.Count) {
        # Existing unhealthy, foreign, or initializing instances are never killed/replaced.
        return
    }
    $attemptFile = Join-Path $script:StateDirectory "$Name-attempts.json"
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $attempts = @()
    if (Test-Path $attemptFile) {
        $history = Get-Content $attemptFile -Raw | ConvertFrom-Json
        $attempts = @($history.starts | Where-Object { [long]$_ -gt ($now - $script:LocalConfig.recoveryWindowSeconds) })
    }
    if ($attempts.Count -ge $script:LocalConfig.maxStartsPerWindow) { Write-Warning "$Name recovery budget exhausted; cooldown active."; return }
    @{starts=@($attempts + $now)} | ConvertTo-Json -Depth 3 | Set-Content $attemptFile -Encoding UTF8
    $runtime = Get-RuntimePaths
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $env:HOST = $script:LocalConfig.host
    $env:PORT = [string]$script:LocalConfig.backendPort
    # PORT is the sole process-level alias; NUSANTARA_RUNTIME_PORT maps to the same field and causes ENV_ALIAS_CONFLICT.
    Remove-Item Env:NUSANTARA_RUNTIME_PORT -ErrorAction SilentlyContinue
    $env:NUSANTARA_BACKEND_URL = "http://127.0.0.1:$($script:LocalConfig.backendPort)"
    if ($Name -eq 'backend') {
        $binary = $runtime.python
        $arguments = "-B -m uvicorn app.main:app --host 127.0.0.1 --port $port --workers 1 --env-file .env"
        $directory = $script:Repository
    } else {
        $binary = $runtime.node
        $vite = Join-Path $script:Repository 'control-plane/node_modules/vite/bin/vite.js'
        $arguments = "`"$vite`" --host 127.0.0.1 --port $port --strictPort"
        $directory = Join-Path $script:Repository 'control-plane'
    }
    Start-Process -FilePath $binary -ArgumentList $arguments -WorkingDirectory $directory -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $script:StateDirectory "$Name-$stamp.log") `
        -RedirectStandardError (Join-Path $script:StateDirectory "$Name-$stamp.err.log") | Out-Null
}
function Invoke-LocalStart([switch]$NoOllama) {
    Initialize-LocalState
    # Ollama is managed by existing Windows Startup entries. Do not race or duplicate them.
    if (-not $NoOllama -and -not (Test-Http "http://127.0.0.1:$($script:LocalConfig.ollamaPort)/api/version")) {
        Write-Warning 'External Ollama is not ready. No additional instance will be created.'
    }
    foreach ($name in @('backend','frontend')) { Start-LocalService $name }
}
function Stop-LocalServices([switch]$AllowStop) {
    if (-not $AllowStop) { throw 'Stopping requires explicit permission: -AllowStop. Run status and verify PIDs first.' }
    Initialize-LocalState
    'stopped' | Set-Content (Join-Path $script:StateDirectory 'desired-state')
    foreach ($name in @('frontend','backend')) {
        foreach ($candidate in @(Get-ServiceProcesses $name)) {
            # Re-query ownership and creation time immediately before stopping (PID reuse protection).
            $verified = @(Get-ServiceProcesses $name | Where-Object { $_.ProcessId -eq $candidate.ProcessId -and $_.CreationDate -eq $candidate.CreationDate })
            if ($verified.Count -eq 1) { Stop-Process -Id $candidate.ProcessId -ErrorAction Stop }
        }
    }
    # Ollama is shared and is never stopped by NUSANTARA.
}
function Invoke-WithLifecycleLock([scriptblock]$Action) {
    $mutex = New-Object Threading.Mutex($false, 'Global\NUSANTARA-V1-Lifecycle')
    $locked = $false
    try {
        try { $locked = $mutex.WaitOne(30000) } catch [Threading.AbandonedMutexException] { $locked = $true }
        if (-not $locked) { throw 'Lifecycle operation already in progress.' }
        & $Action
    } finally { if ($locked) { $mutex.ReleaseMutex() }; $mutex.Dispose() }
}
