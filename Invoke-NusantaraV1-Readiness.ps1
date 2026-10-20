#requires -Version 5.1
<#
.SYNOPSIS
  Safe, evidence-producing audit for Nusantara V1: Grounding/RAG, runtime, memory/governance.
.DESCRIPTION
  Read-only source inspection by default. Does not edit source, reset Git, clean files,
  migrate databases, call external services, or modify production data.
  Optional tests run only when -RunTests is supplied.
.EXAMPLE
  Set-ExecutionPolicy -Scope Process Bypass
  .\Invoke-NusantaraV1-Readiness.ps1
.EXAMPLE
  .\Invoke-NusantaraV1-Readiness.ps1 -Root "C:\Users\dmaza\mcp-starter" -RunTests
#>
[CmdletBinding()]
param(
    [string]$Root = "C:\Users\dmaza\mcp-starter",
    [switch]$RunTests,
    [switch]$IncludeBroadSearch,
    [int]$MaxFilesPerSearch = 250
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Started = Get-Date
$RunId = $Started.ToString("yyyyMMdd-HHmmss")
$ReportDir = Join-Path $Root ("artifacts\readiness\v1-" + $RunId)
$null = New-Item -ItemType Directory -Path $ReportDir -Force

$script:Findings = [System.Collections.Generic.List[object]]::new()
$script:Commands = [System.Collections.Generic.List[object]]::new()

function Add-Finding {
    param([string]$Area,[string]$Severity,[string]$Status,[string]$Title,[string]$Evidence,[string]$NextAction)
    $script:Findings.Add([pscustomobject]@{
        area=$Area; severity=$Severity; status=$Status; title=$Title
        evidence=$Evidence; next_action=$NextAction
    })
}
function Invoke-Captured {
    param([string]$Name,[string]$Exe,[string[]]$Args,[string]$WorkingDirectory)
    $output = @()
    $exitCode = -999
    try {
        $output = & $Exe @Args 2>&1 | ForEach-Object { "$_" }
        $exitCode = $LASTEXITCODE
    } catch {
        $output = @("ERROR: $($_.Exception.Message)")
    }
    $entry = [pscustomobject]@{
        name=$Name; executable=$Exe; arguments=($Args -join " ")
        working_directory=$WorkingDirectory; exit_code=$exitCode
        output=@($output)
    }
    $script:Commands.Add($entry)
    $safeName = ($Name -replace '[^A-Za-z0-9._-]','_')
    @($output) | Set-Content -LiteralPath (Join-Path $ReportDir "$safeName.txt") -Encoding UTF8
    return $entry
}
function Get-RelativePath([string]$FullPath) {
    try { return [IO.Path]::GetRelativePath($Root,$FullPath) } catch { return $FullPath }
}
function Find-SourceMatches {
    param([string]$Label,[string[]]$Roots,[string[]]$Patterns,[string[]]$Extensions)
    $files = [System.Collections.Generic.List[string]]::new()
    foreach ($relative in $Roots) {
        $base = Join-Path $Root $relative
        if (-not (Test-Path -LiteralPath $base)) { continue }
        if ((Get-Item -LiteralPath $base).PSIsContainer) {
            Get-ChildItem -LiteralPath $base -Recurse -File -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.Extension -in $Extensions -and
                    $_.FullName -notmatch '[\\/](\.git|\.venv|venv|node_modules|__pycache__|dist|build|\.next)[\\/]'
                } | ForEach-Object { $files.Add($_.FullName) }
        } else { $files.Add($base) }
    }
    $files = @($files | Select-Object -Unique | Select-Object -First $MaxFilesPerSearch)
    $matches = [System.Collections.Generic.List[object]]::new()
    foreach ($file in $files) {
        try {
            Select-String -LiteralPath $file -Pattern $Patterns -SimpleMatch -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $matches.Add([pscustomobject]@{
                        file=(Get-RelativePath $_.Path); line=$_.LineNumber
                        pattern=$_.Pattern; text=$_.Line.Trim()
                    })
                }
        } catch {}
    }
    $matches | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ReportDir "$Label-matches.json") -Encoding UTF8
    return @($matches)
}

if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "Repository tidak ditemukan: $Root. Berikan -Root dengan path repository yang benar."
}
Set-Location -LiteralPath $Root

# Environment and repository identity
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    $null = Invoke-Captured "git-status" "git" @("status","--short","--branch") $Root
    $null = Invoke-Captured "git-head" "git" @("rev-parse","HEAD") $Root
    $null = Invoke-Captured "git-diff-stat" "git" @("diff","--stat") $Root
    $null = Invoke-Captured "git-diff-cached-stat" "git" @("diff","--cached","--stat") $Root
} else {
    Add-Finding "Repository" "MEDIUM" "NOT_VERIFIED" "Git tidak ditemukan" "Perintah git tidak tersedia di PATH." "Pasang/aktifkan Git sebelum memakai bukti status repository."
}
Add-Finding "Safety" "INFO" "READ_ONLY" "Mode audit aman" "Script hanya membaca source dan menulis laporan di artifacts/readiness; tidak mengubah source atau database." "Tinjau laporan sebelum developer mengubah kode."

# File inventory (bounded)
$inventoryRoots = @("app","tests","docs","scripts","data")
$inventory = foreach ($rel in $inventoryRoots) {
    $path = Join-Path $Root $rel
    if (Test-Path -LiteralPath $path) {
        $items = Get-ChildItem -LiteralPath $path -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '[\\/](\.git|\.venv|venv|node_modules|__pycache__|dist|build)[\\/]' }
        [pscustomobject]@{root=$rel; file_count=@($items).Count}
    } else { [pscustomobject]@{root=$rel; file_count=0} }
}
$inventory | ConvertTo-Json | Set-Content (Join-Path $ReportDir "inventory.json") -Encoding UTF8

# Key file existence
$keyFiles = @(
 "app\knowledge\grounding.py",
 "app\api\routes.py",
 "app\main.py",
 "tests"
)
foreach ($item in $keyFiles) {
    $exists = Test-Path -LiteralPath (Join-Path $Root $item)
    Add-Finding "Repository" $(if($exists){"INFO"}else{"HIGH"}) $(if($exists){"FOUND"}else{"MISSING"}) "Pemeriksaan path: $item" $(if($exists){"Path tersedia."}else{"Path tidak ditemukan."}) "Konfirmasi lokasi aktual bila struktur repository berbeda."
}

# Grounding/RAG search
$groundingPatterns = @(
 "EvidenceGroundingGuard","def validate(","unsupported_sentences","requirement_evidence_missing",
 "possible_unsupported_content","build_grounded_context","search_knowledge","rerank",
 "filter","grounding","evidence","retriev","oracle","PROJECT_FIXTURE","REVIEW_REQUIRED","MISSING"
)
$grounding = Find-SourceMatches "grounding-rag" @("app\knowledge","app\api","tests","docs") $groundingPatterns @(".py",".md",".json",".yaml",".yml",".toml")
Add-Finding "Grounding/RAG" "INFO" "SCANNED" "Pola Grounding/RAG dikumpulkan" "$($grounding.Count) kecocokan tersimpan di grounding-rag-matches.json." "Baca konteks fungsi validate dan pemanggilnya; kecocokan teks bukan bukti fungsi berjalan saat runtime."

$groundingFile = Join-Path $Root "app\knowledge\grounding.py"
if (Test-Path $groundingFile) {
    $gText = Get-Content -LiteralPath $groundingFile -Raw
    foreach ($pattern in @("EvidenceGroundingGuard","def validate(","build_grounded_context","requirement_evidence_missing","possible_unsupported_content")) {
        $present = $gText.Contains($pattern)
        Add-Finding "Grounding/RAG" "INFO" $(if($present){"PRESENT"}else{"NOT_FOUND"}) "grounding.py: $pattern" $(if($present){"String/fungsi ditemukan."}else{"String/fungsi tidak ditemukan; periksa apakah nama berubah."}) "Periksa implementasi lengkap, tipe evidence, pemanggil, dan tes."
    }
}

# Runtime V1 / Hermes / provider / fallback
$runtimePatterns = @(
 '"/v1/chat"','/v1/chat','HermesAgent','ModelRouter','provider.generate',
 'gate_pipeline','fallback','ollama','LanguageEngine','ProblemEngine',
 'KnowledgeEngine','request_id','trust','response_model'
)
$runtime = Find-SourceMatches "runtime-v1" @("app\api","app\main.py","app\core","app\engine","tests") $runtimePatterns @(".py",".md",".json")
Add-Finding "Runtime V1" "INFO" "SCANNED" "Pola jalur runtime dikumpulkan" "$($runtime.Count) kecocokan tersimpan di runtime-v1-matches.json." "Telusuri handler aktual dari route ke provider dan fallback; jangan menyimpulkan integrasi hanya dari import atau konstruksi objek."

# Memory and governance
$governancePatterns = @(
 "memory","Memory","approval","Approval","policy","Policy","trust","Trust",
 "audit","redact","secret","sensitive","gate_pipeline","developer_snapshot",
 "persist","sqlite","transaction","retention","consent","permission"
)
$gov = Find-SourceMatches "memory-governance" @("app","tests","docs") $governancePatterns @(".py",".md",".json",".yaml",".yml",".toml")
Add-Finding "Memori/Tata Kelola" "INFO" "SCANNED" "Pola memori dan tata kelola dikumpulkan" "$($gov.Count) kecocokan tersimpan di memory-governance-matches.json." "Periksa lifecycle data, kontrol akses, approval, redaksi log, dan kontrak publik berdasarkan jalur eksekusi aktual."

# Existing test inventory
$testFiles = @()
$testsPath = Join-Path $Root "tests"
if (Test-Path $testsPath) {
    $testFiles = @(Get-ChildItem $testsPath -Recurse -File -Filter "test_*.py" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '[\\/](\.venv|venv|__pycache__)[\\/]' })
}
Add-Finding "Tests" "INFO" "INVENTORIED" "File tes Python ditemukan" "$($testFiles.Count) file bernama test_*.py di tests." "Pilih tes terarah dari file yang menyentuh grounding, knowledge, route, memory, approval, dan trust."

# Optional focused tests; no tests are guessed to exist.
if ($RunTests) {
    $pytestCmd = Get-Command pytest -ErrorAction SilentlyContinue
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    $targets = @()
    $candidatePatterns = @(
        "grounding","knowledge","rag","chat","route","memory","approval","trust","policy","contract"
    )
    foreach ($tf in $testFiles) {
        $name = $tf.FullName.ToLowerInvariant()
        if ($candidatePatterns | Where-Object { $name.Contains($_) }) { $targets += $tf.FullName }
    }
    $targets = @($targets | Select-Object -Unique)
    if ($targets.Count -eq 0) {
        Add-Finding "Tests" "MEDIUM" "NOT_RUN" "Tidak ada file tes terarah terdeteksi otomatis" "Nama file tests tidak cocok dengan kata kunci yang dipakai script." "Pilih tes yang benar berdasarkan isi repository; jangan jalankan seluruh suite secara otomatis."
    } elseif ($pytestCmd) {
        $relTargets = @($targets | ForEach-Object { Get-RelativePath $_ })
        $null = Invoke-Captured "pytest-focused" "pytest" (@("-q","--tb=short") + $relTargets) $Root
        $last = $script:Commands | Where-Object name -eq "pytest-focused" | Select-Object -Last 1
        Add-Finding "Tests" $(if($last.exit_code -eq 0){"INFO"}else{"HIGH"}) $(if($last.exit_code -eq 0){"PASSED"}else{"FAILED"}) "Tes pytest terarah" "Exit code: $($last.exit_code). Output lengkap ada di pytest-focused.txt." "Analisis setiap kegagalan; jangan mengubah tes untuk sekadar membuatnya hijau."
    } elseif ($pyCmd) {
        $relTargets = @($targets | ForEach-Object { Get-RelativePath $_ })
        $null = Invoke-Captured "pytest-focused" "python" (@("-m","pytest","-q","--tb=short") + $relTargets) $Root
        $last = $script:Commands | Where-Object name -eq "pytest-focused" | Select-Object -Last 1
        Add-Finding "Tests" $(if($last.exit_code -eq 0){"INFO"}else{"HIGH"}) $(if($last.exit_code -eq 0){"PASSED"}else{"FAILED"}) "Tes pytest terarah" "Exit code: $($last.exit_code). Output lengkap ada di pytest-focused.txt." "Analisis setiap kegagalan; jangan mengubah tes untuk sekadar membuatnya hijau."
    } else {
        Add-Finding "Tests" "HIGH" "NOT_RUN" "Python/pytest tidak ditemukan" "Tidak ada executable pytest atau python di PATH." "Aktifkan virtual environment proyek lalu jalankan ulang dengan -RunTests."
    }
} else {
    Add-Finding "Tests" "INFO" "NOT_RUN_BY_DESIGN" "Tes tidak dijalankan" "Gunakan switch -RunTests untuk menjalankan hanya file tes terarah yang ditemukan." "Review daftar file tes terlebih dahulu bila ingin kontrol penuh."
}

if ($IncludeBroadSearch) {
    $broadPatterns = @("TODO","FIXME","NotImplementedError","pass #","REVIEW_REQUIRED","NOT_IMPLEMENTED","MISSING")
    $broad = Find-SourceMatches "broad-followup" @("app","tests","docs") $broadPatterns @(".py",".md",".json",".yaml",".yml",".toml")
    Add-Finding "Follow-up" "INFO" "SCANNED" "Pencarian blocker luas dijalankan" "$($broad.Count) kecocokan; lihat broad-followup-matches.json." "Triage hasil secara manual; TODO atau MISSING tidak otomatis blocker."
}

# Machine-readable report
$Report = [pscustomobject]@{
    contract="NUSANTARA-V1-READINESS-SCAN"
    run_id=$RunId
    started_at=$Started.ToString("o")
    completed_at=(Get-Date).ToString("o")
    repository=$Root
    mode=$(if($RunTests){"READ_ONLY_PLUS_FOCUSED_TESTS"}else{"READ_ONLY"})
    boundaries=@(
      "No source edits","No git reset/clean/checkout","No database migration or writes",
      "No external service calls","Test results depend on local environment"
    )
    inventory=$inventory
    findings=@($script:Findings)
    commands=@($script:Commands | ForEach-Object {
        [pscustomobject]@{name=$_.name; executable=$_.executable; arguments=$_.arguments;
            working_directory=$_.working_directory; exit_code=$_.exit_code; output_file=("$($_.name).txt")}
    })
}
$Report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ReportDir "report.json") -Encoding UTF8

# Human-readable summary
$md = [System.Collections.Generic.List[string]]::new()
$md.Add("# Nusantara V1 Readiness Scan")
$md.Add("")
$md.Add("- Run ID: $RunId")
$md.Add("- Repository: ``$Root``")
$md.Add("- Mode: $(if($RunTests){"read-only + focused tests"}else{"read-only"})")
$md.Add("- Completed: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz"))")
$md.Add("")
$md.Add("> This is a scan report, not an acceptance certificate. Text matches do not prove runtime execution.")
$md.Add("")
$md.Add("## Findings")
$md.Add("")
$md.Add("| Area | Severity | Status | Finding |")
$md.Add("|---|---|---|---|")
foreach ($f in $script:Findings) {
    $title = $f.title.Replace("|","\|")
    $md.Add("| $($f.area) | $($f.severity) | $($f.status) | $title |")
}
$md.Add("")
$md.Add("## Recommended review order")
$md.Add("1. ``grounding-rag-matches.json`` — validate evidence flow and rejection paths.")
$md.Add("2. ``runtime-v1-matches.json`` — trace actual ``/v1/chat`` handler to provider/fallback.")
$md.Add("3. ``memory-governance-matches.json`` — trace persistence, approval, trust/policy and public response projection.")
$md.Add("4. ``git-status.txt`` and diff summaries — protect existing local changes.")
$md.Add("5. ``pytest-focused.txt`` if tests were requested; resolve root causes before modifying code.")
$md.Add("")
$md.Add("## Files")
$md.Add("- ``report.json``: machine-readable summary")
$md.Add("- ``inventory.json``: file counts")
$md.Add("- ``*-matches.json``: source matches with file and line")
$md | Set-Content -LiteralPath (Join-Path $ReportDir "report.md") -Encoding UTF8

Write-Host ""
Write-Host "Nusantara V1 readiness scan selesai." -ForegroundColor Green
Write-Host "Laporan: $ReportDir" -ForegroundColor Cyan
Write-Host "Ringkasan: $(Join-Path $ReportDir 'report.md')"
Write-Host "JSON: $(Join-Path $ReportDir 'report.json')"
Write-Host ""
Write-Host "Catatan: script ini mengumpulkan bukti dan tes opsional; tidak mengubah kode secara otomatis." -ForegroundColor Yellow
