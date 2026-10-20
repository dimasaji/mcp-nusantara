param(
    [ValidateSet('start','stop','restart','status','health','run-backend','install-autostart','uninstall-autostart')]
    [string]$Action = 'status',
    [switch]$AllowStop,
    [switch]$NoOllama
)
. "$PSScriptRoot/local-services.ps1"
switch ($Action) {
    'run-backend' {
        # Foreground diagnostics use the same V1 executable/configuration. The
        # port guard prevents racing an existing service or foreign listener.
        $runtime = Get-RuntimePaths
        $port = [int]$script:LocalConfig.backendPort
        Invoke-WithLifecycleLock {
            if (@(Get-PortListeners $port).Count -or @(Get-ServiceProcesses 'backend').Count) {
                throw 'Backend already exists; refusing a duplicate foreground server.'
            }
        }
        $env:HOST = $script:LocalConfig.host
        $env:PORT = [string]$port
        Remove-Item Env:NUSANTARA_RUNTIME_PORT -ErrorAction SilentlyContinue
        Push-Location $script:Repository
        try {
            & $runtime.python -B -m uvicorn app.main:app --host 127.0.0.1 --port $port --workers 1 --env-file .env
            exit $LASTEXITCODE
        } finally { Pop-Location }
    }
    'status' { Get-LocalStatus | ConvertTo-Json -Depth 6 }
    'health' {
        $status = Get-LocalStatus
        $status | ConvertTo-Json -Depth 6
        if (@($status.services | Where-Object { -not $_.healthy }).Count -or -not $status.proxyHealthy -or (-not $NoOllama -and -not $status.ollamaHealthy)) { exit 1 }
    }
    'start' {
        Invoke-WithLifecycleLock {
            Initialize-LocalState
            'running' | Set-Content (Join-Path $script:StateDirectory 'desired-state')
            Invoke-LocalStart -NoOllama:$NoOllama
        }
        Resume-LocalMonitor
        $deadline = (Get-Date).AddSeconds($script:LocalConfig.startupTimeoutSeconds)
        do {
            $status = Get-LocalStatus
            if (@($status.services | Where-Object { -not $_.healthy }).Count -eq 0 -and $status.proxyHealthy) { break }
            Start-Sleep -Seconds 2
        } while ((Get-Date) -lt $deadline)
        $status | ConvertTo-Json -Depth 6
        if (@($status.services | Where-Object { -not $_.healthy }).Count -or -not $status.proxyHealthy) { exit 1 }
    }
    'stop' { Invoke-WithLifecycleLock { Stop-LocalServices -AllowStop:$AllowStop } }
    'restart' {
        Invoke-WithLifecycleLock {
            Stop-LocalServices -AllowStop:$AllowStop
            Start-Sleep -Seconds 2
            if (@(Get-ServiceProcesses 'backend').Count -or @(Get-ServiceProcesses 'frontend').Count) { throw 'Verified processes are still exiting; restart held.' }
            'running' | Set-Content (Join-Path $script:StateDirectory 'desired-state')
            Invoke-LocalStart -NoOllama:$NoOllama
        }
        & "$PSScriptRoot/nusantara-service.ps1" start -NoOllama:$NoOllama
    }
    'install-autostart' { & "$PSScriptRoot/install-nusantara-task.ps1" }
    'uninstall-autostart' { & "$PSScriptRoot/install-nusantara-task.ps1" -Uninstall }
}
