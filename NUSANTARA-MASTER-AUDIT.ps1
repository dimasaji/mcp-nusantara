# ============================================================
# NUSANTARA AI â€” MASTER ENGINEERING AUDIT V1
# ID       : NUSANTARA-MASTER-AUDIT-V1
# MODE     : READ-ONLY
# PURPOSE  : Audit struktur, kontrak, testing, security,
#            observability, governance, memory, RAG, MCP
#            tanpa mengubah source code.
#
# REQUIREMENT:
#   PowerShell 5+ / PowerShell 7+
#
# RUN:
#   powershell -ExecutionPolicy Bypass -File .\NUSANTARA-MASTER-AUDIT.ps1
# ============================================================

$ErrorActionPreference = "Continue"

# ------------------------------------------------------------
# ROOT
# ------------------------------------------------------------

$Root = (Get-Location).Path

$ReportDir = Join-Path $Root "audit_reports"
$ReportFile = Join-Path $ReportDir "NUSANTARA-MASTER-AUDIT.md"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$Findings = New-Object System.Collections.Generic.List[object]
$Evidence = New-Object System.Collections.Generic.List[string]

$Pass = 0
$Warn = 0
$Fail = 0
$Info = 0

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

function Add-Finding {
    param(
        [string]$Area,
        [string]$Status,
        [string]$Finding,
        [string]$EvidenceText = "",
        [string]$Recommendation = ""
    )

    switch ($Status) {
        "PASS" { $script:Pass++ }
        "WARN" { $script:Warn++ }
        "FAIL" { $script:Fail++ }
        "INFO" { $script:Info++ }
    }

    $obj = [PSCustomObject]@{
        Area          = $Area
        Status        = $Status
        Finding       = $Finding
        Evidence      = $EvidenceText
        Recommendation = $Recommendation
    }

    $script:Findings.Add($obj)

    $symbol = switch ($Status) {
        "PASS" { "[PASS]" }
        "WARN" { "[WARN]" }
        "FAIL" { "[FAIL]" }
        "INFO" { "[INFO]" }
    }

    $color = switch ($Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
        "INFO" { "Cyan" }
    }

    Write-Host "$symbol $Area - $Finding" -ForegroundColor $color
}

function Test-PathExists {
    param([string]$RelativePath)

    return Test-Path (Join-Path $Root $RelativePath)
}

function Read-TextSafe {
    param([string]$RelativePath)

    $path = Join-Path $Root $RelativePath

    if (-not (Test-Path $path)) {
        return ""
    }

    try {
        return Get-Content -Raw -LiteralPath $path -ErrorAction Stop
    }
    catch {
        return ""
    }
}

function Count-Files {
    param([string]$RelativePath)

    $path = Join-Path $Root $RelativePath

    if (-not (Test-Path $path)) {
        return 0
    }

    try {
        return @(Get-ChildItem -LiteralPath $path -File -Recurse -ErrorAction SilentlyContinue).Count
    }
    catch {
        return 0
    }
}

function Has-Text {
    param(
        [string]$RelativePath,
        [string]$Pattern
    )

    $content = Read-TextSafe $RelativePath

    if ([string]::IsNullOrEmpty($content)) {
        return $false
    }

    return $content -match $Pattern
}

function Get-PythonFiles {
    try {
        return @(Get-ChildItem -Path $Root -Recurse -File -Filter "*.py" `
            -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch "\\\.git\\" -and
                $_.FullName -notmatch "\\__pycache__\\"
            })
    }
    catch {
        return @()
    }
}

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

Clear-Host

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        NUSANTARA AI â€” MASTER ENGINEERING AUDIT V1" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repository : $Root"
Write-Host "Mode       : READ-ONLY"
Write-Host "Date       : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# ------------------------------------------------------------
# 1. REPOSITORY BASELINE
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 1. REPOSITORY BASELINE ===" -ForegroundColor Cyan

if (Test-Path (Join-Path $Root ".git")) {
    Add-Finding `
        "Repository" `
        "PASS" `
        "Git repository terdeteksi." `
        ".git tersedia." `
        "Gunakan Git history sebagai audit trail."
}
else {
    Add-Finding `
        "Repository" `
        "WARN" `
        "Git repository tidak terdeteksi." `
        ".git tidak ditemukan." `
        "Pastikan repository memiliki version control."
}

$pyFiles = Get-PythonFiles

Add-Finding `
    "Repository" `
    "INFO" `
    "Python source files terdeteksi: $($pyFiles.Count)" `
    "Recursive scan *.py." `
    "Tidak ada tindakan."
    
# ------------------------------------------------------------
# 2. ARCHITECTURE
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 2. ARCHITECTURE INTEGRITY ===" -ForegroundColor Cyan

$architectureCandidates = @(
    "docs\architecture\ARCHITECTURE-CONTRACT.md",
    "docs\architecture\ARCHITECTURE.md",
    "docs\contracts\ARCHITECTURE-CONTRACT.md"
)

$architectureFound = $false

foreach ($p in $architectureCandidates) {
    if (Test-PathExists $p) {
        $architectureFound = $true
        Add-Finding `
            "Architecture" `
            "PASS" `
            "Architecture contract ditemukan." `
            $p `
            "Pertahankan sebagai source of architectural truth."
        break
    }
}

if (-not $architectureFound) {
    Add-Finding `
        "Architecture" `
        "WARN" `
        "Architecture contract belum ditemukan pada lokasi standar." `
        ($architectureCandidates -join ", ") `
        "Dokumentasikan architecture contract."
}

$coreCandidates = @(
    "app\core",
    "app\devcore",
    "app\v2"
)

$coreFound = @(
    $coreCandidates | Where-Object { Test-PathExists $_ }
).Count

if ($coreFound -gt 0) {
    Add-Finding `
        "Architecture" `
        "PASS" `
        "Core-related directories terdeteksi." `
        ($coreCandidates -join ", ") `
        "Audit dependency direction sebelum refactor besar."
}
else {
    Add-Finding `
        "Architecture" `
        "WARN" `
        "Core directory standar tidak ditemukan." `
        "Tidak ditemukan app/core, app/devcore, atau app/v2." `
        "Periksa struktur repository."
}

# ------------------------------------------------------------
# 3. HARDENING
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 3. CORE HARDENING ===" -ForegroundColor Cyan

$hardeningFiles = @(
    "app\core\hardening\validator.py",
    "app\core\hardening\timeout.py",
    "app\core\hardening\retry.py",
    "app\core\hardening\circuit_breaker.py",
    "app\core\hardening\safe_execution.py"
)

$hardeningMissing = @()

foreach ($p in $hardeningFiles) {
    if (Test-PathExists $p) {
        Add-Finding `
            "Hardening" `
            "PASS" `
            "$p tersedia." `
            $p `
            ""
    }
    else {
        $hardeningMissing += $p
    }
}

if ($hardeningMissing.Count -gt 0) {
    Add-Finding `
        "Hardening" `
        "WARN" `
        "Sebagian komponen hardening tidak ditemukan." `
        ($hardeningMissing -join ", ") `
        "Audit apakah fungsi tersebut berada di lokasi lain."
}

# ------------------------------------------------------------
# 4. OBSERVABILITY
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 4. OBSERVABILITY ===" -ForegroundColor Cyan

$obsFiles = @(
    "app\observability\context.py",
    "app\observability\logging.py",
    "app\observability\metrics.py"
)

foreach ($p in $obsFiles) {
    if (Test-PathExists $p) {
        Add-Finding `
            "Observability" `
            "PASS" `
            "$p tersedia." `
            $p `
            ""
    }
    else {
        Add-Finding `
            "Observability" `
            "WARN" `
            "$p tidak ditemukan." `
            "" `
            "Periksa apakah fungsi observability berada pada module existing."
    }
}

$testObs = @(
    "tests\test_phase3_observability.py",
    "tests\test_phase3_http_integration.py",
    "tests\test_phase3_metrics_integration.py"
)

foreach ($p in $testObs) {
    if (Test-PathExists $p) {
        Add-Finding `
            "Observability Test" `
            "PASS" `
            "Test observability ditemukan." `
            $p `
            ""
    }
    else {
        Add-Finding `
            "Observability Test" `
            "WARN" `
            "Test observability tidak ditemukan." `
            $p `
            "Periksa test coverage."
    }
}

# ------------------------------------------------------------
# 5. GOVERNANCE
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 5. TOOL GOVERNANCE ===" -ForegroundColor Cyan

$governance = "app\governance\tools.py"

if (Test-PathExists $governance) {
    Add-Finding `
        "Governance" `
        "PASS" `
        "GovernedToolRegistry ditemukan." `
        $governance `
        "Pertahankan registry sebagai single tool governance boundary."

    $g = Read-TextSafe $governance

    $checks = @(
        @{ Name = "Decision"; Pattern = "Decision" },
        @{ Name = "Risk"; Pattern = "Risk" },
        @{ Name = "Permission"; Pattern = "permission" },
        @{ Name = "Approval"; Pattern = "approval" },
        @{ Name = "Audit"; Pattern = "audit" },
        @{ Name = "Schema validation"; Pattern = "validate_schema" },
        @{ Name = "safe_call"; Pattern = "safe_call" }
    )

    foreach ($c in $checks) {
        if ($g -match $c.Pattern) {
            Add-Finding `
                "Governance" `
                "PASS" `
                "$($c.Name) ditemukan dalam governance." `
                $c.Pattern `
                ""
        }
        else {
            Add-Finding `
                "Governance" `
                "WARN" `
                "$($c.Name) tidak terdeteksi secara tekstual." `
                $c.Pattern `
                "Audit manual diperlukan."
        }
    }
}
else {
    Add-Finding `
        "Governance" `
        "FAIL" `
        "GovernedToolRegistry tidak ditemukan." `
        $governance `
        "Tool execution governance harus memiliki boundary."
}

# ------------------------------------------------------------
# 6. APPROVAL / AUDIT
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 6. APPROVAL & AUDIT ===" -ForegroundColor Cyan

$approvalDirs = @(
    "app\approval",
    "app\observability"
)

foreach ($p in $approvalDirs) {
    if (Test-PathExists $p) {
        Add-Finding `
            "Approval/Audit" `
            "PASS" `
            "$p tersedia." `
            $p `
            ""
    }
    else {
        Add-Finding `
            "Approval/Audit" `
            "WARN" `
            "$p tidak ditemukan." `
            $p `
            "Audit approval architecture."
    }
}

# ------------------------------------------------------------
# 7. MEMORY
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 7. MEMORY GOVERNANCE ===" -ForegroundColor Cyan

$memoryDirs = @(
    "app\memory",
    "memory"
)

$memoryFound = $false

foreach ($p in $memoryDirs) {
    if (Test-PathExists $p) {
        $memoryFound = $true

        Add-Finding `
            "Memory" `
            "PASS" `
            "Memory subsystem ditemukan." `
            $p `
            "Audit policy penyimpanan memory."
    }
}

if (-not $memoryFound) {
    Add-Finding `
        "Memory" `
        "INFO" `
        "Memory subsystem belum ditemukan pada lokasi standar." `
        "" `
        "Belum berarti defect."
}

# ------------------------------------------------------------
# 8. RAG
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 8. RAG ===" -ForegroundColor Cyan

$ragDirs = @(
    "app\rag",
    "rag"
)

$ragFound = $false

foreach ($p in $ragDirs) {
    if (Test-PathExists $p) {
        $ragFound = $true

        Add-Finding `
            "RAG" `
            "PASS" `
            "RAG subsystem ditemukan." `
            $p `
            "Audit provenance, versioning, citation dan conflict detection."
    }
}

if (-not $ragFound) {
    Add-Finding `
        "RAG" `
        "INFO" `
        "RAG subsystem belum ditemukan pada lokasi standar." `
        "" `
        "Belum berarti defect."
}

# ------------------------------------------------------------
# 9. MCP
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 9. MCP ===" -ForegroundColor Cyan

$mcpDirs = @(
    "app\mcp",
    "mcp"
)

$mcpFound = $false

foreach ($p in $mcpDirs) {
    if (Test-PathExists $p) {
        $mcpFound = $true

        Add-Finding `
            "MCP" `
            "PASS" `
            "MCP subsystem ditemukan." `
            $p `
            "Audit adapter, permission, timeout, risk dan external trust boundary."
    }
}

if (-not $mcpFound) {
    Add-Finding `
        "MCP" `
        "INFO" `
        "MCP subsystem belum ditemukan pada lokasi standar." `
        "" `
        "Belum berarti defect."
}

# ------------------------------------------------------------
# 10. SECURITY SCAN
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 10. SECURITY BASELINE SCAN ===" -ForegroundColor Cyan


$securityHits = New-Object System.Collections.Generic.List[string]

foreach ($file in $pyFiles) {

    try {
        $lines = Get-Content -LiteralPath $file.FullName -ErrorAction SilentlyContinue

        $lineNumber = 0

        foreach ($line in $lines) {
            $lineNumber++

            foreach ($pattern in $secretPatterns) {
                if ($line -match $pattern) {

                    $relative = $file.FullName.Substring($Root.Length).TrimStart("\","/")

                    $securityHits.Add(
                        "$relative : line $lineNumber : pattern=$pattern"
                    )

                    break
                }
            }
        }
    }
    catch {
        # Read-only scanner: ignore unreadable files.
    }
}

if ($securityHits.Count -eq 0) {
    Add-Finding `
        "Security" `
        "PASS" `
        "Baseline credential pattern scanner tidak menemukan hit." `
        "Python source scan." `
        "Tetap gunakan security scanner existing."
}
else {
    Add-Finding `
        "Security" `
        "WARN" `
        "Credential-like pattern ditemukan: $($securityHits.Count)." `
        ($securityHits -join "`n") `
        "Audit setiap finding; dummy test fixture harus dibedakan dari credential nyata."
}

# ------------------------------------------------------------
# 11. TEST STRUCTURE
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 11. TEST STRUCTURE ===" -ForegroundColor Cyan

$testsPath = Join-Path $Root "tests"

if (Test-Path $testsPath) {

    $testFiles = @(Get-ChildItem $testsPath -Recurse -File `
        -Filter "test_*.py" -ErrorAction SilentlyContinue)

    Add-Finding `
        "Testing" `
        "PASS" `
        "Test files ditemukan: $($testFiles.Count)." `
        "tests/ recursive scan." `
        "Full regression harus tetap dijalankan."

    $duplicateNames = $testFiles |
        Group-Object Name |
        Where-Object { $_.Count -gt 1 }

    if ($duplicateNames.Count -gt 0) {

        foreach ($dup in $duplicateNames) {
            $paths = $dup.Group |
                ForEach-Object {
                    $_.FullName.Substring($Root.Length).TrimStart("\","/")
                }

            Add-Finding `
                "Testing" `
                "WARN" `
                "Duplicate test filename: $($dup.Name)." `
                ($paths -join "`n") `
                "Gunakan import-mode=importlib atau rapikan naming bila diperlukan."
        }
    }
    else {
        Add-Finding `
            "Testing" `
            "PASS" `
            "Tidak ditemukan duplicate test filename." `
            "" `
            ""
    }
}
else {
    Add-Finding `
        "Testing" `
        "FAIL" `
        "Directory tests tidak ditemukan." `
        "tests/" `
        "Repository membutuhkan regression suite."
}

# ------------------------------------------------------------
# 12. CONTRACTS
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 12. CONTRACT SYSTEM ===" -ForegroundColor Cyan

$contractCandidates = @(
    "docs\contracts",
    "docs\architecture",
    "docs\audit"
)

foreach ($p in $contractCandidates) {

    if (Test-PathExists $p) {

        $files = @(Get-ChildItem `
            -LiteralPath (Join-Path $Root $p) `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue)

        Add-Finding `
            "Contracts" `
            "PASS" `
            "$p tersedia dengan $($files.Count) file." `
            $p `
            ""
    }
    else {
        Add-Finding `
            "Contracts" `
            "INFO" `
            "$p belum tersedia." `
            $p `
            "Belum otomatis dianggap defect."
    }
}

# ------------------------------------------------------------
# 13. DEVELOPER CONTRACT
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 13. DEVELOPER GOVERNANCE ===" -ForegroundColor Cyan

$developerContractCandidates = @(
    "docs\contracts\DEVELOPER-CONTRACT.md",
    "docs\developer\DEVELOPER-CONTRACT.md"
)

$developerFound = $false

foreach ($p in $developerContractCandidates) {
    if (Test-PathExists $p) {
        $developerFound = $true

        Add-Finding `
            "Developer Governance" `
            "PASS" `
            "Developer Contract ditemukan." `
            $p `
            "Jadikan contract wajib untuk human developer dan AI coding agent."

        break
    }
}

if (-not $developerFound) {
    Add-Finding `
        "Developer Governance" `
        "WARN" `
        "Developer Contract belum ditemukan pada lokasi standar." `
        ($developerContractCandidates -join ", ") `
        "Simpan Developer Contract setelah disetujui."
}

# ------------------------------------------------------------
# 14. GATES
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 14. GATES ===" -ForegroundColor Cyan

$gateCandidates = @(
    "docs\audit\GATES.md",
    "docs\GATES.md"
)

$gateFound = $false

foreach ($p in $gateCandidates) {
    if (Test-PathExists $p) {
        $gateFound = $true

        Add-Finding `
            "Gates" `
            "PASS" `
            "GATES V1 ditemukan." `
            $p `
            "Gunakan sebagai release gate."

        break
    }
}

if (-not $gateFound) {
    Add-Finding `
        "Gates" `
        "WARN" `
        "GATES V1 tidak ditemukan pada lokasi standar." `
        ($gateCandidates -join ", ") `
        "Buat gate sebelum phase berikutnya."
}

# ------------------------------------------------------------
# 15. GIT STATUS
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 15. GIT STATUS ===" -ForegroundColor Cyan

if (Test-Path (Join-Path $Root ".git")) {

    try {
        $gitStatus = @(git status --short 2>$null)

        if ($gitStatus.Count -eq 0) {

            Add-Finding `
                "Git" `
                "PASS" `
                "Working tree bersih." `
                "git status --short kosong." `
                ""
        }
        else {

            Add-Finding `
                "Git" `
                "WARN" `
                "Working tree memiliki perubahan lokal: $($gitStatus.Count)." `
                ($gitStatus -join "`n") `
                "Pastikan perubahan diketahui sebelum audit baseline."
        }
    }
    catch {

        Add-Finding `
            "Git" `
            "WARN" `
            "Git status tidak dapat diperiksa." `
            $_.Exception.Message `
            ""
    }
}

# ------------------------------------------------------------
# 16. PYPROJECT / PYTEST
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 16. PYTEST CONFIGURATION ===" -ForegroundColor Cyan

if (Test-PathExists "pyproject.toml") {

    $pyproject = Read-TextSafe "pyproject.toml"

    if ($pyproject -match "\[tool\.pytest\.ini_options\]") {

        Add-Finding `
            "Pytest" `
            "PASS" `
            "Pytest configuration ditemukan." `
            "[tool.pytest.ini_options]" `
            ""
    }
    else {

        Add-Finding `
            "Pytest" `
            "WARN" `
            "pytest configuration section tidak terdeteksi." `
            "pyproject.toml" `
            "Periksa konfigurasi pytest."
    }

    if ($pyproject -match "import-mode") {

        Add-Finding `
            "Pytest" `
            "INFO" `
            "Import mode tercantum dalam pytest configuration." `
            "import-mode ditemukan." `
            ""
    }
    else {

        Add-Finding `
            "Pytest" `
            "INFO" `
            "Import mode tidak dikunci di pyproject.toml." `
            "Full regression dapat menggunakan --import-mode=importlib." `
            "Jangan mengubah pyproject tanpa kebutuhan."
    }
}
else {

    Add-Finding `
        "Pytest" `
        "WARN" `
        "pyproject.toml tidak ditemukan." `
        "" `
        "Periksa konfigurasi project."
}

# ------------------------------------------------------------
# 17. AUTOMATED TEST RESULT
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 17. LIVE REGRESSION ===" -ForegroundColor Cyan

Write-Host "Menjalankan pytest read-only..." -ForegroundColor Yellow
Write-Host ""

$pytestOutput = @(
    python -m pytest -q --import-mode=importlib 2>&1
)

$pytestExit = $LASTEXITCODE

$pytestText = $pytestOutput -join "`n"

Write-Host $pytestText

if ($pytestExit -eq 0) {

    Add-Finding `
        "Regression" `
        "PASS" `
        "Full pytest regression PASS." `
        $pytestText `
        "Phase dapat dievaluasi terhadap GATES."
}
else {

    Add-Finding `
        "Regression" `
        "WARN" `
        "Full pytest regression belum PASS penuh." `
        $pytestText `
        "Perbaiki/root-cause setiap failure sebelum phase dinyatakan FINAL."
}

# ------------------------------------------------------------
# 18. PHASE 2 TEST
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 18. PHASE 2 HARDENING TEST ===" -ForegroundColor Cyan

$phase2Output = @(
    python -m pytest tests\test_phase2_hardening.py -q 2>&1
)

$phase2Exit = $LASTEXITCODE
$phase2Text = $phase2Output -join "`n"

Write-Host $phase2Text

if ($phase2Exit -eq 0) {

    Add-Finding `
        "Phase 2" `
        "PASS" `
        "Phase 2 hardening test PASS." `
        $phase2Text `
        "Phase 2 dapat dipertahankan sebagai VERIFIED."
}
else {

    Add-Finding `
        "Phase 2" `
        "FAIL" `
        "Phase 2 hardening test gagal." `
        $phase2Text `
        "Jangan lanjutkan phase tanpa root-cause analysis."
}

# ------------------------------------------------------------
# 19. PHASE 3 TEST
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 19. PHASE 3 OBSERVABILITY TEST ===" -ForegroundColor Cyan

$phase3Tests = @(
    "tests\test_phase3_observability.py",
    "tests\test_phase3_http_integration.py",
    "tests\test_phase3_metrics_integration.py"
)

$phase3Output = @()

foreach ($test in $phase3Tests) {

    if (Test-PathExists $test) {

        $result = @(python -m pytest $test -q 2>&1)

        $exit = $LASTEXITCODE

        $phase3Output += "=== $test ==="
        $phase3Output += $result

        if ($exit -ne 0) {
            $phase3Output += "RESULT: FAILED"
        }
        else {
            $phase3Output += "RESULT: PASS"
        }
    }
}

$phase3Text = $phase3Output -join "`n"

Write-Host $phase3Text

if ($phase3Text -and $phase3Text -notmatch "RESULT: FAILED") {

    Add-Finding `
        "Phase 3" `
        "PASS" `
        "Phase 3 observability targeted tests PASS." `
        $phase3Text `
        "Full regression tetap menjadi final gate."
}
else {

    Add-Finding `
        "Phase 3" `
        "WARN" `
        "Phase 3 targeted tests belum seluruhnya PASS." `
        $phase3Text `
        "Investigasi failure."
}

# ------------------------------------------------------------
# 20. FORBIDDEN PATTERN AUDIT
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== 20. FORBIDDEN PATTERN AUDIT ===" -ForegroundColor Cyan

$forbiddenPatterns = @(
    @{ Name = "eval("; Pattern = '\beval\s*\(' },
    @{ Name = "exec("; Pattern = '\bexec\s*\(' },
    @{ Name = "os.system("; Pattern = 'os\.system\s*\(' },
    @{ Name = "subprocess shell=True"; Pattern = "shell\s*=\s*True" },
    @{ Name = "pickle.loads"; Pattern = "pickle\.loads\s*\(" }
)

$forbiddenHits = New-Object System.Collections.Generic.List[string]

foreach ($file in $pyFiles) {

    try {
        $lines = Get-Content -LiteralPath $file.FullName -ErrorAction SilentlyContinue
        $lineNumber = 0

        foreach ($line in $lines) {

            $lineNumber++

            foreach ($rule in $forbiddenPatterns) {

                if ($line -match $rule.Pattern) {

                    $relative = $file.FullName.Substring($Root.Length).TrimStart("\","/")

                    $forbiddenHits.Add(
                        "$relative : line $lineNumber : $($rule.Name)"
                    )
                }
            }
        }
    }
    catch {
    }
}

if ($forbiddenHits.Count -eq 0) {

    Add-Finding `
        "Security Pattern" `
        "PASS" `
        "Tidak ditemukan forbidden execution pattern sederhana." `
        "Recursive Python scan." `
        ""
}
else {

    Add-Finding `
        "Security Pattern" `
        "WARN" `
        "Execution-sensitive pattern ditemukan: $($forbiddenHits.Count)." `
        ($forbiddenHits -join "`n") `
        "Audit manual. Finding tidak otomatis berarti vulnerability."
}

# ------------------------------------------------------------
# 21. FINAL ENGINEERING STATUS
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "             MASTER ENGINEERING STATUS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$overallStatus = "VERIFIED"

if ($Fail -gt 0) {
    $overallStatus = "FAILED"
}
elseif ($Warn -gt 0) {
    $overallStatus = "PARTIALLY VERIFIED"
}

Write-Host ""
Write-Host "PASS : $Pass" -ForegroundColor Green
Write-Host "WARN : $Warn" -ForegroundColor Yellow
Write-Host "FAIL : $Fail" -ForegroundColor Red
Write-Host "INFO : $Info" -ForegroundColor Cyan
Write-Host ""
Write-Host "OVERALL STATUS: $overallStatus" -ForegroundColor Magenta
Write-Host ""

# ------------------------------------------------------------
# 22. REPORT GENERATION
# ------------------------------------------------------------

$report = New-Object System.Collections.Generic.List[string]

$report.Add("# NUSANTARA AI â€” MASTER ENGINEERING AUDIT V1")
$report.Add("")
$report.Add("**Repository:** `$Root`")
$report.Add("")
$report.Add("**Audit Date:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$report.Add("")
$report.Add("**Mode:** READ-ONLY")
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
$report.Add("| Area | Status | Finding |")
$report.Add("|---|---|---|")

foreach ($f in $Findings) {

    $finding = ($f.Finding -replace "\|", "\|")
    $report.Add("| $($f.Area) | $($f.Status) | $finding |")
}

$report.Add("")
$report.Add("## Engineering Interpretation")
$report.Add("")
$report.Add("- `PASS` = evidence ditemukan dan pemeriksaan berhasil.")
$report.Add("- `WARN` = perlu pemeriksaan/interpretasi lebih lanjut.")
$report.Add("- `FAIL` = pemeriksaan menemukan kondisi yang tidak memenuhi baseline.")
$report.Add("- `INFO` = informasi audit, bukan otomatis defect.")
$report.Add("")
$report.Add("## Phase Discipline")
$report.Add("")
$report.Add("Phase tidak boleh dinyatakan FINAL hanya berdasarkan keberadaan source code.")
$report.Add("")
$report.Add("Minimal:")
$report.Add("")
$report.Add("`IMPLEMENTATION + TARGETED TEST + SECURITY + FULL REGRESSION + EVIDENCE`")
$report.Add("")
$report.Add("## Important")
$report.Add("")
$report.Add("Audit ini tidak melakukan perubahan terhadap source code production.")
$report.Add("")
$report.Add("Temuan harus dianalisis terlebih dahulu sebelum dilakukan patch.")
$report.Add("")

$report | Set-Content -LiteralPath $ReportFile -Encoding UTF8

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "AUDIT SELESAI" -ForegroundColor Green
Write-Host ""
Write-Host "Report:" -ForegroundColor Cyan
Write-Host $ReportFile
Write-Host ""
Write-Host "STATUS: $overallStatus" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Cyan
