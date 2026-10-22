# start-openwebui.ps1
# PowerShell script to start OpenWebUI with admin account

$ErrorActionPreference = "Stop"

# 1. Stop existing OpenWebUI
Write-Host "[OK] Stop existing OpenWebUI..."
Stop-Process -Name "open-webui" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# 2. Delete old DB
Write-Host "[OK] Delete old database..."
$dbPath = "C:\Users\dmaza\AppData\Roaming\Python\Python311\Scripts\open-webui.exe.db"
if (Test-Path $dbPath) {
    Remove-Item $dbPath -Force
    Write-Host "   Deleted: $dbPath"
}

# 3. Delete old secret key
$secretPath = "C:\Users\dmaza\.webui_secret_key"
if (Test-Path $secretPath) {
    Remove-Item $secretPath -Force
    Write-Host "   Deleted: $secretPath"
}

# 4. Start new server with admin env vars
Write-Host "[OK] Start OpenWebUI..."
$env:WEBUI_ADMIN_EMAIL = "admin@admin.com"
$env:WEBUI_ADMIN_PASSWORD = "admin123"
$env:WEBUI_SECRET_KEY = [Convert]::ToBase64String([System.GUID]::NewGuid().ToByteArray())

& "C:\Users\dmaza\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\dmaza\AppData\Local\Programs\Python\Python311\Scripts\open-webui.exe" serve --host 0.0.0.0 --port 8080

Write-Host "[INFO] OpenWebUI stopped."
