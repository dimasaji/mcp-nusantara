<#
.SYNOPSIS
    OpenWebUI Autopilot Setup - Start Ollama + OpenWebUI + verify login
.DESCRIPTION
    Melakukan:
    1. Cek Ollama running (port 11434)
    2. Start OpenWebUI dengan admin account
    3. Verify login berhasil
.NOTES
    Jalankan di Windows PowerShell (bukan bash)
#>

# ========== CONFIG ==========
$OWUI_HOME = "C:\Users\dmaza\AppData\Roaming\Python\Python311\Scripts"
$OWUI_PYTHON = "C:\Users\dmaza\AppData\Local\Programs\Python\Python311\python.exe"
$OWUI_EXE = "$OWUI_HOME\open-webui.exe"
$OWUI_PORT = 8080
$OWUI_EMAIL = "admin@admin.com"
$OWUI_PASSWORD = "admin123"
$OWUI_SECRET = [Convert]::ToBase64String([System.GUID]::NewGuid().ToByteArray())
# ===========================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OpenWebUI Autopilot Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ========== STEP 1: Cek Ollama ==========
Write-Host "`n[1] Checking Ollama..."
$ollama = Invoke-RestMethod "http://localhost:11434/api/tags" -ErrorAction SilentlyContinue
if ($ollama -and $ollama.models) {
    Write-Host "   OK: Ollama berjalan" -ForegroundColor Green
    $model = $ollama.models | Where-Object { $_.name -like "*llama3.2*" }
    if ($model) {
        Write-Host "   Model: $($model.name) ($(Format-HumanSize $model.size))" -ForegroundColor Green
    }
} else {
    Write-Host "   WARNING: Ollama tidak terdeteksi" -ForegroundColor Yellow
    Write-Host "   Mulai Ollama..."
    Start-Process "C:\Users\dmaza\AppData\Local\Programs\Ollama\ollama.exe" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
    $ollama = Invoke-RestMethod "http://localhost:11434/api/tags" -ErrorAction SilentlyContinue
    if ($ollama -and $ollama.models) {
        Write-Host "   OK: Ollama berjalan" -ForegroundColor Green
    } else {
        Write-Host "   ERROR: Ollama tidak berjalan" -ForegroundColor Red
    }
}

# ========== STEP 2: Stop & reset existing OpenWebUI ==========
Write-Host "`n[2] Preparing OpenWebUI..."
Stop-Process -Name "open-webui" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

$dbPath = "C:\Users\dmaza\AppData\Roaming\Python\Python311\Scripts\open-webui.exe.db"
$secretPath = "C:\Users\dmaza\.webui_secret_key"
if (Test-Path $dbPath) { Remove-Item $dbPath -Force; Write-Host "   Deleted $dbPath" }
if (Test-Path $secretPath) { Remove-Item $secretPath -Force; Write-Host "   Deleted $secretPath" }

# ========== STEP 3: Start OpenWebUI ==========
Write-Host "`n[3] Starting OpenWebUI..."
$env:WEBUI_ADMIN_EMAIL = $OWUI_EMAIL
$env:WEBUI_ADMIN_PASSWORD = $OWUI_PASSWORD
$env:WEBUI_SECRET_KEY = $OWUI_SECRET

Write-Host "   Email: $OWUI_EMAIL"
Write-Host "   Password: $OWUI_PASSWORD"
Write-Host "   Secret: $OWUI_SECRET"

$process = Start-Process -FilePath $OWUI_PYTHON -ArgumentList "`"$OWUI_EXE`" serve --host 0.0.0.0 --port $OWUI_PORT" -PassThru -WindowStyle Hidden

Write-Host "   Started (PID: $($process.Id))"

# ========== STEP 4: Wait for server ==========
Write-Host "`n[4] Waiting for server..."
$maxWait = 60
$waited = 0
$serverUp = $false
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    try {
        $health = Invoke-RestMethod "http://localhost:$OWUI_PORT/api/v1/health" -ErrorAction SilentlyContinue
        if ($health) {
            Write-Host "   Server running (HTTP 200)" -ForegroundColor Green
            $serverUp = $true
            break
        }
    } catch { }
}

if (-not $serverUp) {
    Write-Host "   ERROR: Server tidak berjalan setelah 60s" -ForegroundColor Red
    exit 1
}

# ========== STEP 5: Test Login ==========
Write-Host "`n[5] Testing login..."
Start-Sleep -Seconds 5

$loginResult = Invoke-RestMethod "http://localhost:$OWUI_PORT/api/v1/auths/signin" -Method Post -ContentType "application/json" -Body (ConvertTo-Json @{
    email = $OWUI_EMAIL
    password = $OWUI_PASSWORD
}) -ErrorAction SilentlyContinue

if ($loginResult -and -notcontains "detail" $loginResult) {
    Write-Host "   OK: Login berhasil" -ForegroundColor Green
    Write-Host "   Token: $($loginResult.token.Substring(0, 20))..." -ForegroundColor Gray
} else {
    Write-Host "   ERROR: Login gagal" -ForegroundColor Red
    Write-Host "   Response: $($loginResult.detail)" -ForegroundColor Red
    exit 1
}

# ========== STEP 6: Test Chat ==========
Write-Host "`n[6] Testing chat (llama3.2:1b)..."
Start-Sleep -Seconds 5

$chatResult = Invoke-RestMethod "http://localhost:$OWUI_PORT/api/v1/chat" -Method Post -ContentType "application/json" -Body (ConvertTo-Json @{
    model = "llama3.2:1b"
    messages = @(@{
        role = "user"
        content = "Halo, apa kabar?"
    })
}) -ErrorAction SilentlyContinue

if ($chatResult -and $chatResult.message) {
    Write-Host "   OK: Chat response received" -ForegroundColor Green
    Write-Host "   Response: $($chatResult.message.content.Substring(0, 60))..." -ForegroundColor Gray
} else {
    Write-Host "   WARNING: Chat gagal, tapi server berjalan" -ForegroundColor Yellow
}

# ========== RESULT ==========
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hemostasis Autopilot" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:$OWUI_PORT"
Write-Host "   Email: $OWUI_EMAIL"
Write-Host "   Password: $OWUI_PASSWORD"
Write-Host "========================================" -ForegroundColor Cyan
