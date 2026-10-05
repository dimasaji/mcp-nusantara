# ============================================================
# NUSANTARA MASTER AUDIT PHASE 0-21
# ============================================================

$ErrorActionPreference = "Continue"

$Root = (Get-Location).Path
$AuditDir = Join-Path $Root "docs\audit"

New-Item -ItemType Directory -Force -Path $AuditDir | Out-Null

$Report = Join-Path $AuditDir "NUSANTARA_AUDIT_PHASE_0_21.md"

function Exists($Path) {
    return Test-Path (Join-Path $Root $Path)
}

function Add-Phase {
    param(
        [int]$Number,
        [string]$Name,
        [string]$Status,
        [string]$Evidence,
        [string]$Missing,
        [string]$Priority
    )

    $script:Rows += [PSCustomObject]@{
        Phase = $Number
        Area = $Name
        Status = $Status
        Priority = $Priority
        Evidence = $Evidence
        Missing = $Missing
    }
}

$Rows = @()

Write-Host ""
Write-Host "============================================================"
Write-Host " NUSANTARA MASTER AUDIT PHASE 0-21"
Write-Host "============================================================"
Write-Host "ROOT: $Root"
Write-Host ""

# ------------------------------------------------------------
# PHASE 0
# ------------------------------------------------------------

$e = @()

if (Exists ".git") { $e += "Git repository" }
if (Exists "app") { $e += "app/" }
if (Exists "tests") { $e += "tests/" }
if (Exists "pyproject.toml") { $e += "pyproject.toml" }

Add-Phase `
    0 `
    "Discovery" `
    "PARTIAL" `
    ($e -join "; ") `
    "Repository inventory; dependency inventory; runtime inventory; config audit; duplicate engine audit" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 1
# ------------------------------------------------------------

$e = @()

if (Exists "ARCHITECTURE_CURRENT.md") {
    $e += "ARCHITECTURE_CURRENT.md"
}

if (Exists "TARGET_ARCHITECTURE.md") {
    $e += "TARGET_ARCHITECTURE.md"
}

if (Exists "docs\contracts\NUSANTARA-ARCHITECTURE-CONTRACT-V1.md") {
    $e += "V1 Architecture Contract"
}

Add-Phase `
    1 `
    "Architecture Map" `
    "PARTIAL" `
    ($e -join "; ") `
    "Complete call graph; engine ownership; config ownership; V1 freeze; contract tests" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 2
# ------------------------------------------------------------

$e = @()

if (Exists "app\core\hardening") {
    $e += "Hardening directory"
}

foreach ($f in @(
    "validator.py",
    "timeout.py",
    "retry.py",
    "circuit_breaker.py",
    "safe_execution.py"
)) {
    if (Exists "app\core\hardening\$f") {
        $e += $f
    }
}

if (Exists "tests\test_phase2_hardening.py") {
    $e += "Phase 2 tests"
}

Add-Phase `
    2 `
    "Core Hardening" `
    "DONE*" `
    ($e -join "; ") `
    "Final repository verification" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 3
# ------------------------------------------------------------

$e = @()

if (Exists "app\observability") {
    $e += "app/observability"
}

foreach ($f in @(
    "tests\test_phase3_http_integration.py",
    "tests\test_phase3_metrics_integration.py",
    "tests\test_phase3_observability.py"
)) {
    if (Exists $f) {
        $e += $f
    }
}

Add-Phase `
    3 `
    "Observability" `
    "PARTIAL" `
    ($e -join "; ") `
    "Runtime verification; metrics; tracing; integration tests; production telemetry" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 4
# ------------------------------------------------------------

$e = @()

if (Exists "app\trust") {
    $e += "app/trust"
}

Add-Phase `
    4 `
    "Trust" `
    "PARTIAL" `
    ($e -join "; ") `
    "Trust scoring; source trust; model trust; tool trust; execution enforcement; tests" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 5
# ------------------------------------------------------------

$e = @()

if (Exists "app\policy") {
    $e += "app/policy"
}

Add-Phase `
    5 `
    "Policy" `
    "PARTIAL" `
    ($e -join "; ") `
    "Policy enforcement; risk classification; deny/allow tests; audit trail" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 6
# ------------------------------------------------------------

$e = @()

if (Exists "app\memory") {
    $e += "app/memory"
}

Add-Phase `
    6 `
    "Memory" `
    "PARTIAL" `
    ($e -join "; ") `
    "STM; LTM; retrieval; write policy; retention; evaluation" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 7
# ------------------------------------------------------------

$e = @()

if (Exists "app\knowledge") {
    $e += "app/knowledge"
}

if (Exists "app\knowledge\rag.py") {
    $e += "rag.py"
}

if (Exists "app\knowledge\grounding.py") {
    $e += "grounding.py"
}

Add-Phase `
    7 `
    "RAG / Knowledge" `
    "PARTIAL" `
    ($e -join "; ") `
    "Relevance benchmark; negative retrieval; metadata filtering; reranker; grounding regression; E2E evaluation" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 8
# ------------------------------------------------------------

$e = @()

if (Exists "app\mcp") {
    $e += "app/mcp"
}

Add-Phase `
    8 `
    "MCP" `
    "PARTIAL" `
    ($e -join "; ") `
    "Registry; discovery; lifecycle; permissions; failure handling; security tests" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 9
# ------------------------------------------------------------

Add-Phase `
    9 `
    "Tool Governance" `
    "PARTIAL" `
    "Tool architecture requires verification" `
    "Identity; capabilities; risk; authorization; validation; approval; audit; sandbox" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 10
# ------------------------------------------------------------

$e = @()

if (Exists "app\main.py") {
    $e += "FastAPI main.py"
}

if (Exists "frontend") {
    $e += "frontend/"
}

if (Exists "ui") {
    $e += "ui/"
}

Add-Phase `
    10 `
    "Experience" `
    "PARTIAL" `
    ($e -join "; ") `
    "Complete UI; history; files; streaming; evidence UX; session isolation" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 11
# ------------------------------------------------------------

Add-Phase `
    11 `
    "Feedback" `
    "PARTIAL" `
    "Requires repository verification" `
    "Feedback storage; corrections; evaluation pipeline; analytics" `
    "MEDIUM"


# ------------------------------------------------------------
# PHASE 12
# ------------------------------------------------------------

Add-Phase `
    12 `
    "Evaluation" `
    "NOT COMPLETE" `
    "Tests directory exists" `
    "Golden dataset; benchmarks; scoring; thresholds; regression evaluation" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 13
# ------------------------------------------------------------

Add-Phase `
    13 `
    "Failure Analysis" `
    "NOT COMPLETE" `
    "Requires implementation verification" `
    "Failure taxonomy; RCA; severity; reproduction; remediation; regression generation" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 14
# ------------------------------------------------------------

Add-Phase `
    14 `
    "Gap Detection" `
    "NOT COMPLETE" `
    "Requires implementation verification" `
    "Capability inventory; requirement mapping; missing capability detection; priority; dependencies" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 15
# ------------------------------------------------------------

Add-Phase `
    15 `
    "Knowledge Discovery" `
    "NOT COMPLETE" `
    "Requires implementation verification" `
    "Source discovery; trust; candidates; deduplication; freshness; verification; approval" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 16
# ------------------------------------------------------------

Add-Phase `
    16 `
    "Experiment" `
    "NOT COMPLETE" `
    "Requires implementation verification" `
    "Sandbox; baseline; candidate; comparison; evaluation; promotion; rollback" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 17
# ------------------------------------------------------------

$e = @()

if (Exists "app\developer_core") {
    $e += "app/developer_core"
}

if (Exists "app\developer_core\engine.py") {
    $e += "DeveloperCoreEngine"
}

Add-Phase `
    17 `
    "Developer Core" `
    "PARTIAL" `
    ($e -join "; ") `
    "Self-analysis; diagnosis; gap integration; proposal; risk; patch; testing; sandbox; evaluation; approval; promotion; rollback" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 18
# ------------------------------------------------------------

Add-Phase `
    18 `
    "Human Approval" `
    "PARTIAL" `
    "Approval architecture requires verification" `
    "Approval request; risk; diff; evidence; approve/reject; audit; rollback" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 19
# ------------------------------------------------------------

Add-Phase `
    19 `
    "V1.x Development" `
    "NOT COMPLETE" `
    "V1.x gate not yet closed" `
    "V1 freeze; baseline; regression; security; approved roadmap; implementation" `
    "HIGH"


# ------------------------------------------------------------
# PHASE 20
# ------------------------------------------------------------

Add-Phase `
    20 `
    "Regression / Security" `
    "NOT COMPLETE" `
    "Tests directory exists" `
    "Full regression; E2E; security; injection; tool abuse; leakage; RAG poisoning; load tests" `
    "CRITICAL"


# ------------------------------------------------------------
# PHASE 21
# ------------------------------------------------------------

Add-Phase `
    21 `
    "Release / Rollback" `
    "NOT COMPLETE" `
    "Git available" `
    "Release artifact; config snapshot; backup; smoke test; rollback; recovery; monitoring; approval" `
    "CRITICAL"


# ============================================================
# CALCULATE
# ============================================================

$Done = @($Rows | Where-Object {
    $_.Status -like "DONE*"
}).Count

$Partial = @($Rows | Where-Object {
    $_.Status -eq "PARTIAL"
}).Count

$NotComplete = @($Rows | Where-Object {
    $_.Status -eq "NOT COMPLETE"
}).Count

$Score = [math]::Round(
    (($Done * 1.0) + ($Partial * 0.5)) / $Rows.Count * 100,
    2
)


# ============================================================
# CONSOLE OUTPUT
# ============================================================

Write-Host ""
Write-Host "PHASE STATUS"
Write-Host "------------------------------------------------------------"

foreach ($r in $Rows) {

    switch -Wildcard ($r.Status) {
        "DONE*" {
            $icon = "[DONE]"
        }

        "PARTIAL" {
            $icon = "[PARTIAL]"
        }

        "NOT COMPLETE" {
            $icon = "[NOT COMPLETE]"
        }

        default {
            $icon = "[UNKNOWN]"
        }
    }

    Write-Host ("PHASE {0,2} | {1,-25} | {2}" -f `
        $r.Phase,
        $r.Area,
        "$icon $($r.Status)")
}


# ============================================================
# MARKDOWN REPORT
# ============================================================

$Lines = @()

$Lines += "# NUSANTARA MASTER AUDIT PHASE 0–21"
$Lines += ""
$Lines += "**Tanggal:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$Lines += ""
$Lines += "**Repository:** ``$Root``"
$Lines += ""
$Lines += "## Overall Progress"
$Lines += ""
$Lines += "**Estimated Progress: $Score%**"
$Lines += ""
$Lines += "| Metric | Count |"
$Lines += "|---|---:|"
$Lines += "| DONE | $Done |"
$Lines += "| PARTIAL | $Partial |"
$Lines += "| NOT COMPLETE | $NotComplete |"
$Lines += ""
$Lines += "> Status ini adalah audit otomatis awal. DONE final tetap membutuhkan implementation + integration + test evidence."
$Lines += ""
$Lines += "## Phase Matrix"
$Lines += ""
$Lines += "| Phase | Area | Status | Priority | Evidence |"
$Lines += "|---:|---|---|---|---|"

foreach ($r in $Rows) {

    $Evidence = $r.Evidence.Replace("|", "\|")
    $Lines += "| $($r.Phase) | $($r.Area) | **$($r.Status)** | $($r.Priority) | $Evidence |"
}

$Lines += ""
$Lines += "## Remaining Work"
$Lines += ""

foreach ($r in $Rows) {

    $Lines += "### Phase $($r.Phase) — $($r.Area)"
    $Lines += ""
    $Lines += "**Status:** $($r.Status)"
    $Lines += ""
    $Lines += "**Evidence:** $($r.Evidence)"
    $Lines += ""
    $Lines += "**Masih diperlukan:**"
    $Lines += ""

    foreach ($m in ($r.Missing -split "; ")) {
        $Lines += "- [ ] $m"
    }

    $Lines += ""
}

$Lines += "## Critical Order"
$Lines += ""
$Lines += "1. Phase 3 — Observability"
$Lines += "2. Phase 4–5 — Trust + Policy"
$Lines += "3. Phase 6–9 — Memory + RAG + MCP + Tool Governance"
$Lines += "4. Phase 12 — Evaluation"
$Lines += "5. Phase 13–14 — Failure Analysis + Gap Detection"
$Lines += "6. Phase 17 — Developer Core"
$Lines += "7. Phase 18 — Human Approval"
$Lines += "8. Phase 20 — Regression/Security"
$Lines += "9. Phase 21 — Release/Rollback"
$Lines += ""
$Lines += "## Important"
$Lines += ""
$Lines += "Graphify/Hermes runtime connection must be explicitly verified. A self-analysis call alone does not prove that the complete Developer Core lifecycle is operational."
$Lines += ""

$Lines | Set-Content -Path $Report -Encoding UTF8

Write-Host ""
Write-Host "============================================================"
Write-Host "AUDIT SELESAI"
Write-Host "============================================================"
Write-Host "Estimated Progress : $Score%"
Write-Host "Report             : $Report"
Write-Host ""
