$ErrorActionPreference = 'Continue'
# Non-destructive startup/health check. Does NOT stop or restart services.
# Writes a JSON evidence file to data/service-v1/startup-test-<timestamp>.json
$root = Split-Path $PSScriptRoot -Parent
$svc = Join-Path $root 'service/nusantara-service.ps1'
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$evidenceDir = Join-Path $root 'data/service-v1'
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
$out = Join-Path $evidenceDir "startup-test-$ts.json"

$results = [ordered]@{}

# 1. Status (process ownership + port listening)
$statusJson = & powershell -NoProfile -ExecutionPolicy Bypass -File $svc -Action status
$status = $statusJson | ConvertFrom-Json
$results.status = @{
    backend  = ($status.services | Where-Object service -eq 'backend' | Select-Object -First 1 | ForEach-Object { @{ port = $_.port; healthy = $_.healthy; owned = $_.owned; pids = $_.pids } })
    frontend = ($status.services | Where-Object service -eq 'frontend' | Select-Object -First 1 | ForEach-Object { @{ port = $_.port; healthy = $_.healthy; owned = $_.owned; pids = $_.pids } })
    proxyHealthy = $status.proxyHealthy
    ollamaHealthy = $status.ollamaHealthy
}

# 2. Duplicate-instance check: exactly one listener per port
foreach ($port in 8000, 5180) {
    $listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
    $results["listeners_$port"] = $listeners.Count
}

# 3. Backend health
try { $results.backend_health = (Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 10).status } catch { $results.backend_health = "ERROR: $($_.Exception.Message)" }

# 4. Proxy health through frontend
try { $results.proxy_5180_health = (Invoke-RestMethod -Uri 'http://127.0.0.1:5180/health' -TimeoutSec 10).status } catch { $results.proxy_5180_health = "ERROR: $($_.Exception.Message)" }

# 5. Ollama
try { $results.ollama_version = (Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 5).version } catch { $results.ollama_version = "ERROR: $($_.Exception.Message)" }

# 6. Autostart: task registered? (read-only)
$task = Get-ScheduledTask -TaskName 'NUSANTARA-V1*' -ErrorAction SilentlyContinue
$results.autostart_task = if ($task) { "REGISTERED: $($task.TaskName) state=$($task.State)" } else { 'NOT_REGISTERED' }

# 7. Admin rights (needed only for install/uninstall)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$results.session_is_admin = $isAdmin

# 8. Chat via backend (real provider call only if OpenRouter model is active; PIAK-03 uses evidence fast path)
$body = @{ session_id = 'web-00000000-0000-4000-8000-000000000001'; user_input = 'Apa persyaratan PIAK-03?'; request_id = ([guid]::NewGuid().ToString('N')) } | ConvertTo-Json
try {
    $chat = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/v1/chat' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120
    $results.chat_piak03 = @{ provider_status = $chat.provider_status; grounded = $chat.grounding.grounded; response = $chat.response }
} catch { $results.chat_piak03 = "ERROR: $($_.Exception.Message)" }

$results.evidence_file = $out
$results.generated_at = (Get-Date).ToString('o')
$results | ConvertTo-Json -Depth 8 | Set-Content -Path $out -Encoding UTF8
$results | ConvertTo-Json -Depth 8
