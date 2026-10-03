# ============================================================
# NUSANTARA AI - PHASE 1 MASTER GATE CONTROLLER
# ============================================================
# Tujuan:
#   Phase 1 -> Architecture Contract -> GATES V1
#   -> Lock Phase 0-3 -> Approval -> Phase 4 Trust
#
# Prinsip:
#   - READ ONLY terhadap production code
#   - Tidak install package
#   - Tidak mengubah database
#   - Tidak menjalankan Phase 4
#   - Tidak menghapus file
#   - Tidak membuat engine kedua
#   - Tidak melewati gate
# ============================================================

$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$ReportDir = Join-Path $Root "audit_reports"
$Report = Join-Path $ReportDir "NUSANTARA-PHASE1-GATE.md"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$Results = @()

function Add-Result {
    param(
        [string]$ID,
        [string]$Status,
        [string]$Item,
        [string]$Evidence,
        [string]$Action = ""
    )

    $script:Results += [PSCustomObject]@{
        ID       = $ID
        Status   = $Status
        Item     = $Item
        Evidence = $Evidence
        Action   = $Action
    }

    Write-Host ("[{0}] {1} - {2}" -f $Status, $ID, $Item)
}

function Exists {
    param([string]$Path)
    return Test-Path (Join-Path $Root $Path)
}

function Read-Text {
    param([string]$Path)

    $Full = Join-Path $Root $Path

    if (-not (Test-Path $Full)) {
        return ""
    }

    return Get-Content $Full -Raw -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "============================================================"
Write-Host " NUSANTARA AI - PHASE 1 MASTER GATE CONTROLLER"
Write-Host "============================================================"
Write-Host "ROOT : $Root"
Write-Host ""

# ------------------------------------------------------------
# GATE 0 - REPOSITORY BASELINE
# ------------------------------------------------------------

if (Exists "app") {
    Add-Result "P1-001" "PASS" `
        "Application directory tersedia" `
        "app\"
} else {
    Add-Result "P1-001" "FAIL" `
        "Application directory tersedia" `
        "app\ tidak ditemukan" `
        "Hentikan proses"
}

if (Exists "tests") {
    Add-Result "P1-002" "PASS" `
        "Test suite tersedia" `
        "tests\"
} else {
    Add-Result "P1-002" "FAIL" `
        "Test suite tersedia" `
        "tests\ tidak ditemukan"
}

if (Exists "pyproject.toml") {
    Add-Result "P1-003" "PASS" `
        "Project configuration tersedia" `
        "pyproject.toml"
} else {
    Add-Result "P1-003" "WARN" `
        "Project configuration" `
        "pyproject.toml tidak ditemukan"
}

# ------------------------------------------------------------
# GATE 1 - ARCHITECTURE SOURCES
# ------------------------------------------------------------

$ArchitectureCurrent = Read-Text "ARCHITECTURE_CURRENT.md"
$ArchitectureBaseline = Read-Text "docs\architecture.md"
$ArchitectureTarget = Read-Text "docs\architecture\TARGET_ARCHITECTURE.md"
$ADR = Read-Text "docs\architecture-decisions.md"

if ($ArchitectureCurrent) {
    Add-Result "P1-010" "PASS" `
        "Current architecture ditemukan" `
        "ARCHITECTURE_CURRENT.md"
} else {
    Add-Result "P1-010" "FAIL" `
        "Current architecture" `
        "ARCHITECTURE_CURRENT.md tidak ditemukan"
}

if ($ArchitectureBaseline) {
    Add-Result "P1-011" "PASS" `
        "Phase 0 architecture baseline ditemukan" `
        "docs\architecture.md"
} else {
    Add-Result "P1-011" "WARN" `
        "Phase 0 architecture baseline" `
        "docs\architecture.md tidak ditemukan"
}

if ($ArchitectureTarget) {
    Add-Result "P1-012" "PASS" `
        "Target V2 architecture ditemukan" `
        "docs\architecture\TARGET_ARCHITECTURE.md"
} else {
    Add-Result "P1-012" "WARN" `
        "Target V2 architecture" `
        "TARGET_ARCHITECTURE.md tidak ditemukan"
}

if ($ADR) {
    Add-Result "P1-013" "PASS" `
        "Architecture Decision Records ditemukan" `
        "docs\architecture-decisions.md"
} else {
    Add-Result "P1-013" "WARN" `
        "Architecture Decision Records" `
        "ADR tidak ditemukan"
}

# ------------------------------------------------------------
# GATE 2 - V1 / V2 BOUNDARY
# ------------------------------------------------------------

if ($ArchitectureTarget -match "V2\s*=\s*V1\s*\+\s*lapisan baru") {
    Add-Result "P1-020" "PASS" `
        "V2 mempertahankan Core V1" `
        "Target architecture menyatakan V2 = V1 + lapisan baru"
} else {
    Add-Result "P1-020" "WARN" `
        "V1/V2 boundary" `
        "Pernyataan V2 = V1 + lapisan baru tidak ditemukan"
}

if ($ArchitectureTarget -match "/v1.*tidak berubah") {
    Add-Result "P1-021" "PASS" `
        "API V1 preservation principle" `
        "/v1 tidak berubah"
} else {
    Add-Result "P1-021" "WARN" `
        "API V1 preservation principle" `
        "Belum terdeteksi"
}

if ($ArchitectureTarget -match "tanpa engine duplikat") {
    Add-Result "P1-022" "PASS" `
        "No duplicate engine principle" `
        "Target architecture melarang engine duplikat"
} else {
    Add-Result "P1-022" "WARN" `
        "No duplicate engine principle" `
        "Belum terdeteksi"
}

# ------------------------------------------------------------
# GATE 3 - CURRENT DOCUMENT CONSISTENCY
# ------------------------------------------------------------

if ($ArchitectureCurrent -match "Observability.*MISSING") {
    Add-Result "P1-030" "WARN" `
        "ARCHITECTURE_CURRENT sinkron dengan implementasi" `
        "Dokumen masih menyatakan Observability = MISSING" `
        "Perlu diperbarui berdasarkan evidence Phase 3"
} else {
    Add-Result "P1-030" "PASS" `
        "ARCHITECTURE_CURRENT sinkron" `
        "Tidak ditemukan status Observability = MISSING"
}

if ($ArchitectureCurrent -match "Security.*PARTIAL") {
    Add-Result "P1-031" "WARN" `
        "Security status perlu rekonsiliasi" `
        "Dokumen masih menyatakan Security PARTIAL" `
        "Bandingkan dengan hasil security audit"
} else {
    Add-Result "P1-031" "PASS" `
        "Security status" `
        "Tidak ada konflik langsung"
}

# ------------------------------------------------------------
# GATE 4 - PHASE 2 EVIDENCE
# ------------------------------------------------------------

$Phase2Test = Join-Path $Root "tests\test_phase2_hardening.py"

if (Test-Path $Phase2Test) {
    Add-Result "P1-040" "PASS" `
        "Phase 2 test suite tersedia" `
        "tests\test_phase2_hardening.py"
} else {
    Add-Result "P1-040" "FAIL" `
        "Phase 2 test suite" `
        "Test Phase 2 tidak ditemukan"
}

# ------------------------------------------------------------
# GATE 5 - PHASE 3 EVIDENCE
# ------------------------------------------------------------

$Phase3Tests = @(
    "tests\test_phase3_observability.py",
    "tests\test_phase3_http_integration.py",
    "tests\test_phase3_metrics_integration.py"
)

$MissingPhase3 = @()

foreach ($T in $Phase3Tests) {
    if (-not (Exists $T)) {
        $MissingPhase3 += $T
    }
}

if ($MissingPhase3.Count -eq 0) {
    Add-Result "P1-050" "PASS" `
        "Phase 3 test suite tersedia" `
        "3 test suite observability ditemukan"
} else {
    Add-Result "P1-050" "FAIL" `
        "Phase 3 test suite" `
        ($MissingPhase3 -join ", ")
}

# ------------------------------------------------------------
# GATE 6 - ARCHITECTURE CONTRACT
# ------------------------------------------------------------

$ContractCandidates = @(
    "NUSANTARA-ARCHITECTURE-CONTRACT-V1.md",
    "docs\architecture\NUSANTARA-ARCHITECTURE-CONTRACT-V1.md",
    "docs\contracts\NUSANTARA-ARCHITECTURE-CONTRACT-V1.md"
)

$ContractFound = $null

foreach ($Candidate in $ContractCandidates) {
    if (Exists $Candidate) {
        $ContractFound = $Candidate
        break
    }
}

if ($ContractFound) {
    Add-Result "P1-060" "PASS" `
        "Architecture Contract ditemukan" `
        $ContractFound
} else {
    Add-Result "P1-060" "BLOCKED" `
        "Architecture Contract" `
        "Belum ada dokumen contract tunggal" `
        "Buat/ratifikasi Architecture Contract terlebih dahulu"
}

# ------------------------------------------------------------
# GATE 7 - GATES V1
# ------------------------------------------------------------

$GateCandidates = @(
    "docs\audit\GATES.md",
    "NUSANTARA-GATES-V1.md",
    "docs\GATES.md"
)

$GateFound = $null

foreach ($Candidate in $GateCandidates) {
    if (Exists $Candidate) {
        $GateFound = $Candidate
        break
    }
}

if ($GateFound) {
    Add-Result "P1-070" "PASS" `
        "GATES V1 ditemukan" `
        $GateFound
} else {
    Add-Result "P1-070" "BLOCKED" `
        "GATES V1" `
        "Dokumen GATES belum ditemukan pada lokasi kandidat" `
        "Ratifikasi GATES V1"
}

# ------------------------------------------------------------
# GATE 8 - REGRESSION EVIDENCE
# ------------------------------------------------------------

Write-Host ""
Write-Host "Menjalankan full regression..."
Write-Host ""

$PytestOutput = & python -m pytest -q --import-mode=importlib 2>&1
$PytestExit = $LASTEXITCODE

$PytestText = ($PytestOutput | Out-String).Trim()

if ($PytestExit -eq 0) {
    Add-Result "P1-080" "PASS" `
        "Full regression" `
        $PytestText
} else {
    Add-Result "P1-080" "FAIL" `
        "Full regression" `
        $PytestText `
        "Jangan lanjut ke Phase 4"
}

# ------------------------------------------------------------
# GATE 9 - PHASE LOCK DECISION
# ------------------------------------------------------------

$Blocking = @(
    $Results | Where-Object {
        $_.Status -in @("FAIL", "BLOCKED")
    }
)

if ($Blocking.Count -eq 0) {

    Add-Result "P1-090" "READY" `
        "Phase 0-3 Lock" `
        "Tidak ada FAIL/BLOCKED"

} else {

    Add-Result "P1-090" "BLOCKED" `
        "Phase 0-3 Lock" `
        "$($Blocking.Count) item masih FAIL/BLOCKED" `
        "Selesaikan seluruh blocking item"
}

# ------------------------------------------------------------
# GATE 10 - PHASE 4
# ------------------------------------------------------------

if ($Blocking.Count -eq 0 -and $ContractFound -and $GateFound -and $PytestExit -eq 0) {

    Add-Result "P1-100" "READY" `
        "Phase 4 Trust" `
        "Semua prerequisite terdeteksi"

} else {

    Add-Result "P1-100" "LOCKED" `
        "Phase 4 Trust" `
        "Phase 4 belum boleh dimulai"
        "Jangan coding Phase 4"
}

# ------------------------------------------------------------
# REPORT
# ------------------------------------------------------------

$Lines = @()

$Lines += "# NUSANTARA AI - PHASE 1 GATE REPORT"
$Lines += ""
$Lines += "**Generated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$Lines += ""
$Lines += "## Prinsip"
$Lines += ""
$Lines += "- Read-only audit controller"
$Lines += "- Tidak mengubah production code"
$Lines += "- Tidak install dependency"
$Lines += "- Tidak mengubah database"
$Lines += "- Tidak menjalankan Phase 4"
$Lines += "- Phase berikutnya hanya dibuka setelah gate lulus"
$Lines += ""
$Lines += "## Results"
$Lines += ""
$Lines += "| ID | Status | Item | Evidence |"
$Lines += "|---|---|---|---|"

foreach ($R in $Results) {

    $Evidence = ($R.Evidence -replace "`r?`n", " ") -replace "\|", "\|"
    $Item = ($R.Item -replace "\|", "\|")

    $Lines += "| $($R.ID) | $($R.Status) | $Item | $Evidence |"
}

$Lines += ""
$Lines += "## Decision"
$Lines += ""

if ($Blocking.Count -eq 0 -and $ContractFound -and $GateFound -and $PytestExit -eq 0) {

    $Lines += "**READY FOR HUMAN APPROVAL**"
    $Lines += ""
    $Lines += "Phase 4 Trust masih membutuhkan approval manusia."
    $Lines += "Script ini tidak menjalankan Phase 4."

} else {

    $Lines += "**PHASE 4 LOCKED**"
    $Lines += ""
    $Lines += "Masih terdapat prerequisite yang belum terpenuhi."
}

Set-Content -Path $Report -Value ($Lines -join "`r`n") -Encoding UTF8

Write-Host ""
Write-Host "============================================================"
Write-Host " RESULT"
Write-Host "============================================================"

if ($Blocking.Count -eq 0 -and $ContractFound -and $GateFound -and $PytestExit -eq 0) {

    Write-Host "STATUS : READY FOR HUMAN APPROVAL"
    Write-Host "PHASE 4: LOCKED UNTIL APPROVAL"

} else {

    Write-Host "STATUS : BLOCKED"
    Write-Host "PHASE 4: LOCKED"
}

Write-Host ""
Write-Host "REPORT : $Report"
Write-Host ""
Write-Host "============================================================"
