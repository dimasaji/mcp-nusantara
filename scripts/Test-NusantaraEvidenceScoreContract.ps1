$ErrorActionPreference = 'Stop'
$Root = (Get-Location).Path

$Files = @(
    'app\hermes\agent.py',
    'app\knowledge\engine.py',
    'app\knowledge\rag.py',
    'app\api\routes.py'
)

foreach ($Relative in $Files) {
    $Path = Join-Path $Root $Relative
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "ABORT: File tidak ditemukan: $Relative"
    }
}

Write-Host "`n=== 1. GATE 7: SKOR YANG DIBACA ===" -ForegroundColor Cyan
Select-String `
    -Path '.\app\hermes\agent.py' `
    -Pattern 'def _evidence_score|consumer_post_filter|_evidence_score\(item\)' `
    -Context 2,8

Write-Host "`n=== 2. ENGINE: KONVERSI HASIL RAG ===" -ForegroundColor Cyan
Select-String `
    -Path '.\app\knowledge\engine.py' `
    -Pattern 'RetrievalEvidenceList|evidence_pack\.evidence|search_knowledge' `
    -Context 2,5

Write-Host "`n=== 3. MODEL EVIDENCE DI SELURUH APP ===" -ForegroundColor Cyan
Get-ChildItem '.\app' -Recurse -File -Filter '*.py' |
    Select-String `
        -Pattern 'class Evidence\b|class RetrievalEvidenceList\b|score\s*:' `
        -Context 2,6 |
    ForEach-Object {
        '{0}:{1}: {2}' -f $_.Path, $_.LineNumber, $_.Line.Trim()
        $_.Context.PreContext
        $_.Context.PostContext
        ''
    }

Write-Host "`n=== 4. HASIL ===" -ForegroundColor Yellow
Write-Host 'Pemeriksaan selesai. Source tidak diubah.'
Write-Host 'Pastikan field skor Evidence kanonis sebelum menerapkan patch.'