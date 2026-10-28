$ErrorActionPreference = "SilentlyContinue"

$ROOT = "C:\Users\dmaza\mcp-starter"
$VENV = "$ROOT\.venv\Scripts\python.exe"
$LOGDIR = "$ROOT\data\logs"
$PIDFILE = "$ROOT\data\nusantara-core.pid"
$PORT = 8000

New-Item -ItemType Directory -Path $LOGDIR -Force | Out-Null

function Get-NusantaraProcesses {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match 'uvicorn.*app\.main:app.*--port 8000'
        }
}

function Is-PortOpen($Port) {
    return $null -ne (
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    )
}

function Stop-Nusantara {

    Write-Host "Stopping Nusantara Core..."

    $processes = @(Get-NusantaraProcesses)

    foreach ($p in $processes) {
        Write-Host "Stopping Uvicorn PID: $($p.ProcessId)"
        Stop-Process -Id ([int]$p.ProcessId) -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $PIDFILE) {
        Remove-Item $PIDFILE -Force -ErrorAction SilentlyContinue
    }

    for ($i = 1; $i -le 10; $i++) {
        $remaining = @(Get-NusantaraProcesses)

        if ($remaining.Count -eq 0 -and -not (Is-PortOpen $PORT)) {
            break
        }

        Start-Sleep -Milliseconds 500
    }

    # Final cleanup berdasarkan port
    $owners = @(
        Get-NetTCPConnection -LocalPort $PORT -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    )

    foreach ($owner in $owners) {
        Stop-Process -Id ([int]$owner) -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep 1

    Write-Host "Nusantara Core stopped."
}

function Start-Nusantara {

    Write-Host "Starting Ollama..."

    if (-not (Is-PortOpen 11434)) {
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep 3
    }

    # HARD CLEAN: jangan pernah start jika ada instance lama
    $existing = @(Get-NusantaraProcesses)

    if ($existing.Count -gt 0 -or (Is-PortOpen $PORT)) {
        Write-Host "Existing Nusantara instance detected. Cleaning..."

        Stop-Nusantara

        Start-Sleep 1
    }

    Write-Host "Starting Nusantara Core..."

    $process = Start-Process `
        -FilePath $VENV `
        -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1" `
        -WorkingDirectory $ROOT `
        -RedirectStandardOutput "$LOGDIR\nusantara-core.log" `
        -RedirectStandardError "$LOGDIR\nusantara-core-error.log" `
        -PassThru `
        -WindowStyle Hidden

    $process.Id | Set-Content $PIDFILE

    Write-Host "PID: $($process.Id)"

    for ($i = 1; $i -le 30; $i++) {

        Start-Sleep 1

        $running = @(Get-NusantaraProcesses)

        if ((Is-PortOpen $PORT) -and $running.Count -ge 1) {

            $final = @(Get-NusantaraProcesses)

            Write-Host ""
            Write-Host "NUSANTARA AI RUNNING"
            Write-Host "PID: $($process.Id)"
            Write-Host "http://127.0.0.1:8000"
            Write-Host "http://127.0.0.1:8000/docs"

            return
        }
    }

    Write-Host "ERROR: Nusantara Core gagal start."
}

function Status-Nusantara {

    Write-Host ""
    Write-Host "=========================================="
    Write-Host "       NUSANTARA AI STATUS"
    Write-Host "=========================================="
    Write-Host ""

    if (Is-PortOpen 11434) {
        Write-Host "Ollama         : RUNNING"
    }
    else {
        Write-Host "Ollama         : STOPPED"
    }

    $processes = @(Get-NusantaraProcesses)

    if (Is-PortOpen $PORT) {
        Write-Host "Nusantara Core : RUNNING"
        Write-Host "Uvicorn count  : $($processes.Count)"
    }
    else {
        Write-Host "Nusantara Core : STOPPED"
    }

    Write-Host ""
}

switch ($args[0]) {

    "start" {
        Start-Nusantara
    }

    "stop" {
        Stop-Nusantara
    }

    "restart" {
        Stop-Nusantara
        Start-Sleep 2
        Start-Nusantara
    }

    "status" {
        Status-Nusantara
    }

    default {
        Write-Host "Usage:"
        Write-Host "  nusantara-service.ps1 start"
        Write-Host "  nusantara-service.ps1 stop"
        Write-Host "  nusantara-service.ps1 restart"
        Write-Host "  nusantara-service.ps1 status"
    }
}

