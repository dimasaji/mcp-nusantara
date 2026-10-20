<#
.SYNOPSIS
    Test Chat API - Nusantara Core + Hermes

.DESCRIPTION
    Script ini menguji endpoint chat API dari project mcp-starter.
    Meliputi: health check, pertanyaan umum (general knowledge),
    pertanyaan berbasis knowledge base, dan blokir keamanan.

.NOTES
    File: Test-Chat-API.ps1
    Directory: C:\Users\dmaza\mcp-starter\
    Last modified: 2026-10-20

#>

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Session = "test-session-001",
    [int]$MaxRetries = 3,
    [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Continue"

# Color output helpers
function Write-Color([string]$Text, [string]$Color = "White") {
    $original = $host.UI.RawUI.ForegroundColor
    try {
        $host.UI.RawUI.ForegroundColor = $Color
        Write-Host $Text -NoNewline
    } finally {
        $host.UI.RawUI.ForegroundColor = $original
    }
}

function Write-Info([string]$Message) {
    Write-Host "[INFO]" -ForegroundColor Yellow -NoNewline
    Write-Host " $Message"
}

function Write-Success([string]$Message) {
    Write-Host "[OK]" -ForegroundColor Green -NoNewline
    Write-Host " $Message"
}

function Write-WarningMsg([string]$Message) {
    Write-Host "[WARN]" -ForegroundColor Red -NoNewline
    Write-Host " $Message"
}

function Write-ErrorMsg([string]$Message) {
    Write-Host "[ERROR]" -ForegroundColor Red -NoNewline
    Write-Host " $Message"
}

function Invoke-CurlGet {
    param([string]$Url, [int]$Retry = 0)
    $result = curl.exe -s -w "\n%{http_code}" -X GET "$Url" 2>&1
    $lines = $result -split "`n"
    $body = ($lines | Where-Object { $_ -notmatch "^\d{3}$" }) -join "`n"
    $code = ($lines | Where-Object { $_ -match "^\d{3}$" })[-1]
    return @{
        Body = $body
        Code = $code
    }
}

function CurlPost {
    param([string]$Url, [string]$Body, [hashtable]$H = @{}, [int]$T = 5)
    $h = @("-H", "Content-Type: application/json")
    foreach ($k in $H.Keys) { $h += @("-H", "$k: $($H[$k])") }
    $r = curl.exe -s -m $T -w "\n%{http_code}" -X POST $h "$Url" -d $Body 2>&1
    $lines = $r -split "`n"
    $body = ($lines | Where-Object { $_ -notmatch "^\d{3}$" }) -join "`n"
    $code = ($lines | Where-Object { $_ -match "^\d{3}$" })[-1]
    return @{"body"=$body; "code"=$code}
}

# Clear screen
Clear-Host
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Chat API - Nusantara Core + Hermes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Health Check
# 1. Health Check
if (-not $SkipHealthCheck) {
    Write-Info "1. Mengecek kesehatan server..."
    $health = Invoke-CurlGet -Url "$BaseUrl/health"
    if ($health.Code -eq "200") {
        $data = $health.Body | ConvertFrom-Json
        Write-Color "Status: " -ForegroundColor Green -NoNewline
        Write-Host "OK ($($data.status)) | version: $($data.version)"
        Write-Success "Server berjalan"
    } else {
        Write-ErrorMsg "Gagal: HTTP $($health.Code)"
        Write-ErrorMsg "Response: $($health.Body)"
        Write-ErrorMsg "Pastikan server sedang berjalan: python app/main.py"
        exit 1
    }
    Write-Host ""
}

# 2. General knowledge
W-Info "2. Pertanyaan umum (harus natural)..."
$qs = @("Apa itu Nusantara?", "Siapa presiden Indonesia?", "Apa fungsi CPU?")
foreach ($q in $qs) {
    $body = @{"session_id"=$Session;"user_input"=$q;"model"="llama3.2:1b"} | ConvertTo-Json
    $r = CurlPost -Url "$BaseUrl/v1/chat" -Body $body -T $Timeout
    $d = $r.body | ConvertFrom-Json 2>$null
    if ($r.code -eq "200") {
        $p = $d.provider_status
        $t = $d.response
        $ok = $t -notmatch "belum tersedia" -and $t.Length -gt 10
        $tag = if ($ok) { "OK" } else { "FALLBACK" }
        Write-Host "   [$tag] $q"
        Write-Host "       Provider: $p | Response: $($t.Substring(0, [Math]::Min(80, $t.Length)))"
    } else {
        Write-Host "   [ERROR] $q -> HTTP $($r.code)"
    }
}

# 3. Knowledge-based
W-Info "3. Berbasis KB..."
$body = @{"session_id"=$Session;"user_input"="Apa syarat daftar KTP-el?","model"="llama3.2:1b"} | ConvertTo-Json
$r = CurlPost -Url "$BaseUrl/v1/chat" -Body $body -T $Timeout
$d = $r.body | ConvertFrom-Json 2>$null
if ($r.code -eq "200") {
    Write-Host "   Provider: $($d.provider_status)"
    Write-Host "   Response: $($d.response.Substring(0, [Math]::Min(100, $d.response.Length)))"
} else {
    Write-Host "   [ERROR] -> HTTP $($r.code)"
}
Write-Host ""

# 4. Blocked
W-Info "4. Blokir (KTP)..."
$body = @{"session_id"=$Session;"user_input"="Cara daftar KTP-el yang terverifikasi","model"="llama3.2:1b"} | ConvertTo-Json
$r = CurlPost -Url "$BaseUrl/v1/chat" -Body $body -T $Timeout
$d = $r.body | ConvertFrom-Json 2>$null
if ($r.code -eq "200") {
    Write-Host "   Provider: $($d.provider_status)"
    Write-Host "   Response: $($d.response.Substring(0, [Math]::Min(100, $d.response.Length)))"
} else {
    Write-Host "   [ERROR] -> HTTP $($r.code)"
}
Write-Host ""

# 5. Conversation
W-Info "5. Percakapan..."
$body = @{"session_id"=$Session;"user_input"="Halo, siapa kabar?","model"="llama3.2:1b"} | ConvertTo-Json
$r = CurlPost -Url "$BaseUrl/v1/chat" -Body $body -T $Timeout
$d = $r.body | ConvertFrom-Json 2>$null
if ($r.code -eq "200") {
    Write-Host "   Provider: $($d.provider_status)"
    Write-Host "   Response: $($d.response.Substring(0, [Math]::Min(100, $d.response.Length)))"
} else {
    Write-Host "   [ERROR] -> HTTP $($r.code)"
}
Write-Host ""

# 6. Chat History
W-Info "6. History..."
$body = @{"session_id"=$Session} | ConvertTo-Json
$r = CurlPost -Url "$BaseUrl/v1/chat/history" -Body $body -H @{"x-chat-session"=$Session} -T $Timeout
if ($r.code -eq "200") {
    $d = $r.body | ConvertFrom-Json
    $count = ($d.turns | Measure-Object).Count
    Write-Host "   Total turn: $count"
    if ($count -gt 0) {
        Write-Host "   Last 2 turns:"
        $d.turns | Select-Object -Last 2 | ForEach-Object {
            Write-Host "     - [$($_.provider_status)] $($_.question.substring(0, [Math]::Min(80, $_.question.Length)))" -FC Gray
        }
    }
} else {
    Write-Host "   [ERROR] -> HTTP $($r.code)"
}
Write-Host ""

# Summary
W-Info "7. Ringkasan..."
$succeeded = 0
$total = 0
for ($i = 3; $i -le 5; $i++) {
    $body = @{"session_id"=$Session;"user_input"="Pertanyaan $i","model"="llama3.2:1b"} | ConvertTo-Json
    $r = CurlPost -Url "$BaseUrl/v1/chat" -Body $body -T $Timeout
    $d = $r.body | ConvertFrom-Json 2>$null
    if ($r.code -eq "200") {
        $total++
        if ($d.response -notmatch "belum tersedia" -and $d.response.Length -gt 10) {
            $succeeded++
            W-Success "Pertanyaan $i: natural"
        } else {
            W-Warn "Pertanyaan $i: fallback"
        }
    } else {
        W-Err "Pertanyaan $i: HTTP $($r.code)"
    }
}
Write-Host ""
W-Success "Server berjalan di http://localhost:8000"
Write-Host ""
Write-Host "  Test manual:"
Write-Host "  curl -X POST http://localhost:8000/v1/chat -H 'Content-Type: application/json' -d '{\"session_id\":\"t1\",\"user_input\":\"Apa itu Nusantara?\",\"model\":\"llama3.2:1b\"}'"
Write-Host ""
Write-Host "  Perintah cepat:"
Write-Host "  pwsh -ExecutionPolicy Bypass -File Test-Chat-API.ps1"
Write-Host ""

Write-Info "Test selesai. Cek server logs untuk detail."
