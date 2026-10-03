$ErrorActionPreference = "Continue"

$Root = (Get-Location).Path
$ScriptDir = Join-Path $Root "scripts"
$OutDir = Join-Path $Root "data\validation"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Invoke-PythonValidator {
    param(
        [string]$Path
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = "`"$Path`""
    $psi.WorkingDirectory = $Root
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi

    [void]$proc.Start()

    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()

    $proc.WaitForExit()

    [PSCustomObject]@{
        exit_code = $proc.ExitCode
        output    = ($stdout + "`n" + $stderr).Trim()
    }
}

function Add-Result {
    param(
        [int]$Gate,
        [string]$Name,
        [string]$Script,
        [bool]$Pass,
        [int]$ExitCode,
        [string]$Details
    )

    $script:Results += [PSCustomObject]@{
        gate       = $Gate
        name       = $Name
        script     = $Script
        status     = if ($Pass) { "PASS" } else { "FAIL" }
        exit_code  = $ExitCode
        details    = (($Details -split "`r?`n" | Select-Object -Last 8) -join "`n")
    }

    $label = if ($Pass) { "PASS" } else { "FAIL" }
    $color = if ($Pass) { "Green" } else { "Red" }

    Write-Host ("Gate {0,-2} {1,-30} : {2}" -f $Gate,$Name,$label) -ForegroundColor $color
}

$Results = @()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA MASTER VALIDATOR - GATE 7-17" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PROJECT : $Root"
Write-Host ""

# ============================================================
# GATE 7
# ============================================================

$gate7 = @(
    @{ Script="test_knowledge_grounding.py"; Name="Knowledge Grounding" },
    @{ Script="test_knowledge_retrieval.py"; Name="Knowledge Retrieval" },
    @{ Script="test_grounding_ollama_api.py"; Name="Ollama API Grounding" },
    @{ Script="test_grounding_hermes.py"; Name="Hermes Grounding" }
)

foreach ($item in $gate7) {
    $path = Join-Path $ScriptDir $item.Script

    if (-not (Test-Path $path)) {
        Add-Result 7 $item.Name $item.Script $false 999 "Validator tidak ditemukan"
        continue
    }

    $r = Invoke-PythonValidator $path

    $hasFail = (
        $r.output -match "\[FAIL\]" -or
        $r.output -match "FAIL\s+:\s*[1-9]" -or
        $r.output -match "RESULT\s*:\s*FAIL"
    )

    $hasPass = (
        $r.output -match "\[PASS\]" -or
        $r.output -match "PASS\s+:\s*[1-9]" -or
        $r.output -match "RESULT\s*:\s*PASS"
    )

    $pass = ($r.exit_code -eq 0) -and (-not $hasFail) -and $hasPass

    Add-Result 7 $item.Name $item.Script $pass $r.exit_code $r.output
}

# ============================================================
# GATE 8-13 FOUNDATION VALIDATION
# ============================================================

$combinedPath = Join-Path $ScriptDir "validate_gates_8_16.py"

if (Test-Path $combinedPath) {

    Write-Host ""
    Write-Host "Menjalankan validator Gate 8-13..." -ForegroundColor Cyan

    $r = Invoke-PythonValidator $combinedPath
    $o = $r.output

    $markers = @{
        8  = "GATE 8  Reasoning           : PASS"
        9  = "GATE 9  Decision / Policy   : PASS"
        10 = "GATE 10 Memory / Context    : PASS"
        11 = "GATE 11 Tool / Action       : PASS"
        13 = "GATE 13 Orchestration       : PASS"
    }

    foreach ($g in @(8,9,10,11,13)) {
        $marker = $markers[$g]
        $pass = ($r.exit_code -eq 0) -and ($o -match [regex]::Escape($marker))

        Add-Result $g "Foundation" "validate_gates_8_16.py" $pass $r.exit_code $o
    }

    # Gate 12 sekarang validator final tersendiri
    $gate12Path = Join-Path $ScriptDir "validate_gate12_final.py"

    if (Test-Path $gate12Path) {
        $g12 = Invoke-PythonValidator $gate12Path
        $pass12 = (
            $g12.exit_code -eq 0 -and
            $g12.output -match "GATE 12 FINAL\s+:\s+PASS" -and
            $g12.output -notmatch "FAIL\s+:\s*[1-9]"
        )

        Add-Result 12 "Existing Tools" "validate_gate12_final.py" $pass12 $g12.exit_code $g12.output
    }
    else {
        Add-Result 12 "Existing Tools" "validate_gate12_final.py" $false 999 "Validator tidak ditemukan"
    }
}
else {
    foreach ($g in @(8,9,10,11,13)) {
        Add-Result $g "Foundation" "validate_gates_8_16.py" $false 999 "Validator tidak ditemukan"
    }

    Add-Result 12 "Existing Tools" "validate_gate12_final.py" $false 999 "Validator tidak ditemukan"
}

# ============================================================
# GATE 14
# ============================================================

$path14 = Join-Path $ScriptDir "validate_gate14_final.py"

if (Test-Path $path14) {
    $r14 = Invoke-PythonValidator $path14

    $pass14 = (
        $r14.exit_code -eq 0 -and
        $r14.output -match "GATE 14 FINAL\s+:\s+PASS" -and
        $r14.output -notmatch "FAIL\s+:\s*[1-9]"
    )

    Add-Result 14 "Developer Core / Graph" "validate_gate14_final.py" $pass14 $r14.exit_code $r14.output
}
else {
    Add-Result 14 "Developer Core / Graph" "validate_gate14_final.py" $false 999 "Validator tidak ditemukan"
}

# ============================================================
# GATE 15
# ============================================================

$path15 = Join-Path $ScriptDir "validate_gate15_final.py"

if (Test-Path $path15) {
    $r15 = Invoke-PythonValidator $path15

    $pass15 = (
        $r15.exit_code -eq 0 -and
        $r15.output -match "GATE 15 FINAL\s+:\s+PASS" -and
        $r15.output -notmatch "FAIL\s+:\s*[1-9]"
    )

    Add-Result 15 "Evaluation / Security" "validate_gate15_final.py" $pass15 $r15.exit_code $r15.output
}
else {
    Add-Result 15 "Evaluation / Security" "validate_gate15_final.py" $false 999 "Validator tidak ditemukan"
}

# ============================================================
# GATE 16
# ============================================================

$path16 = Join-Path $ScriptDir "validate_gate16_final.py"

if (Test-Path $path16) {
    $r16 = Invoke-PythonValidator $path16

    $pass16 = (
        $r16.exit_code -eq 0 -and
        $r16.output -match "GATE 16 FINAL\s+:\s+PASS" -and
        $r16.output -notmatch "FAIL\s+:\s*[1-9]"
    )

    Add-Result 16 "Production Hardening" "validate_gate16_final.py" $pass16 $r16.exit_code $r16.output
}
else {
    Add-Result 16 "Production Hardening" "validate_gate16_final.py" $false 999 "Validator tidak ditemukan"
}

# ============================================================
# GATE 17
# ============================================================

$path17 = Join-Path $ScriptDir "validate_gate17_final.py"

if (Test-Path $path17) {
    $r17 = Invoke-PythonValidator $path17

    $pass17 = (
        $r17.exit_code -eq 0 -and
        $r17.output -match "GATE 17 FINAL\s+:\s+PASS" -and
        $r17.output -notmatch "FAIL\s+:\s*[1-9]"
    )

    Add-Result 17 "Self Improvement" "validate_gate17_final.py" $pass17 $r17.exit_code $r17.output
}
else {
    Add-Result 17 "Self Improvement" "validate_gate17_final.py" $false 999 "Validator tidak ditemukan"
}

# ============================================================
# SUMMARY
# ============================================================

$total = $Results.Count
$passCount = @($Results | Where-Object { $_.status -eq "PASS" }).Count
$failCount = @($Results | Where-Object { $_.status -eq "FAIL" }).Count

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA MASTER VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ("TOTAL CHECKS : {0}" -f $total)
Write-Host ("PASS         : {0}" -f $passCount) -ForegroundColor Green
Write-Host ("FAIL         : {0}" -f $failCount) -ForegroundColor $(if ($failCount -eq 0) {"Green"} else {"Red"})

$report = [ordered]@{
    summary = [ordered]@{
        pass  = $passCount
        fail  = $failCount
        total = $total
        warn  = 0
    }
    timestamp = (Get-Date).ToString("o")
    project = $Root
    gates = [ordered]@{}
    results = $Results
    safety = [ordered]@{
        production_write = $false
        broad_write = $false
        shell_execution_enabled = $false
        execution_enabled = $false
        approval_required = $true
        evaluation_deterministic = $true
    }
}

foreach ($g in ($Results | Select-Object -ExpandProperty gate -Unique | Sort-Object)) {
    $items = @($Results | Where-Object { $_.gate -eq $g })
    $report.gates["Gate $g"] = [ordered]@{
        status = if (@($items | Where-Object status -eq "FAIL").Count -eq 0) { "PASS" } else { "FAIL" }
        checks = $items.Count
        pass = @($items | Where-Object status -eq "PASS").Count
        fail = @($items | Where-Object status -eq "FAIL").Count
    }
}

$reportPath = Join-Path $OutDir "nusantara_validation_report.json"

$report | ConvertTo-Json -Depth 10 | Set-Content $reportPath -Encoding UTF8

Write-Host ""
Write-Host "REPORT : $reportPath" -ForegroundColor Cyan

if ($failCount -eq 0 -and $total -eq 14) {
    Write-Host ""
    Write-Host "NUSANTARA MASTER : PASS" -ForegroundColor Green
    exit 0
}
else {
    Write-Host ""
    Write-Host "NUSANTARA MASTER : FAIL" -ForegroundColor Red
    exit 1
}

