$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA AI V1 - GATE 7 RAG GAP AUDIT" -ForegroundColor Cyan
Write-Host " READ-ONLY / NO CODE CHANGES" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$root = (Get-Location).Path
$files = Get-ChildItem app,tests -Recurse -File -Include *.py,*.md,*.json,*.yaml,*.yml -ErrorAction SilentlyContinue

function Section($number, $title) {
    Write-Host ""
    Write-Host "[$number] $title" -ForegroundColor Cyan
    Write-Host "------------------------------------------------------------"
}

function Search-Pattern($patterns) {
    $results = @()

    foreach ($p in $patterns) {
        $results += $files | Select-String -Pattern $p -CaseSensitive:$false
    }

    $results |
        Sort-Object Path,LineNumber -Unique |
        Select-Object Path,LineNumber,Line |
        Format-Table -AutoSize
}

# ============================================================
# 5. RERANKER
# ============================================================

Section "5" "RERANKER"

Write-Host "Cari implementasi dan pemanggilan reranker..." -ForegroundColor Yellow

Search-Pattern @(
    'rerank',
    'reranker',
    '_simple_rerank',
    'reranker_enabled',
    'reranker_model'
)

Write-Host ""
Write-Host "KESIMPULAN AWAL:" -ForegroundColor Yellow
Write-Host "- Ada implementasi reranker      : periksa hasil di atas"
Write-Host "- Ada fallback sederhana        : periksa _simple_rerank"
Write-Host "- Model reranker nyata aktif     : BELUM disimpulkan oleh script"
Write-Host "- Audit bersifat READ-ONLY"

# ============================================================
# 6. GROUNDING -> LLM
# ============================================================

Section "6" "GROUNDING -> LLM"

Write-Host "Mencari alur Evidence -> Grounding -> Prompt/LLM..." -ForegroundColor Yellow

Search-Pattern @(
    'EvidenceGroundingGuard',
    'evidence_pack',
    'evidence_pack\.evidence',
    'grounding',
    'grounded',
    'grounded_context',
    'context.*evidence',
    'evidence.*context',
    'prompt.*evidence',
    'evidence.*prompt',
    'system_prompt',
    'user_prompt',
    'generate\(',
    'chat\('
)

Write-Host ""
Write-Host "KESIMPULAN AWAL:" -ForegroundColor Yellow
Write-Host "- Apakah evidence hanya dibuat?      : lihat jalur evidence_pack"
Write-Host "- Apakah evidence masuk grounding?  : lihat EvidenceGroundingGuard"
Write-Host "- Apakah grounding masuk prompt LLM?: lihat prompt/context"
Write-Host "- Status final tetap perlu verifikasi manual berdasarkan alur kode."

# ============================================================
# 7. PROVENANCE / CITATION
# ============================================================

Section "7" "PROVENANCE / CITATION"

Write-Host "Mencari source, provenance, citation, document identity..." -ForegroundColor Yellow

Search-Pattern @(
    'provenance',
    'citation',
    'citations',
    'source',
    'document_id',
    'chunk_id',
    'chunk_index',
    'start_char',
    'end_char',
    'verification',
    'verified',
    'authority'
)

Write-Host ""
Write-Host "KESIMPULAN AWAL:" -ForegroundColor Yellow
Write-Host "- Evidence source fields tersedia?      : lihat hasil"
Write-Host "- Provenance eksplisit tersedia?        : lihat hasil"
Write-Host "- Citation end-to-end ke jawaban LLM?   : BELUM otomatis dianggap terbukti"
Write-Host "- Verification/authority metadata?      : lihat hasil"

# ============================================================
# 8. CONFLICT / VERSION
# ============================================================

Section "8" "CONFLICT / VERSION AWARENESS"

Write-Host "Mencari conflict detection dan version awareness..." -ForegroundColor Yellow

Search-Pattern @(
    'conflict',
    'contradict',
    'inconsisten',
    'inconsistent',
    'version',
    'effective',
    'valid_from',
    'valid_until',
    'supersed',
    'obsolete',
    'deprecated',
    'authority',
    'priority',
    'precedence'
)

Write-Host ""
Write-Host "KESIMPULAN AWAL:" -ForegroundColor Yellow
Write-Host "- Conflict detection runtime?       : lihat hasil"
Write-Host "- Document/version awareness?       : lihat hasil"
Write-Host "- Effective-date handling?          : lihat hasil"
Write-Host "- Superseded/obsolete handling?     : lihat hasil"
Write-Host "- Jangan menyimpulkan PASS hanya karena field version ada."

# ============================================================
# 9. BENCHMARK
# ============================================================

Section "9" "RAG BENCHMARK / EVALUATION"

Write-Host "Mencari benchmark retrieval dan evaluation..." -ForegroundColor Yellow

Search-Pattern @(
    'benchmark',
    'retrieval.*eval',
    'eval.*retrieval',
    'evaluation',
    'precision',
    'recall',
    'hit_rate',
    'mrr',
    'ndcg',
    'groundedness',
    'faithfulness',
    'relevance',
    'golden',
    'test.*rag',
    'rag.*test',
    'retrieval.*test'
)

Write-Host ""
Write-Host "KESIMPULAN AWAL:" -ForegroundColor Yellow
Write-Host "- Benchmark khusus RAG tersedia?       : lihat hasil"
Write-Host "- Retrieval quality metric tersedia?   : lihat hasil"
Write-Host "- Golden dataset tersedia?             : lihat hasil"
Write-Host "- 70/30 hybrid weight tervalidasi?     : BELUM dianggap tervalidasi tanpa benchmark"

# ============================================================
# FINAL STRUCTURED SUMMARY
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GATE 7 - STATUS AUDIT SEMENTARA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "5. Reranker              : 🟡 GAP" -ForegroundColor Yellow
Write-Host "6. Grounding -> LLM      : 🟡 VERIFIKASI" -ForegroundColor Yellow
Write-Host "7. Provenance/Citation   : 🟡 VERIFIKASI" -ForegroundColor Yellow
Write-Host "8. Conflict/Version      : 🟡 VERIFIKASI" -ForegroundColor Yellow
Write-Host "9. Benchmark             : 🟡 VERIFIKASI" -ForegroundColor Yellow

Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Red
Write-Host "Script ini READ-ONLY."
Write-Host "Tidak membuat, menghapus, atau mengubah file."
Write-Host "Tidak menjalankan migration."
Write-Host "Tidak mengubah Core V1."
Write-Host "Tidak memperbaiki bug."
Write-Host ""
Write-Host "Audit selesai." -ForegroundColor Green
