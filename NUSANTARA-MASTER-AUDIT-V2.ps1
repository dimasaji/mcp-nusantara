# ============================================================
# NUSANTARA AI - MASTER ENGINEERING AUDIT V2
# READ-ONLY AUDIT
# ============================================================

$ErrorActionPreference = "Continue"

$Root = (Get-Location).Path
$ReportDir = Join-Path $Root "audit_reports"
$ReportFile = Join-Path $ReportDir "NUSANTARA-MASTER-AUDIT-V2.md"

New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null

$Findings = New-Object System.Collections.Generic.List[object]

$Pass = 0
$Warn = 0
$Fail = 0
$Info = 0

function Add-Finding {
    param(
        [string]$Area,
        [string]$Status,
        [string]$Finding,
        [string]$Evidence,
        [string]$Action
    )

    $item = [PSCustomObject]@{
        Area = $Area
        Status = $Status
        Finding = $Finding
        Evidence = $Evidence
        Action = $Action
    }

    $Findings.Add($item)

    if ($Status -eq "PASS") { $script:Pass++ }
    elseif ($Status -eq "WARN") { $script:Warn++ }
    elseif ($Status -eq "FAIL") { $script:Fail++ }
    elseif ($Status -eq "INFO") { $script:Info++ }

    Write-Host ("[{0}] {1} - {2}" -f $Status, $Area, $Finding)
}

function Exists {
    param([string]$RelativePath)

    return Test-Path -LiteralPath (Join-Path $Root $RelativePath)
}

function Read-Safe {
    param([string]$RelativePath)

    $path = Join-Path $Root $RelativePath

    if (-not (Test-Path -LiteralPath $path)) {
        return ""
    }

    try {
        return Get-Content -LiteralPath $path -Raw -ErrorAction Stop
    }
    catch {
        return ""
    }
}

function Contains-Text {
    param(
        [string]$RelativePath,
        [string]$Text
    )

    $content = Read-Safe $RelativePath

    if ([string]::IsNullOrEmpty($content)) {
        return $false
    }

    return $content.Contains($Text)
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA AI - MASTER ENGINEERING AUDIT V2" -ForegroundColor Cyan
Write-Host " READ-ONLY" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# 1. BASELINE
# ============================================================

Write-Host "=== 1. BASELINE ===" -ForegroundColor Cyan

if (Exists ".git") {
    Add-Finding `
        "Baseline" `
        "PASS" `
        "Git repository terdeteksi." `
        ".git" `
        ""
}
else {
    Add-Finding `
        "Baseline" `
        "WARN" `
        "Git repository tidak terdeteksi." `
        ".git" `
        "Audit git manual diperlukan."
}

if (Exists "app") {
    Add-Finding `
        "Baseline" `
        "PASS" `
        "Direktori app tersedia." `
        "app" `
        ""
}
else {
    Add-Finding `
        "Baseline" `
        "FAIL" `
        "Direktori app tidak ditemukan." `
        "app" `
        "Repository tidak terlihat seperti struktur Nusantara yang diharapkan."
}

$pyFiles = @(Get-ChildItem -Path $Root -Recurse -File -Filter "*.py" -ErrorAction SilentlyContinue)

Add-Finding `
    "Baseline" `
    "INFO" `
    ("Jumlah file Python terdeteksi: {0}" -f $pyFiles.Count) `
    "Recursive Python scan" `
    ""

# ============================================================
# 2. ARCHITECTURE CONTRACT
# ============================================================

Write-Host ""
Write-Host "=== 2. ARCHITECTURE CONTRACT ===" -ForegroundColor Cyan

$architectureCandidates = @(
    "docs\NUSANTARA-V1-ARCHITECTURE-CONTRACT.md",
    "docs\architecture\NUSANTARA-V1-ARCHITECTURE-CONTRACT.md",
    "docs\NUSANTARA-ARCHITECTURE-CONTRACT-V1.md",
    "NUSANTARA-V1-ARCHITECTURE-CONTRACT.md"
)

$architectureFound = $false

foreach ($candidate in $architectureCandidates) {
    if (Exists $candidate) {
        $architectureFound = $true

        Add-Finding `
            "Architecture" `
            "PASS" `
            "Architecture Contract ditemukan." `
            $candidate `
            ""

        break
    }
}

if (-not $architectureFound) {
    Add-Finding `
        "Architecture" `
        "WARN" `
        "Architecture Contract tidak ditemukan pada lokasi kandidat." `
        "Architecture contract candidates" `
        "Audit manual nama/lokasi dokumen diperlukan."
}

# ============================================================
# 3. CORE HARDENING
# ============================================================

Write-Host ""
Write-Host "=== 3. CORE HARDENING ===" -ForegroundColor Cyan

$hardeningFiles = @(
    "app\core\hardening\validator.py",
    "app\core\hardening\timeout.py",
    "app\core\hardening\retry.py",
    "app\core\hardening\circuit_breaker.py",
    "app\core\hardening\safe_execution.py"
)

foreach ($file in $hardeningFiles) {
    if (Exists $file) {
        Add-Finding `
            "Core Hardening" `
            "PASS" `
            ("Komponen ditemukan: {0}" -f $file) `
            $file `
            ""
    }
    else {
        Add-Finding `
            "Core Hardening" `
            "WARN" `
            ("Komponen tidak ditemukan: {0}" -f $file) `
            $file `
            "Periksa apakah implementasi berada pada lokasi lain."
    }
}

$phase2Tests = @(
    "tests\test_phase2_hardening.py",
    "tests\v2\test_phase2_hardening.py"
)

$phase2TestFound = $false

foreach ($test in $phase2Tests) {
    if (Exists $test) {
        $phase2TestFound = $true

        Add-Finding `
            "Core Hardening" `
            "PASS" `
            "Targeted Phase 2 test ditemukan." `
            $test `
            ""

        break
    }
}

if (-not $phase2TestFound) {
    Add-Finding `
        "Core Hardening" `
        "WARN" `
        "Targeted Phase 2 test tidak ditemukan." `
        "Phase 2 test candidates" `
        ""
}

# ============================================================
# 4. OBSERVABILITY
# ============================================================

Write-Host ""
Write-Host "=== 4. OBSERVABILITY ===" -ForegroundColor Cyan

$observabilityFiles = @(
    "app\observability\context.py",
    "app\observability\logging.py",
    "app\observability\metrics.py"
)

foreach ($file in $observabilityFiles) {
    if (Exists $file) {
        Add-Finding `
            "Observability" `
            "PASS" `
            ("Komponen ditemukan: {0}" -f $file) `
            $file `
            ""
    }
    else {
        Add-Finding `
            "Observability" `
            "WARN" `
            ("Komponen tidak ditemukan: {0}" -f $file) `
            $file `
            ""
    }
}

$phase3Tests = @(
    "tests\test_phase3_observability.py",
    "tests\test_phase3_http_integration.py",
    "tests\test_phase3_metrics_integration.py"
)

foreach ($test in $phase3Tests) {
    if (Exists $test) {
        Add-Finding `
            "Observability" `
            "PASS" `
            ("Phase 3 test ditemukan: {0}" -f $test) `
            $test `
            ""
    }
    else {
        Add-Finding `
            "Observability" `
            "WARN" `
            ("Phase 3 test tidak ditemukan: {0}" -f $test) `
            $test `
            ""
    }
}

# ============================================================
# 5. GOVERNANCE
# ============================================================

Write-Host ""
Write-Host "=== 5. TOOL GOVERNANCE ===" -ForegroundColor Cyan

$governance = "app\governance\tools.py"

if (Exists $governance) {

    Add-Finding `
        "Governance" `
        "PASS" `
        "Governance tool registry ditemukan." `
        $governance `
        ""

    $gov = Read-Safe $governance

    $checks = @(
        @{ Name = "Risk"; Text = "Risk" },
        @{ Name = "Decision"; Text = "Decision" },
        @{ Name = "permission"; Text = "permission" },
        @{ Name = "approval"; Text = "approval" },
        @{ Name = "audit"; Text = "audit" },
        @{ Name = "schema validation"; Text = "validate_schema" },
        @{ Name = "safe execution"; Text = "safe_call" }
    )

    foreach ($check in $checks) {
        if ($gov.Contains($check.Text)) {
            Add-Finding `
                "Governance" `
                "PASS" `
                ("Governance memiliki indikator: {0}" -f $check.Name) `
                $governance `
                ""
        }
        else {
            Add-Finding `
                "Governance" `
                "WARN" `
                ("Indikator governance tidak terdeteksi: {0}" -f $check.Name) `
                $governance `
                "Audit manual diperlukan."
        }
    }
}
else {
    Add-Finding `
        "Governance" `
        "WARN" `
        "Governance registry tidak ditemukan pada lokasi standar." `
        $governance `
        ""
}

# ============================================================
# 6. APPROVAL / AUDIT
# ============================================================

Write-Host ""
Write-Host "=== 6. APPROVAL AND AUDIT ===" -ForegroundColor Cyan

$approvalPaths = @(
    "app\approval",
    "app\audit",
    "app\observability"
)

foreach ($path in $approvalPaths) {
    if (Exists $path) {
        Add-Finding `
            "Approval/Audit" `
            "PASS" `
            ("Direktori tersedia: {0}" -f $path) `
            $path `
            ""
    }
    else {
        Add-Finding `
            "Approval/Audit" `
            "INFO" `
            ("Direktori tidak ditemukan: {0}" -f $path) `
            $path `
            "Pastikan fungsi approval/audit tetap memiliki single source of truth."
    }
}

# ============================================================
# 7. MEMORY
# ============================================================

Write-Host ""
Write-Host "=== 7. MEMORY ===" -ForegroundColor Cyan

$memoryPaths = @(
    "app\memory",
    "memory"
)

$memoryFound = $false

foreach ($path in $memoryPaths) {
    if (Exists $path) {
        $memoryFound = $true

        Add-Finding `
            "Memory" `
            "PASS" `
            ("Memory layer ditemukan: {0}" -f $path) `
            $path `
            ""
    }
}

if (-not $memoryFound) {
    Add-Finding `
        "Memory" `
        "INFO" `
        "Memory layer belum ditemukan pada lokasi standar." `
        "memory candidates" `
        "Tidak otomatis dianggap defect karena Phase Memory belum final."
}

# ============================================================
# 8. RAG
# ============================================================

Write-Host ""
Write-Host "=== 8. RAG ===" -ForegroundColor Cyan

$ragPaths = @(
    "app\rag",
    "rag"
)

$ragFound = $false

foreach ($path in $ragPaths) {
    if (Exists $path) {
        $ragFound = $true

        Add-Finding `
            "RAG" `
            "PASS" `
            ("RAG layer ditemukan: {0}" -f $path) `
            $path `
            ""
    }
}

if (-not $ragFound) {
    Add-Finding `
        "RAG" `
        "INFO" `
        "RAG layer belum ditemukan pada lokasi standar." `
        "rag candidates" `
        "Phase RAG belum final."
}

# ============================================================
# 9. MCP
# ============================================================

Write-Host ""
Write-Host "=== 9. MCP ===" -ForegroundColor Cyan

$mcpPaths = @(
    "app\mcp",
    "mcp",
    "app\core\mcp"
)

$mcpFound = $false

foreach ($path in $mcpPaths) {
    if (Exists $path) {
        $mcpFound = $true

        Add-Finding `
            "MCP" `
            "PASS" `
            ("MCP layer ditemukan: {0}" -f $path) `
            $path `
            ""
    }
}

if (-not $mcpFound) {
    Add-Finding `
        "MCP" `
        "INFO" `
        "MCP layer belum ditemukan pada lokasi standar." `
        "MCP candidates" `
        "Phase MCP belum final."
}

# ============================================================
# 10. SECURITY BASELINE
# ============================================================

Write-Host ""
Write-Host "=== 10. SECURITY BASELINE ===" -ForegroundColor Cyan

$securityFiles = @(
    "app\security",
    "app\governance",
    "app\core\hardening"
)

foreach ($path in $securityFiles) {
    if (Exists $path) {
        Add-Finding `
            "Security" `
            "PASS" `
            ("Security-related layer ditemukan: {0}" -f $path) `
            $path `
            ""
    }
    else {
        Add-Finding `
            "Security" `
            "INFO" `
            ("Security-related layer tidak ditemukan: {0}" -f $path) `
            $path `
            ""
    }
}

# Simple textual scan.
# This scan is deliberately informational.
$securityTerms = @(
    "os.system(",
    "shell=True",
    "subprocess.",
    "eval(",
    "exec("
)

foreach ($py in $pyFiles) {

    if ($py.FullName -like "*\tests\*") {
        continue
    }

    try {
        $content = Get-Content -LiteralPath $py.FullName -Raw -ErrorAction Stop

        foreach ($term in $securityTerms) {

            if ($content.Contains($term)) {

                $relative = $py.FullName.Substring($Root.Length).TrimStart("\","/")

                Add-Finding `
                    "Security" `
                    "WARN" `
                    ("Pattern sensitif terdeteksi: {0}" -f $term) `
                    $relative `
                    "Audit konteks manual diperlukan; tidak otomatis berarti vulnerability."
            }
        }
    }
    catch {
        Add-Finding `
            "Security" `
            "WARN" `
            ("Tidak dapat membaca file: {0}" -f $py.Name) `
            $py.FullName `
            ""
    }
}

# ============================================================
# 11. CONTRACTS
# ============================================================

Write-Host ""
Write-Host "=== 11. CONTRACTS ===" -ForegroundColor Cyan

$contractFiles = @(
    "docs\NUSANTARA-GATES-V1.md",
    "docs\NUSANTARA-V1-DEVELOPER-CONTRACT.md",
    "docs\NUSANTARA-DEVELOPER-CONTRACT-V1.md",
    "NUSANTARA-GATES-V1.md",
    "NUSANTARA-DEVELOPER-CONTRACT-V1.md"
)

foreach ($file in $contractFiles) {
    if (Exists $file) {
        Add-Finding `
            "Contracts" `
            "PASS" `
            ("Contract ditemukan: {0}" -f $file) `
            $file `
            ""
    }
}

# ============================================================
# 12. TEST INVENTORY
# ============================================================

Write-Host ""
Write-Host "=== 12. TEST INVENTORY ===" -ForegroundColor Cyan

$testFiles = @(Get-ChildItem `
    -Path (Join-Path $Root "tests") `
    -Recurse `
    -File `
    -Filter "*.py" `
    -ErrorAction SilentlyContinue)

Add-Finding `
    "Testing" `
    "INFO" `
    ("Jumlah file test Python: {0}" -f $testFiles.Count) `
    "tests" `
    ""

# Duplicate test basename detection.
$duplicates = $testFiles |
    Group-Object Name |
    Where-Object { $_.Count -gt 1 }

foreach ($dup in $duplicates) {
    Add-Finding `
        "Testing" `
        "WARN" `
        ("Duplicate test basename: {0}" -f $dup.Name) `
        "tests" `
        "Gunakan pytest --import-mode=importlib bila diperlukan."
}

# ============================================================
# 13. PYPROJECT
# ============================================================

Write-Host ""
Write-Host "=== 13. PYPROJECT ===" -ForegroundColor Cyan

if (Exists "pyproject.toml") {

    Add-Finding `
        "Build/Test Configuration" `
        "PASS" `
        "pyproject.toml ditemukan." `
        "pyproject.toml" `
        ""

    $pyproject = Read-Safe "pyproject.toml"

    if ($pyproject.Contains("pytest")) {
        Add-Finding `
            "Build/Test Configuration" `
            "PASS" `
            "Konfigurasi pytest terdeteksi." `
            "pyproject.toml" `
            ""
    }
}
else {
    Add-Finding `
        "Build/Test Configuration" `
        "WARN" `
        "pyproject.toml tidak ditemukan." `
        "pyproject.toml" `
        ""
}

# ============================================================
# 14. GIT STATUS
# ============================================================

Write-Host ""
Write-Host "=== 14. GIT STATUS ===" -ForegroundColor Cyan

if (Exists ".git") {

    try {
        $gitStatus = git status --short 2>&1

        if ($LASTEXITCODE -eq 0) {

            if ([string]::IsNullOrWhiteSpace(($gitStatus -join ""))) {
                Add-Finding `
                    "Git" `
                    "PASS" `
                    "Working tree bersih." `
                    "git status --short" `
                    ""
            }
            else {
                Add-Finding `
                    "Git" `
                    "INFO" `
                    "Working tree memiliki perubahan." `
                    "git status --short" `
                    "Audit perubahan sebelum release."
            }
        }
        else {
            Add-Finding `
                "Git" `
                "WARN" `
                "git status gagal dijalankan." `
                "git status --short" `
                ""
        }
    }
    catch {
        Add-Finding `
            "Git" `
            "WARN" `
            "Git tidak dapat diperiksa." `
            ".git" `
            ""
    }
}

# ============================================================
# 15. TARGETED TESTS
# ============================================================

Write-Host ""
Write-Host "=== 15. TARGETED TEST EXECUTION ===" -ForegroundColor Cyan

$targetedTests = @(
    "tests\test_phase2_hardening.py",
    "tests\test_phase3_observability.py",
    "tests\test_phase3_http_integration.py",
    "tests\test_phase3_metrics_integration.py"
)

foreach ($test in $targetedTests) {

    if (-not (Exists $test)) {
        continue
    }

    Write-Host ("Running: {0}" -f $test) -ForegroundColor Yellow

    $output = & python -m pytest $test -q 2>&1
    $exitCode = $LASTEXITCODE

    $joined = ($output -join "`n")

    if ($exitCode -eq 0) {

        Add-Finding `
            "Targeted Testing" `
            "PASS" `
            ("Test berhasil: {0}" -f $test) `
            $joined `
            ""
    }
    else {

        Add-Finding `
            "Targeted Testing" `
            "FAIL" `
            ("Test gagal: {0}" -f $test) `
            $joined `
            "Periksa failure sebelum phase dinyatakan final."
    }
}

# ============================================================
# 16. FULL REGRESSION
# ============================================================

Write-Host ""
Write-Host "=== 16. FULL REGRESSION ===" -ForegroundColor Cyan

Write-Host "Running full pytest..." -ForegroundColor Yellow

$fullOutput = & python -m pytest -q --import-mode=importlib 2>&1
$fullExit = $LASTEXITCODE

$fullJoined = ($fullOutput -join "`n")

if ($fullExit -eq 0) {

    Add-Finding `
        "Full Regression" `
        "PASS" `
        "Full pytest regression berhasil." `
        $fullJoined `
        ""
}
else {

    Add-Finding `
        "Full Regression" `
        "FAIL" `
        "Full pytest regression gagal atau menghasilkan non-zero exit code." `
        $fullJoined `
        "Failure harus dianalisis sebelum phase final."
}

# ============================================================
# 17. PHASE ASSESSMENT
# ============================================================

Write-Host ""
Write-Host "=== 17. PHASE ASSESSMENT ===" -ForegroundColor Cyan

$phase0 = $true
$phase1 = $architectureFound
$phase2 = $false
$phase3 = $false

$phase2Finding = $Findings |
    Where-Object {
        $_.Area -eq "Targeted Testing" -and
        $_.Finding -like "*test_phase2_hardening.py*"
    } |
    Select-Object -Last 1

if ($phase2Finding -and $phase2Finding.Status -eq "PASS") {
    $phase2 = $true
}

$phase3Results = $Findings |
    Where-Object {
        $_.Area -eq "Targeted Testing" -and
        (
            $_.Finding -like "*test_phase3_observability.py*" -or
            $_.Finding -like "*test_phase3_http_integration.py*" -or
            $_.Finding -like "*test_phase3_metrics_integration.py*"
        )
    }

$phase3Fail = $phase3Results |
    Where-Object { $_.Status -eq "FAIL" }

$phase3Expected = 3
$phase3Passed = @($phase3Results | Where-Object { $_.Status -eq "PASS" }).Count

if ($phase3Passed -eq $phase3Expected -and $phase3Fail.Count -eq 0) {
    $phase3 = $true
}

Add-Finding `
    "Phase Assessment" `
    "INFO" `
    ("Phase 0 Baseline: {0}" -f $(if ($phase0) { "READY" } else { "NOT READY" })) `
    "" `
    ""

Add-Finding `
    "Phase Assessment" `
    "INFO" `
    ("Phase 1 Architecture: {0}" -f $(if ($phase1) { "DOCUMENT FOUND" } else { "DOCUMENT NOT CONFIRMED" })) `
    "" `
    ""

Add-Finding `
    "Phase Assessment" `
    "INFO" `
    ("Phase 2 Hardening: {0}" -f $(if ($phase2) { "TARGETED TEST PASS" } else { "NOT VERIFIED BY THIS AUDIT" })) `
    "" `
    ""

Add-Finding `
    "Phase Assessment" `
    "INFO" `
    ("Phase 3 Observability: {0}" -f $(if ($phase3) { "TARGETED TESTS PASS" } else { "NOT VERIFIED BY THIS AUDIT" })) `
    "" `
    ""

# ============================================================
# 18. OVERALL STATUS
# ============================================================

$overallStatus = "PASS"

if ($Fail -gt 0) {
    $overallStatus = "FAIL"
}
elseif ($Warn -gt 0) {
    $overallStatus = "WARN"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ("OVERALL STATUS: {0}" -f $overallStatus) -ForegroundColor Magenta
Write-Host ("PASS: {0}" -f $Pass)
Write-Host ("WARN: {0}" -f $Warn)
Write-Host ("FAIL: {0}" -f $Fail)
Write-Host ("INFO: {0}" -f $Info)
Write-Host "============================================================" -ForegroundColor Cyan

# ============================================================
# 19. REPORT
# ============================================================

$report = New-Object System.Collections.Generic.List[string]

$report.Add("# NUSANTARA AI - MASTER ENGINEERING AUDIT V2")
$report.Add("")
$report.Add("Repository: $Root")
$report.Add("")
$report.Add("Audit Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")")
$report.Add("")
$report.Add("Mode: READ-ONLY")
$report.Add("")
$report.Add("## Overall Status")
$report.Add("")
$report.Add("**$overallStatus**")
$report.Add("")
$report.Add("| Metric | Count |")
$report.Add("|---|---:|")
$report.Add("| PASS | $Pass |")
$report.Add("| WARN | $Warn |")
$report.Add("| FAIL | $Fail |")
$report.Add("| INFO | $Info |")
$report.Add("")
$report.Add("## Findings")
$report.Add("")
$report.Add("| Area | Status | Finding | Evidence | Action |")
$report.Add("|---|---|---|---|---|")

foreach ($f in $Findings) {

    $findingText = [string]$f.Finding
    $evidenceText = [string]$f.Evidence
    $actionText = [string]$f.Action

    $findingText = $findingText.Replace("|", "/")
    $evidenceText = $evidenceText.Replace("|", "/")
    $actionText = $actionText.Replace("|", "/")

    $report.Add(
        "| $($f.Area) | $($f.Status) | $findingText | $evidenceText | $actionText |"
    )
}

$report.Add("")
$report.Add("## Engineering Rule")
$report.Add("")
$report.Add("A phase is not FINAL merely because source files exist.")
$report.Add("")
$report.Add("Expected evidence:")
$report.Add("")
$report.Add("IMPLEMENTATION + TARGETED TEST + SECURITY + FULL REGRESSION + EVIDENCE")
$report.Add("")
$report.Add("This audit does not modify production source code.")
$report.Add("")
$report.Add("Findings must be analyzed before implementation changes are made.")

Set-Content `
    -LiteralPath $ReportFile `
    -Value $report `
    -Encoding UTF8

Write-Host ""
Write-Host ("REPORT: {0}" -f $ReportFile) -ForegroundColor Green
Write-Host "AUDIT COMPLETE" -ForegroundColor Green
