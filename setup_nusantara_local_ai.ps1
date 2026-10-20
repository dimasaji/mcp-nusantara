#requires -Version 5.1

<#
NUSANTARA LOCAL AI SETUP
========================
Local-first developer environment.

Components:
- Nusantara Core
- Ollama
- llama3.2:1b
- Graphify (optional/local)
- Local project context
- Python compile validation
- API health validation

IMPORTANT:
This script does NOT:
- install Claude Code
- require Claude login
- call Claude API
- modify routes.py
- modify rag.py
- modify production knowledge engine
#>

$ErrorActionPreference = "Continue"

$ProjectRoot = "C:\Users\dmaza\mcp-starter"
$Model = "llama3.2:1b"
$OllamaUrl = "http://127.0.0.1:11434"
$ApiUrl = "http://127.0.0.1:8000"

Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        NUSANTARA LOCAL AI - SETUP                         " -ForegroundColor Cyan
Write-Host "        LOCAL / FREE / NO CLAUDE REQUIRED                  " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# HELPER
# ------------------------------------------------------------

function Write-Pass($Message) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-Warn($Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Fail($Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Write-Info($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Test-CommandExists($Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# ------------------------------------------------------------
# 1. PROJECT ROOT
# ------------------------------------------------------------

Write-Host "[1/10] Checking Nusantara project..." -ForegroundColor Yellow

if (-not (Test-Path $ProjectRoot)) {
    Write-Fail "Project tidak ditemukan: $ProjectRoot"
    exit 1
}

$requiredFiles = @(
    "pyproject.toml",
    "app",
    "data"
)

foreach ($item in $requiredFiles) {
    if (Test-Path (Join-Path $ProjectRoot $item)) {
        Write-Pass "Found: $item"
    }
    else {
        Write-Warn "Tidak ditemukan: $item"
    }
}

# ------------------------------------------------------------
# 2. PYTHON
# ------------------------------------------------------------

Write-Host ""
Write-Host "[2/10] Checking Python..." -ForegroundColor Yellow

if (-not (Test-CommandExists "python")) {
    Write-Fail "Python tidak ditemukan."
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Info "$pythonVersion"
Write-Pass "Python tersedia."

# ------------------------------------------------------------
# 3. OLLAMA
# ------------------------------------------------------------

Write-Host ""
Write-Host "[3/10] Checking Ollama..." -ForegroundColor Yellow

if (-not (Test-CommandExists "ollama")) {
    Write-Warn "Ollama CLI tidak ditemukan."
    Write-Info "Nusantara tetap dapat digunakan untuk compile/source setup."
}
else {
    Write-Pass "Ollama CLI ditemukan."

    Write-Host ""
    Write-Info "Ollama version:"
    ollama --version

    try {
        $ollamaResponse = Invoke-RestMethod `
            -Uri "$OllamaUrl/api/tags" `
            -Method Get `
            -TimeoutSec 5

        Write-Pass "Ollama API aktif: $OllamaUrl"

        $modelFound = $false

        if ($ollamaResponse.models) {
            foreach ($modelItem in $ollamaResponse.models) {
                if ($modelItem.name -eq $Model) {
                    $modelFound = $true
                    break
                }
            }
        }

        if ($modelFound) {
            Write-Pass "Model tersedia: $Model"
        }
        else {
            Write-Warn "Model $Model belum ditemukan."

            Write-Host ""
            $answer = Read-Host "Install model $Model sekarang? (Y/N)"

            if ($answer -match "^[Yy]$") {
                Write-Info "Pulling $Model ..."
                ollama pull $Model

                if ($LASTEXITCODE -eq 0) {
                    Write-Pass "Model $Model berhasil di-install."
                }
                else {
                    Write-Warn "Gagal pull model. Setup dilanjutkan."
                }
            }
            else {
                Write-Info "Model tidak di-install."
            }
        }
    }
    catch {
        Write-Warn "Ollama API belum aktif di $OllamaUrl"
        Write-Info "Jalankan Ollama jika ingin menggunakan local LLM."
    }
}

# ------------------------------------------------------------
# 4. UV
# ------------------------------------------------------------

Write-Host ""
Write-Host "[4/10] Checking uv..." -ForegroundColor Yellow

if (-not (Test-CommandExists "uv")) {

    Write-Warn "uv belum ditemukan."

    if (Test-CommandExists "winget") {
        Write-Info "Installing uv menggunakan winget..."

        winget install `
            --id=astral-sh.uv `
            -e `
            --accept-source-agreements `
            --accept-package-agreements

        $env:Path = `
            [System.Environment]::GetEnvironmentVariable("Path","User") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path","Machine")
    }
    else {
        Write-Warn "winget tidak tersedia."
    }
}

if (Test-CommandExists "uv") {
    Write-Pass "uv tersedia."
    uv --version
}
else {
    Write-Warn "uv belum tersedia. Graphify akan dilewati."
}

# ------------------------------------------------------------
# 5. GRAPHIFY
# ------------------------------------------------------------

Write-Host ""
Write-Host "[5/10] Checking Graphify..." -ForegroundColor Yellow

$graphifyAvailable = $false

if (Test-CommandExists "graphify") {
    $graphifyAvailable = $true
    Write-Pass "Graphify CLI sudah tersedia."
    graphify --version
}
elseif (Test-CommandExists "uv") {

    Write-Info "Installing Graphify secara local tool..."

    uv tool install graphifyy

    $env:Path = `
        [System.Environment]::GetEnvironmentVariable("Path","User") + ";" +
        [System.Environment]::GetEnvironmentVariable("Path","Machine")

    if (Test-CommandExists "graphify") {
        $graphifyAvailable = $true
        Write-Pass "Graphify berhasil dipasang."
        graphify --version
    }
    else {
        Write-Warn "Graphify belum tersedia setelah install."
    }
}
else {
    Write-Warn "uv tidak tersedia. Graphify dilewati."
}

# ------------------------------------------------------------
# 6. NUSANTARA LOCAL DEVELOPER CONTEXT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[6/10] Creating Nusantara local developer context..." -ForegroundColor Yellow

$NusantaraDir = Join-Path $ProjectRoot ".nusantara"

New-Item `
    -ItemType Directory `
    -Force `
    $NusantaraDir | Out-Null

New-Item `
    -ItemType Directory `
    -Force `
    (Join-Path $NusantaraDir "reports") | Out-Null

New-Item `
    -ItemType Directory `
    -Force `
    (Join-Path $NusantaraDir "scripts") | Out-Null

$contextFile = Join-Path $NusantaraDir "PROJECT_CONTEXT.md"

$context = @"
# NUSANTARA AI - LOCAL PROJECT CONTEXT

## Project

Nusantara Core + Hermes

Root:

C:\Users\dmaza\mcp-starter

## Runtime

FastAPI:
http://127.0.0.1:8000

Ollama:
http://127.0.0.1:11434

Default local model:

llama3.2:1b

## Architecture

User
↓
Language Engine
↓
Problem Engine
↓
Knowledge Engine
↓
Deterministic Safety / Routing
↓
Grounding Guard
↓
Hermes / Ollama
↓
Response

## Knowledge Engine

Legacy knowledge database:

data/knowledge/nusantara_knowledge.db

Production knowledge database:

data/knowledge/production_knowledge.db

Production modules:

app/knowledge/production_kb.py
app/knowledge/production_embedding_bridge.py

## Production Knowledge Roadmap

19.0 Production Knowledge Base
19.1 IndoBERT Embedding Bridge
19.2 Production Semantic Retriever
19.3 Production Hybrid RAG Bridge
19.4 Official Knowledge Ingestion
19.5 Production Grounding Benchmark
19.6 /v1/chat Integration
19.7 Full Regression
20.0 Production Knowledge Engine

## Safety Rules

Do NOT blindly modify:

app/api/routes.py
app/knowledge/rag.py

Always:

1. Read current source.
2. Backup before destructive change.
3. Use targeted patch.
4. Compile.
5. Run regression.
6. Preserve existing passing tests.

## Current Baseline

Compile:
PASS

Health:
PASS

API Contract:
20/20 PASS

E2E:
4/4 PASS

Production KB:
PASS

IndoBERT Bridge:
PASS

## Local-first principle

Prefer:

Python
FastAPI
Ollama
IndoBERT
SQLite
FTS5
Local embeddings
Graphify

Avoid unnecessary paid APIs.

## Developer instruction

Understand existing architecture before changing source.

Do not rewrite working modules unnecessarily.

Use isolated tests before production integration.
"@

Set-Content `
    -Path $contextFile `
    -Value $context `
    -Encoding UTF8

Write-Pass "Created .nusantara\PROJECT_CONTEXT.md"

# ------------------------------------------------------------
# 7. CLAUDE.MD AS GENERIC PROJECT CONTEXT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[7/10] Creating project developer instructions..." -ForegroundColor Yellow

$claudeFile = Join-Path $ProjectRoot "CLAUDE.md"

if (-not (Test-Path $claudeFile)) {

    $claudeContent = @"
# Nusantara AI Developer Context

Read `.nusantara/PROJECT_CONTEXT.md` before modifying the project.

Project root:

C:\Users\dmaza\mcp-starter

This project is local-first.

Primary runtime:

- Python
- FastAPI
- Ollama
- llama3.2:1b
- SQLite
- FTS5
- IndoBERT

Important:

Do not modify `routes.py` or `rag.py` blindly.

Before source changes:

1. Read the current file.
2. Identify the exact anchor.
3. Create a backup.
4. Apply a targeted patch.
5. Compile.
6. Run tests.

Preserve the existing baseline:

- Compile PASS
- Health PASS
- API Contract 20/20
- E2E 4/4

Production Knowledge roadmap:

19.2 Production Semantic Retriever
19.3 Production Hybrid RAG Bridge
19.4 Official Knowledge Ingestion
19.5 Production Grounding Benchmark
19.6 `/v1/chat` integration
19.7 Full Regression
20.0 Production Knowledge Engine
"@

    Set-Content `
        -Path $claudeFile `
        -Value $claudeContent `
        -Encoding UTF8

    Write-Pass "Created CLAUDE.md"
}
else {
    Write-Info "CLAUDE.md sudah ada. Tidak ditimpa."
}

# ------------------------------------------------------------
# 8. GRAPHIFY PROJECT GRAPH
# ------------------------------------------------------------

Write-Host ""
Write-Host "[8/10] Building local code graph..." -ForegroundColor Yellow

if ($graphifyAvailable) {

    Write-Info "Running Graphify..."

    try {
        graphify .

        if ($LASTEXITCODE -eq 0) {
            Write-Pass "Graphify selesai."
        }
        else {
            Write-Warn "Graphify selesai dengan exit code $LASTEXITCODE."
        }
    }
    catch {
        Write-Warn "Graphify gagal dijalankan."
        Write-Warn $_.Exception.Message
    }

}
else {
    Write-Warn "Graphify tidak tersedia. Langkah ini dilewati."
}

# ------------------------------------------------------------
# 9. PYTHON COMPILE TEST
# ------------------------------------------------------------

Write-Host ""
Write-Host "[9/10] Running Python compile validation..." -ForegroundColor Yellow

$compileTargets = @(
    "app",
    "scripts"
)

$compileFailed = $false

foreach ($target in $compileTargets) {

    if (-not (Test-Path $target)) {
        continue
    }

    Write-Info "Compiling $target ..."

    python -m compileall -q $target

    if ($LASTEXITCODE -ne 0) {
        $compileFailed = $true
        Write-Fail "Compile failed: $target"
    }
}

if (-not $compileFailed) {
    Write-Pass "Python compile validation PASS."
}

# ------------------------------------------------------------
# 10. API HEALTH
# ------------------------------------------------------------

Write-Host ""
Write-Host "[10/10] Checking Nusantara API..." -ForegroundColor Yellow

try {

    $health = Invoke-RestMethod `
        -Uri "$ApiUrl/v1/health" `
        -Method Get `
        -TimeoutSec 5

    Write-Pass "Nusantara API aktif."

    $health | ConvertTo-Json -Depth 10 |
        Set-Content `
            -Path (Join-Path $NusantaraDir "reports\health.json") `
            -Encoding UTF8

}
catch {

    Write-Warn "Nusantara API belum aktif."
    Write-Info "Health check dilewati."
}

# ------------------------------------------------------------
# CREATE LOCAL STATUS
# ------------------------------------------------------------

$status = [ordered]@{
    project_root = $ProjectRoot
    python = $pythonVersion.ToString()
    ollama_url = $OllamaUrl
    ollama_model = $Model
    graphify_available = $graphifyAvailable
    timestamp = (Get-Date).ToString("o")
}

$status |
    ConvertTo-Json -Depth 10 |
    Set-Content `
        -Path (Join-Path $NusantaraDir "reports\setup_status.json") `
        -Encoding UTF8

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "        NUSANTARA LOCAL AI SETUP COMPLETE                  " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Project : $ProjectRoot"
Write-Host "Ollama  : $OllamaUrl"
Write-Host "Model   : $Model"
Write-Host ""

Write-Host "Local context:" -ForegroundColor Cyan
Write-Host "  .nusantara\PROJECT_CONTEXT.md"

Write-Host ""
Write-Host "Reports:" -ForegroundColor Cyan
Write-Host "  .nusantara\reports\setup_status.json"
Write-Host "  .nusantara\reports\health.json"

Write-Host ""
Write-Host "Graphify:" -ForegroundColor Cyan

if ($graphifyAvailable) {
    Write-Host "  AVAILABLE" -ForegroundColor Green
}
else {
    Write-Host "  NOT AVAILABLE / SKIPPED" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Claude Code:" -ForegroundColor Cyan
Write-Host "  NOT REQUIRED"
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NEXT COMMANDS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Lihat status:" -ForegroundColor White
Write-Host "   Get-Content .\.nusantara\reports\setup_status.json" -ForegroundColor Yellow

Write-Host ""
Write-Host "2. Jika Graphify tersedia, lihat output:" -ForegroundColor White
Write-Host "   Get-ChildItem . -Recurse -File | Where-Object { `$_.Name -match 'graph' }" -ForegroundColor Yellow

Write-Host ""
Write-Host "3. Jika API belum hidup:" -ForegroundColor White
Write-Host "   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000" -ForegroundColor Yellow

Write-Host ""
Write-Host "4. Setelah semua PASS, lanjut Phase 19.2." -ForegroundColor White
Write-Host ""