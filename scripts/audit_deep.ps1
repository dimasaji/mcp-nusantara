# ============================================================
# NUSANTARA DEEP RUNTIME AUDIT
# Phase 0 - 21
# ============================================================

$ErrorActionPreference = "Continue"

$Root = (Get-Location).Path
$AuditDir = Join-Path $Root "docs\audit"
$Report = Join-Path $AuditDir "NUSANTARA_DEEP_AUDIT_PHASE_0_21.md"

New-Item -ItemType Directory -Force -Path $AuditDir | Out-Null

$Results = @()

function Add-Result {
    param(
        [string]$Phase,
        [string]$Area,
        [string]$Status,
        [string]$Evidence
    )

    $script:Results += [PSCustomObject]@{
        Phase    = $Phase
        Area     = $Area
        Status   = $Status
        Evidence = $Evidence
    }
}

function Run-CommandCapture {
    param(
        [string]$Command
    )

    try {
        $output = Invoke-Expression $Command 2>&1 | Out-String
        return $output.Trim()
    }
    catch {
        return "ERROR: $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host " NUSANTARA DEEP RUNTIME AUDIT PHASE 0-21"
Write-Host "============================================================"
Write-Host "ROOT: $Root"
Write-Host ""

# ------------------------------------------------------------
# BASIC ENVIRONMENT
# ------------------------------------------------------------

Write-Host "[1/12] Checking Python..."

$PythonVersion = Run-CommandCapture "python --version"

if ($PythonVersion -match "Python") {
    Add-Result "ENV" "Python" "PASS" $PythonVersion
}
else {
    Add-Result "ENV" "Python" "FAIL" $PythonVersion
}

Write-Host $PythonVersion

# ------------------------------------------------------------
# PROJECT STRUCTURE
# ------------------------------------------------------------

Write-Host ""
Write-Host "[2/12] Checking project structure..."

$RequiredPaths = @(
    "app",
    "tests",
    "scripts",
    "docs",
    "app\main.py",
    "app\knowledge",
    "app\core",
    "app\developer_core"
)

foreach ($Path in $RequiredPaths) {
    $FullPath = Join-Path $Root $Path

    if (Test-Path $FullPath) {
        Add-Result "0-1" "PATH:$Path" "PASS" "Exists"
    }
    else {
        Add-Result "0-1" "PATH:$Path" "FAIL" "Missing"
    }
}

# ------------------------------------------------------------
# GIT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[3/12] Checking Git..."

$GitStatus = Run-CommandCapture "git status --short"
$GitBranch = Run-CommandCapture "git branch --show-current"

Add-Result "0" "Git Branch" "INFO" $GitBranch
Add-Result "0" "Git Status" "INFO" $GitStatus

# ------------------------------------------------------------
# PYTHON COMPILE
# ------------------------------------------------------------

Write-Host ""
Write-Host "[4/12] Running Python compile check..."

$CompileOutput = Run-CommandCapture "python -m compileall -q app tests"

if ($CompileOutput -eq "") {
    Add-Result "20" "Python Compile" "PASS" "compileall completed successfully"
}
else {
    Add-Result "20" "Python Compile" "FAIL" $CompileOutput
}

# ------------------------------------------------------------
# PYTEST
# ------------------------------------------------------------

Write-Host ""
Write-Host "[5/12] Running pytest..."

$PytestOutput = Run-CommandCapture "python -m pytest -q"

if ($PytestOutput -match "\d+ passed") {
    Add-Result "20" "Pytest" "PASS" $PytestOutput
}
elseif ($PytestOutput -match "failed|error") {
    Add-Result "20" "Pytest" "FAIL" $PytestOutput
}
else {
    Add-Result "20" "Pytest" "NOT VERIFIED" $PytestOutput
}

# ------------------------------------------------------------
# PHASE 2
# ------------------------------------------------------------

Write-Host ""
Write-Host "[6/12] Checking Phase 2 Hardening..."

$Phase2Test = "tests\test_phase2_hardening.py"

if (Test-Path $Phase2Test) {

    $P2 = Run-CommandCapture "python -m pytest `"$Phase2Test`" -q"

    if ($P2 -match "\d+ passed" -and $P2 -notmatch "failed|error") {
        Add-Result "2" "Core Hardening" "PASS" $P2
    }
    else {
        Add-Result "2" "Core Hardening" "FAIL" $P2
    }

}
else {
    Add-Result "2" "Core Hardening" "NOT VERIFIED" "Phase 2 test missing"
}

# ------------------------------------------------------------
# PHASE 3
# ------------------------------------------------------------

Write-Host ""
Write-Host "[7/12] Checking Phase 3 Observability..."

$Phase3Tests = @(
    "tests\test_phase3_http_integration.py",
    "tests\test_phase3_metrics_integration.py",
    "tests\test_phase3_observability.py"
)

$Phase3Found = 0

foreach ($Test in $Phase3Tests) {
    if (Test-Path $Test) {
        $Phase3Found++
    }
}

if ($Phase3Found -eq $Phase3Tests.Count) {

    $P3 = Run-CommandCapture "python -m pytest tests/test_phase3_http_integration.py tests/test_phase3_metrics_integration.py tests/test_phase3_observability.py -q"

    if ($P3 -match "failed|error") {
        Add-Result "3" "Observability" "FAIL" $P3
    }
    elseif ($P3 -match "passed") {
        Add-Result "3" "Observability" "PASS" $P3
    }
    else {
        Add-Result "3" "Observability" "NOT VERIFIED" $P3
    }

}
else {
    Add-Result "3" "Observability" "PARTIAL" "Found $Phase3Found/$($Phase3Tests.Count) expected tests"
}

# ------------------------------------------------------------
# SOURCE ARCHITECTURE SCAN
# ------------------------------------------------------------

Write-Host ""
Write-Host "[8/12] Scanning architecture components..."

$PythonFiles = Get-ChildItem `
    -Path (Join-Path $Root "app") `
    -Filter "*.py" `
    -Recurse `
    -File `
    -ErrorAction SilentlyContinue

$AllSource = ($PythonFiles | ForEach-Object {
    try {
        Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    }
    catch {}
}) -join "`n"

function Check-Keyword {
    param(
        [string]$Phase,
        [string]$Name,
        [string[]]$Keywords
    )

    $Found = $false

    foreach ($Keyword in $Keywords) {
        if ($AllSource -match [regex]::Escape($Keyword)) {
            $Found = $true
            break
        }
    }

    if ($Found) {
        Add-Result $Phase $Name "FOUND" "Keyword/component detected in app source"
    }
    else {
        Add-Result $Phase $Name "NOT FOUND" "No matching component detected"
    }
}

Check-Keyword "4" "Trust" @(
    "Trust",
    "trust",
    "TrustEngine"
)

Check-Keyword "5" "Policy" @(
    "Policy",
    "policy",
    "PolicyEngine"
)

Check-Keyword "6" "Memory" @(
    "Memory",
    "memory",
    "MemoryEngine"
)

Check-Keyword "7" "RAG" @(
    "RAG",
    "rag",
    "KnowledgeEngine",
    "EvidenceGroundingGuard"
)

Check-Keyword "8" "MCP" @(
    "MCP",
    "mcp",
    "MCPServer"
)

Check-Keyword "9" "Tool Governance" @(
    "ToolGovernance",
    "tool_governance",
    "ToolPolicy"
)

Check-Keyword "10" "Experience" @(
    "Experience",
    "experience"
)

Check-Keyword "11" "Feedback" @(
    "Feedback",
    "feedback"
)

Check-Keyword "12" "Evaluation" @(
    "Evaluation",
    "evaluation"
)

Check-Keyword "13" "Failure Analysis" @(
    "FailureAnalysis",
    "failure_analysis"
)

Check-Keyword "14" "Gap Detection" @(
    "GapDetection",
    "gap_detection"
)

Check-Keyword "15" "Knowledge Discovery" @(
    "KnowledgeDiscovery",
    "knowledge_discovery"
)

Check-Keyword "16" "Experiment" @(
    "Experiment",
    "experiment"
)

Check-Keyword "17" "Developer Core" @(
    "DeveloperCore",
    "developer_core"
)

Check-Keyword "18" "Human Approval" @(
    "HumanApproval",
    "human_approval",
    "Approval"
)

# ------------------------------------------------------------
# HERMES / GRAPHIFY
# ------------------------------------------------------------

Write-Host ""
Write-Host "[9/12] Checking Hermes / Graphify..."

$HermesFound = $AllSource -match "Hermes"
$GraphifyFound = $AllSource -match "Graphify"

if ($HermesFound) {
    Add-Result "17" "Hermes" "FOUND" "Hermes references detected"
}
else {
    Add-Result "17" "Hermes" "NOT FOUND" "No Hermes reference detected"
}

if ($GraphifyFound) {
    Add-Result "17" "Graphify" "FOUND" "Graphify references detected; connection still requires runtime verification"
}
else {
    Add-Result "17" "Graphify" "NOT FOUND" "No Graphify reference detected"
}

# ------------------------------------------------------------
# DEVELOPER CORE RUNTIME
# ------------------------------------------------------------

Write-Host ""
Write-Host "[10/12] Running Developer Core self-analysis..."

$DeveloperCommand = @'
python -c "from app.developer_core.engine import DeveloperCoreEngine; import json; e=DeveloperCoreEngine(); r=e.self_analyze(); print(json.dumps(r, ensure_ascii=False, default=str))"
'@

$DeveloperOutput = Run-CommandCapture $DeveloperCommand

if ($DeveloperOutput -match "developer_core" -or $DeveloperOutput -match "status") {
    Add-Result "17" "DeveloperCore.self_analyze" "PASS" $DeveloperOutput
}
elseif ($DeveloperOutput -match "Traceback|Error|Exception") {
    Add-Result "17" "DeveloperCore.self_analyze" "FAIL" $DeveloperOutput
}
else {
    Add-Result "17" "DeveloperCore.self_analyze" "NOT VERIFIED" $DeveloperOutput
}

# ------------------------------------------------------------
# FASTAPI RUNTIME
# ------------------------------------------------------------

Write-Host ""
Write-Host "[11/12] Checking FastAPI runtime..."

$HealthUrl = "http://127.0.0.1:8000/health"

try {

    $Health = Invoke-RestMethod `
        -Uri $HealthUrl `
        -Method Get `
        -TimeoutSec 5 `
        -ErrorAction Stop

    Add-Result "3" "FastAPI /health" "PASS" (($Health | ConvertTo-Json -Compress))

}
catch {

    Add-Result "3" "FastAPI /health" "NOT VERIFIED" "Server unavailable at $HealthUrl"
}

# ------------------------------------------------------------
# V1 CHECK
# ------------------------------------------------------------

try {

    $V1 = Invoke-WebRequest `
        -Uri "http://127.0.0.1:8000/v1" `
        -Method Get `
        -TimeoutSec 5 `
        -ErrorAction Stop

    Add-Result "1" "FastAPI /v1" "PASS" "HTTP $($V1.StatusCode)"

}
catch {

    Add-Result "1" "FastAPI /v1" "NOT VERIFIED" "Endpoint unavailable or route requires another method"
}

# ------------------------------------------------------------
# REPORT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[12/12] Generating report..."

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$PassCount = ($Results | Where-Object {
    $_.Status -in @("PASS","FOUND")
}).Count

$FailCount = ($Results | Where-Object {
    $_.Status -eq "FAIL"
}).Count

$PartialCount = ($Results | Where-Object {
    $_.Status -eq "PARTIAL"
}).Count

$NotVerifiedCount = ($Results | Where-Object {
    $_.Status -in @("NOT VERIFIED","NOT FOUND")
}).Count

$TotalEvidence = $Results.Count

$Confidence = if ($TotalEvidence -gt 0) {
    [math]::Round(($PassCount / $TotalEvidence) * 100, 2)
}
else {
    0
}

$Lines = New-Object System.Collections.Generic.List[string]

$Lines.Add("# NUSANTARA DEEP RUNTIME AUDIT")
$Lines.Add("")
$Lines.Add("Generated: $Now")
$Lines.Add("Repository: $Root")
$Lines.Add("")
$Lines.Add("## IMPORTANT")
$Lines.Add("")
$Lines.Add("This report is evidence-based but does not automatically declare a phase COMPLETE merely because source files exist.")
$Lines.Add("")
$Lines.Add("## Summary")
$Lines.Add("")
$Lines.Add("| Metric | Value |")
$Lines.Add("|---|---:|")
$Lines.Add("| Evidence Checks | $TotalEvidence |")
$Lines.Add("| PASS / FOUND | $PassCount |")
$Lines.Add("| FAIL | $FailCount |")
$Lines.Add("| PARTIAL | $PartialCount |")
$Lines.Add("| NOT VERIFIED / NOT FOUND | $NotVerifiedCount |")
$Lines.Add("| Evidence Confidence | $Confidence% |")
$Lines.Add("")
$Lines.Add("## Evidence")
$Lines.Add("")
$Lines.Add("| Phase | Area | Status | Evidence |")
$Lines.Add("|---|---|---|---|")

foreach ($R in $Results) {

    $Evidence = ($R.Evidence -replace "`r|`n", " ")
    $Evidence = $Evidence -replace "\|", "/"

    if ($Evidence.Length -gt 800) {
        $Evidence = $Evidence.Substring(0,800) + "..."
    }

    $Lines.Add("| $($R.Phase) | $($R.Area) | $($R.Status) | $Evidence |")
}

$Lines.Add("")
$Lines.Add("## Interpretation")
$Lines.Add("")
$Lines.Add("PASS means the corresponding runtime/static evidence succeeded.")
$Lines.Add("")
$Lines.Add("FOUND means the component appears in source code but does NOT prove integration.")
$Lines.Add("")
$Lines.Add("PARTIAL means some evidence exists but completion criteria are not proven.")
$Lines.Add("")
$Lines.Add("NOT VERIFIED means the audit could not establish runtime evidence.")
$Lines.Add("")
$Lines.Add("FAIL means an executable check failed.")
$Lines.Add("")
$Lines.Add("## Recommended Next Action")
$Lines.Add("")
$Lines.Add("Do not implement new features based only on this report.")
$Lines.Add("")
$Lines.Add("Use failed and NOT VERIFIED evidence to determine the next engineering task.")
$Lines.Add("")
$Lines.Add("V1 remains the primary scope until its gates are satisfied.")

$Lines | Set-Content -Path $Report -Encoding UTF8

Write-Host ""
Write-Host "============================================================"
Write-Host " DEEP AUDIT SELESAI"
Write-Host "============================================================"
Write-Host ""
Write-Host "Evidence Checks : $TotalEvidence"
Write-Host "PASS / FOUND   : $PassCount"
Write-Host "FAIL           : $FailCount"
Write-Host "PARTIAL        : $PartialCount"
Write-Host "NOT VERIFIED   : $NotVerifiedCount"
Write-Host "Confidence     : $Confidence%"
Write-Host ""
Write-Host "REPORT:"
Write-Host $Report
Write-Host ""