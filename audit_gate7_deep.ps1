$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA AI V1 - GATE 7 DEEP RAG AUDIT" -ForegroundColor Cyan
Write-Host " READ-ONLY" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

function Show-Context {
    param(
        [string]$File,
        [int]$PatternLine,
        [int]$Before = 5,
        [int]$After = 10
    )

    if (-not (Test-Path $File)) { return }

    $lines = Get-Content $File
    $start = [Math]::Max(0, $PatternLine - 1 - $Before)
    $end   = [Math]::Min($lines.Count - 1, $PatternLine - 1 + $After)

    Write-Host ""
    Write-Host "FILE: $File | around line $PatternLine" -ForegroundColor DarkCyan

    for ($i = $start; $i -le $end; $i++) {
        $prefix = "{0,5}" -f ($i + 1)
        if (($i + 1) -eq $PatternLine) {
            Write-Host "$prefix > $($lines[$i])" -ForegroundColor Yellow
        } else {
            Write-Host "$prefix   $($lines[$i])"
        }
    }
}

function Find-First {
    param(
        [string[]]$Paths,
        [string[]]$Patterns
    )

    foreach ($path in $Paths) {
        if (-not (Test-Path $path)) { continue }

        foreach ($pattern in $Patterns) {
            $hits = Select-String -Path $path -Pattern $pattern -CaseSensitive:$false

            foreach ($hit in $hits | Select-Object -First 3) {
                Show-Context -File $hit.Path -PatternLine $hit.LineNumber
            }
        }
    }
}

# ============================================================
# 5 RERANKER
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[5] RERANKER" -ForegroundColor Cyan
Write-Host "============================================================"

Find-First `
    -Paths @("app\knowledge\rag.py","app\knowledge\reranker.py","app\v2\orchestrator.py") `
    -Patterns @(
        'def .*rerank',
        'class .*Rerank',
        '_simple_rerank',
        'reranker_enabled',
        'reranker_model',
        'rerank='
    )

# ============================================================
# 6 GROUNDING -> LLM
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[6] GROUNDING -> LLM" -ForegroundColor Cyan
Write-Host "============================================================"

Find-First `
    -Paths @("app\api\routes.py","app\api\v2_routes.py","app\knowledge\grounding.py","app\hermes","app\v2") `
    -Patterns @(
        'EvidenceGroundingGuard',
        'evidence_pack',
        '\.evidence',
        'grounded',
        'grounding',
        'context',
        'prompt',
        'generate',
        'chat'
    )

# ============================================================
# 7 PROVENANCE / CITATION
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[7] PROVENANCE / CITATION" -ForegroundColor Cyan
Write-Host "============================================================"

Find-First `
    -Paths @("app\knowledge","app\trust","app\v2","app\api") `
    -Patterns @(
        'provenance',
        'citation',
        'source=',
        'document_id=',
        'chunk_id=',
        'verification',
        'verified',
        'authority'
    )

# ============================================================
# 8 CONFLICT / VERSION
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[8] CONFLICT / VERSION AWARENESS" -ForegroundColor Cyan
Write-Host "============================================================"

Find-First `
    -Paths @("app\knowledge","app\trust","app\v2","app\api") `
    -Patterns @(
        'conflict',
        'contradict',
        'inconsisten',
        'version',
        'effective',
        'valid_from',
        'valid_until',
        'supersed',
        'obsolete',
        'deprecated'
    )

# ============================================================
# 9 BENCHMARK
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[9] RAG BENCHMARK / EVALUATION" -ForegroundColor Cyan
Write-Host "============================================================"

$testFiles = Get-ChildItem tests -Recurse -File -Include *.py,*.md -ErrorAction SilentlyContinue

foreach ($pattern in @(
    'benchmark',
    'retrieval',
    'mrr',
    'ndcg',
    'precision',
    'recall',
    'hit_rate',
    'groundedness',
    'faithfulness',
    'golden'
)) {
    foreach ($hit in ($testFiles | Select-String -Pattern $pattern -CaseSensitive:$false | Select-Object -First 5)) {
        Show-Context -File $hit.Path -PatternLine $hit.LineNumber -Before 3 -After 6
    }
}

# ============================================================
# TEST INVENTORY
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "RAG TEST INVENTORY" -ForegroundColor Cyan
Write-Host "============================================================"

Get-ChildItem tests -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match 'rag|retriev|ground|knowledge|embedding|rerank'
    } |
    Select-Object FullName |
    Format-Table -AutoSize

# ============================================================
# FINAL
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "GATE 7 DEEP AUDIT SELESAI" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Belum ada perubahan source code."
Write-Host "Belum ada migration."
Write-Host "Belum ada perubahan Core V1."
Write-Host "Belum ada implementasi perbaikan."
Write-Host ""
