$ErrorActionPreference = "Continue"

$ROOT = "C:\Users\dmaza\mcp-starter"
$VENV = "$ROOT\.venv\Scripts\python.exe"
$LOGDIR = "$ROOT\data\logs"

New-Item -ItemType Directory -Path $LOGDIR -Force | Out-Null

$CORE_LOG = "$LOGDIR\nusantara-core.log"
$SUP_LOG  = "$LOGDIR\nusantara-supervisor.log"

function Write-Log($Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $SUP_LOG -Value "[$timestamp] $Message"
}

function Test-Port($Port) {
    $connection = Get-NetTCPConnection `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction SilentlyContinue

    return ($null -ne $connection)
}

function Start-Ollama {

    if (Test-Port 11434) {
        Write-Log "Ollama sudah berjalan."
        return
    }

    Write-Log "Memulai Ollama..."

    Start-Process `
        -FilePath "ollama" `
        -ArgumentList "serve" `
        -WindowStyle Hidden

    $timeout = 30

    while ($timeout -gt 0) {

        Start-Sleep -Seconds 1

        if (Test-Port 11434) {
            Write-Log "Ollama berhasil berjalan."
            return
        }

        $timeout--
    }

    Write-Log "ERROR: Ollama gagal start."
}

function Start-Nusantara {

    if (Test-Port 8000) {
        Write-Log "Nusantara Core sudah berjalan."
        return
    }

    Write-Log "Memulai Nusantara Core..."

    Start-Process `
        -FilePath $VENV `
        -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" `
        -WorkingDirectory $ROOT `
        -RedirectStandardOutput $CORE_LOG `
        -RedirectStandardError $CORE_LOG `
        -WindowStyle Hidden

    $timeout = 30

    while ($timeout -gt 0) {

        Start-Sleep -Seconds 1

        if (Test-Port 8000) {
            Write-Log "Nusantara Core berhasil berjalan."
            return
        }

        $timeout--
    }

    Write-Log "ERROR: Nusantara Core gagal start."
}

Write-Log "=========================================="
Write-Log "NUSANTARA AI SUPERVISOR START"
Write-Log "=========================================="

while ($true) {

    Start-Ollama
    Start-Nusantara

    if (-not (Test-Port 8000)) {
        Write-Log "Nusantara Core tidak aktif. Akan dicoba kembali."
    }

    Start-Sleep -Seconds 10
}