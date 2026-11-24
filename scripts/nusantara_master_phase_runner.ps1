param(
    [int]$StartPhase = 0,
    [int]$EndPhase = 21,
    [switch]$AuditOnly,
    [switch]$RunTests,
    [switch]$ContinueOnFailure
)

$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$ReportDir = Join-Path $Root "reports\nusantara-phases"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ReportFile = Join-Path $ReportDir "phase-run-$Timestamp.md"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$Phases = @(
    @{ Id=0;  Name="Discovery";             Path="docs";  Pattern="*discovery*"; },
    @{ Id=1;  Name="Architecture Map";     Path="docs";  Pattern="*architecture*"; },
    @{ Id=2;  Name="Core Hardening";       Path="tests"; Pattern="*phase2*"; },
    @{ Id=3;  Name="Observability";        Path="tests"; Pattern="*phase3*"; },
    @{ Id=4;  Name="Trust";                Path="tests"; Pattern="*trust*"; },
    @{ Id=5;  Name="Policy";               Path="tests"; Pattern="*policy*"; },
    @{ Id=6;  Name="Memory";               Path="tests"; Pattern="*memory*"; },
    @{ Id=7;  Name="RAG";                  Path="tests"; Pattern="*rag*"; },
    @{ Id=8;  Name="MCP";                  Path="tests"; Pattern="*mcp*"; },
    @{ Id=9;  Name="Tool Governance";      Path="tests"; Pattern="*tool*"; },
    @{ Id=10; Name="Experience";           Path="tests"; Pattern="*experience*"; },
    @{ Id=11; Name="Feedback";             Path="tests"; Pattern="*feedback*"; },
    @{ Id=12; Name="Evaluation";           Path="tests"; Pattern="*evaluation*"; },
    @{ Id=13; Name="Failure Analysis";     Path="tests"; Pattern="*failure*"; },
    @{ Id=14; Name="Gap Detection";        Path="tests"; Pattern="*gap*"; },
    @{ Id=15; Name="Knowledge Discovery";  Path="tests"; Pattern="*knowledge*"; },
    @{ Id=16; Name="Experiment";           Path="tests"; Pattern="*experiment*"; },
    @{ Id=17; Name="Improvement Proposal"; Path="tests"; Pattern="*developer*"; },
    @{ Id=18; Name="Human Approval";       Path="tests"; Pattern="*approval*"; },
    @{ Id=19; Name="V1.x Development";     Path="tests"; Pattern="*v1*"; },
    @{ Id=20; Name="Regression/Security";  Path="tests"; Pattern="*security*"; },
    @{ Id=21; Name="Release/Rollback";     Path="tests"; Pattern="*release*"; }
)

$Results = @()

function Find-PhaseTests {
    param(
        [string]$Path,
        [string]$Pattern
    )

    $FullPath = Join-Path $Root $Path

    if (-not (Test-Path $FullPath)) {
        return @()
    }

    return @(Get-ChildItem `
        -Path $FullPath `
        -Recurse `
        -File `
        -Filter $Pattern `
        -ErrorAction SilentlyContinue)
}

function Run-PhaseTests {
    param(
        [array]$TestFiles
    )

    if ($TestFiles.Count -eq 0) {
        return "NO_TEST"
    }

    $Arguments = @("-m", "pytest")

    foreach ($File in $TestFiles) {
        $Relative = $File.FullName.Substring($Root.Length).TrimStart("\")
        $Arguments += $Relative
    }

    & python @Arguments

    if ($LASTEXITCODE -eq 0) {
        return "PASS"
    }

    return "FAIL"
}

Write-Host ""
Write-Host "============================================================"
Write-Host "          NUSANTARA MASTER PHASE RUNNER"
Write-Host "============================================================"
Write-Host "Repository : $Root"
Write-Host "Range      : Phase $StartPhase -> Phase $EndPhase"
Write-Host "Audit Only : $AuditOnly"
Write-Host "Run Tests  : $RunTests"
Write-Host "============================================================"
Write-Host ""

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

"# NUSANTARA MASTER PHASE AUDIT" | Set-Content $ReportFile
"" | Add-Content $ReportFile
"- Timestamp: $(Get-Date)" | Add-Content $ReportFile
"- Repository: $Root" | Add-Content $ReportFile
"" | Add-Content $ReportFile

foreach ($Phase in $Phases) {

    if ($Phase.Id -lt $StartPhase) {
        continue
    }

    if ($Phase.Id -gt $EndPhase) {
        break
    }

    Write-Host ""
    Write-Host "------------------------------------------------------------"
    Write-Host "PHASE $($Phase.Id) - $($Phase.Name)"
    Write-Host "------------------------------------------------------------"

    $TestFiles = @(Find-PhaseTests `
        -Path $Phase.Path `
        -Pattern $Phase.Pattern)

    Write-Host "Tests ditemukan: $($TestFiles.Count)"

    foreach ($TestFile in $TestFiles) {
        $Relative = $TestFile.FullName.Substring($Root.Length).TrimStart("\")
        Write-Host "  - $Relative"
    }

    if ($AuditOnly) {

        if ($TestFiles.Count -gt 0) {
            $Status = "READY_FOR_TEST"
        }
        else {
            $Status = "NOT_VERIFIED"
        }

    }
    elseif ($RunTests) {

        $Status = Run-PhaseTests -TestFiles $TestFiles

    }
    else {

        $Status = "DISCOVERED"

    }

    $Results += [PSCustomObject]@{
        Phase = $Phase.Id
        Name = $Phase.Name
        Tests = $TestFiles.Count
        Status = $Status
    }

    Write-Host "STATUS: $Status"

    Add-Content $ReportFile "## Phase $($Phase.Id) - $($Phase.Name)"
    Add-Content $ReportFile ""
    Add-Content $ReportFile "- Tests found: $($TestFiles.Count)"
    Add-Content $ReportFile "- Status: **$Status**"
    Add-Content $ReportFile ""

    if (($Status -eq "FAIL") -and (-not $ContinueOnFailure)) {

        Write-Host ""
        Write-Host "============================================================"
        Write-Host "STOP - PHASE $($Phase.Id) GAGAL"
        Write-Host "============================================================"

        Add-Content $ReportFile "## EXECUTION STOPPED"
        Add-Content $ReportFile ""
        Add-Content $ReportFile "Phase $($Phase.Id) gagal. Phase berikutnya tidak dijalankan."

        break
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "                    FINAL SUMMARY"
Write-Host "============================================================"

$Results | Format-Table -AutoSize

$Pass = @($Results | Where-Object {$_.Status -eq "PASS"}).Count
$Fail = @($Results | Where-Object {$_.Status -eq "FAIL"}).Count
$Unverified = @($Results | Where-Object {
    $_.Status -in @(
        "NO_TEST",
        "NOT_VERIFIED",
        "READY_FOR_TEST",
        "DISCOVERED"
    )
}).Count

Write-Host ""
Write-Host "PASS       : $Pass"
Write-Host "FAIL       : $Fail"
Write-Host "UNVERIFIED : $Unverified"
Write-Host ""
Write-Host "REPORT:"
Write-Host $ReportFile

Add-Content $ReportFile ""
Add-Content $ReportFile "# SUMMARY"
Add-Content $ReportFile ""
Add-Content $ReportFile "| Phase | Area | Tests | Status |"
Add-Content $ReportFile "|---:|---|---:|---|"

foreach ($Result in $Results) {
    Add-Content $ReportFile "| $($Result.Phase) | $($Result.Name) | $($Result.Tests) | $($Result.Status) |"
}

Add-Content $ReportFile ""
Add-Content $ReportFile "- PASS: $Pass"
Add-Content $ReportFile "- FAIL: $Fail"
Add-Content $ReportFile "- UNVERIFIED: $Unverified"
