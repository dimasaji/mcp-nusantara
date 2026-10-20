# Nusantara V1 - safe local diagnostic and targeted verification
# Run from repository root: powershell -ExecutionPolicy Bypass -File .\Invoke-NusantaraV1-AutoPilot.ps1
[CmdletBinding()]
param(
    [string]$Root = 'C:\Users\dmaza\mcp-starter',
    [switch]$ProbeHermes,
    [switch]$RunTests
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw "Repository not found: $Root" }
Set-Location -LiteralPath $Root
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportDir = Join-Path $Root 'docs\reports'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$reportPath = Join-Path $reportDir "NUSANTARA-V1-AUTOPILOT-$stamp.json"
$results = [ordered]@{ timestamp=(Get-Date).ToString('o'); root=$Root; checks=@(); summary='HOLD'; note='Checks are observations, not evidence of full E2E readiness.' }
function Add-Check([string]$Name,[string]$Status,[string]$Detail) {
    $results.checks += [ordered]@{name=$Name;status=$Status;detail=$Detail}
    Write-Host ('[{0}] {1}: {2}' -f $Status,$Name,$Detail)
}
function Request-Local([string]$Url,[string]$Method='GET',[hashtable]$Headers=@{},[string]$Body='') {
    try {
        $params = @{Uri=$Url;Method=$Method;Headers=$Headers;TimeoutSec=12;UseBasicParsing=$true;ErrorAction='Stop'}
        if ($Method -eq 'POST') { $params.ContentType='application/json'; $params.Body=$Body }
        $r = Invoke-WebRequest @params
        return @{code=[int]$r.StatusCode;body=[string]$r.Content}
    } catch {
        $code = 'NO_RESPONSE'; $body=''
        if ($_.Exception.Response) {
            try { $code = [int]$_.Exception.Response.StatusCode } catch {}
            try {
                $stream=$_.Exception.Response.GetResponseStream()
                if ($stream) { $reader=New-Object System.IO.StreamReader($stream); $body=$reader.ReadToEnd();$reader.Dispose() }
            } catch {}
        }
        return @{code=$code;body=$body}
    }
}
try {
    $who = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    Add-Check 'Windows account' 'INFO' $who
    foreach($port in @(8000,5180,8765)) {
        $conn = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
        if($conn.Count -gt 0) {
            $ids = ($conn | Select-Object -ExpandProperty OwningProcess -Unique) -join ','
            Add-Check "Port $port" 'PASS' "LISTEN; PID=$ids"
        } else { Add-Check "Port $port" 'HOLD' 'Not listening' }
    }
    $api = Request-Local 'http://127.0.0.1:8000/openapi.json'
    if ($api.code -eq 200) { Add-Check 'Backend OpenAPI' 'PASS' 'HTTP 200' }
    else { Add-Check 'Backend OpenAPI' 'HOLD' "HTTP $($api.code)" }
    $ui = Request-Local 'http://127.0.0.1:5180/'
    if ($ui.code -eq 200) { Add-Check 'Frontend' 'PASS' 'HTTP 200' }
    else { Add-Check 'Frontend' 'HOLD' "HTTP $($ui.code)" }
    $hermesExe = Join-Path $env:LOCALAPPDATA 'hermes\bin\hermes-acp.exe'
    if (Test-Path -LiteralPath $hermesExe) { Add-Check 'Hermes executable' 'PASS' 'Found under current Windows user LOCALAPPDATA' }
    else { Add-Check 'Hermes executable' 'HOLD' 'Not found under current Windows user LOCALAPPDATA' }
    $python = Join-Path $Root '.venv\Scripts\python.exe'
    $envFile = Join-Path $Root '.env'
    $token = ''
    if ((Test-Path -LiteralPath $python) -and (Test-Path -LiteralPath $envFile)) {
        # Read token with existing python-dotenv, never write it to console or report.
        try {
            $token = (& $python -c "from dotenv import dotenv_values; print(dotenv_values('.env', interpolate=False).get('NUSANTARA_ADMIN_TOKEN') or '')" 2>$null | Select-Object -Last 1).Trim()
        } catch { $token='' }
    }
    if ([string]::IsNullOrWhiteSpace($token)) { Add-Check 'Admin token configured' 'HOLD' 'Token could not be loaded; value not logged' }
    else {
        Add-Check 'Admin token configured' 'PASS' 'Token present; value not logged'
        $headers = @{'X-Admin-Token'=$token}
        $get = Request-Local 'http://127.0.0.1:8000/v1/control-plane/hermes/connection' 'GET' $headers
        if ($get.code -eq 200) {
            $state = 'UNKNOWN'
            try { $state = ([string](ConvertFrom-Json -InputObject $get.body).status) } catch {}
            Add-Check 'Hermes GET' 'PASS' "HTTP 200; status=$state"
        } else { Add-Check 'Hermes GET' 'HOLD' "HTTP $($get.code)" }
        if ($ProbeHermes) {
            $post = Request-Local 'http://127.0.0.1:8000/v1/control-plane/hermes/connection' 'POST' $headers '{}'
            $state = 'UNKNOWN'; $reason = ''
            try { $j = ConvertFrom-Json -InputObject $post.body; $state=[string]$j.status; $reason=[string]$j.reason } catch {}
            if ($reason.Length -gt 200) { $reason = $reason.Substring(0,200) }
            if ($post.code -eq 200 -and $state -eq 'CONNECTED') { Add-Check 'Hermes live handshake' 'PASS' 'HTTP 200; CONNECTED' }
            else { Add-Check 'Hermes live handshake' 'HOLD' "HTTP $($post.code); status=$state; reason=$reason" }
        } else { Add-Check 'Hermes live handshake' 'SKIP' 'Run with -ProbeHermes for real local ACP initialize' }
    }
    $chatFiles = @('control-plane\src\hermes-connection.tsx','app\developer_core\hermes_acp_connection.py','control-plane\vite.config.ts')
    foreach($file in $chatFiles) {
        if(Test-Path -LiteralPath (Join-Path $Root $file)) { Add-Check "File $file" 'PASS' 'Exists' }
        else { Add-Check "File $file" 'HOLD' 'Missing' }
    }
    if ($RunTests) {
        if(Test-Path -LiteralPath $python) {
            $testPath = 'tests\test_hermes_acp_connection.py'
            if(Test-Path -LiteralPath $testPath) {
                & $python -m pytest -q $testPath
                if($LASTEXITCODE -eq 0) { Add-Check 'ACP targeted pytest' 'PASS' 'Tests passed' }
                else { Add-Check 'ACP targeted pytest' 'HOLD' "Exit code $LASTEXITCODE" }
            } else { Add-Check 'ACP targeted pytest' 'SKIP' 'Known test path not present; no test names guessed' }
        }
        $frontend = Join-Path $Root 'control-plane'
        if((Test-Path -LiteralPath (Join-Path $frontend 'package.json')) -and (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
            Push-Location $frontend
            try {
                & npm.cmd run build
                if($LASTEXITCODE -eq 0) { Add-Check 'Frontend build' 'PASS' 'Build passed' }
                else { Add-Check 'Frontend build' 'HOLD' "Exit code $LASTEXITCODE" }
            } finally { Pop-Location }
        } else { Add-Check 'Frontend build' 'SKIP' 'npm or package.json not found' }
    } else { Add-Check 'Tests' 'SKIP' 'Run with -RunTests to execute targeted tests and build' }
    $hold = @($results.checks | Where-Object { $_.status -eq 'HOLD' })
    if ($hold.Count -eq 0) { $results.summary='CHECKS_PASS_NOT_FULL_E2E' }
    $results | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Host "`nReport: $reportPath"
    Write-Host "Summary: $($results.summary)"
    Write-Host 'Note: Chat 504 root cause requires trace/log evidence; this script does not send paid model requests.'
} finally {
    $token = $null; $headers = $null
}
