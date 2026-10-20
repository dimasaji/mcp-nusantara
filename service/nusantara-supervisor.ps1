param([switch]$Once)
. "$PSScriptRoot/local-services.ps1"
Initialize-LocalState
$mutex = New-Object Threading.Mutex($false, 'Global\NUSANTARA-V1-Supervisor')
$locked = $false
try {
    try { $locked = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { exit 0 }
    do {
        $monitor = Join-Path $script:StateDirectory 'monitor-state'
        if ((Test-Path $monitor) -and (Get-Content $monitor -Raw).Trim() -eq 'disabled') { break }
        $desired = Join-Path $script:StateDirectory 'desired-state'
        if ((Test-Path $desired) -and (Get-Content $desired -Raw).Trim() -eq 'stopped') { break }
        try {
            Invoke-WithLifecycleLock {
                # Recheck inside lock so explicit stop cannot race a monitor tick.
                if (-not (Test-Path $desired) -or (Get-Content $desired -Raw).Trim() -ne 'stopped') { Invoke-LocalStart }
            }
            $status = Get-LocalStatus
            $status | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $script:StateDirectory 'health.json') -Encoding UTF8
        } catch {
            # Capture a safe diagnostic, never credentials or response bodies.
            [pscustomobject]@{at=(Get-Date).ToUniversalTime().ToString('o');status='HOLD';errorType=$_.Exception.GetType().Name} |
                ConvertTo-Json | Add-Content (Join-Path $script:StateDirectory 'supervisor-errors.jsonl')
        }
        if (-not $Once) { Start-Sleep -Seconds $script:LocalConfig.monitorSeconds }
    } while (-not $Once)
} finally { if ($locked) { $mutex.ReleaseMutex() }; $mutex.Dispose() }
