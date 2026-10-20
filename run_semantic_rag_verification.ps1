$ErrorActionPreference = "Continue"
$Root = "C:\Users\dmaza\mcp-starter"
Set-Location $Root

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = Join-Path $Root "reports\semantic-rag-verification\$Stamp"
New-Item -ItemType Directory -Path $Out -Force | Out-Null
$Log = Join-Path $Out "execution.log"
$Results = @()

function Run-Tests($Stage, $Pattern) {
    $Files = @(
        Get-ChildItem "$Root\tests" -Recurse -File -Filter "test_*.py" `
            -ErrorAction SilentlyContinue |
        Where-Object {
            Select-String -Path $_.FullName -Pattern $Pattern `
                -Quiet -ErrorAction SilentlyContinue
        } | Select-Object -ExpandProperty FullName -Unique
    )

    if ($Files.Count -eq 0) {
        $script:Results += [pscustomobject]@{
            stage=$Stage; status="NOT VERIFIED"; detail="Tidak ada file tes cocok"
        }
        return
    }

    "TEST: $Stage" | Tee-Object -FilePath $Log -Append
    $Files | ForEach-Object { $_ | Tee-Object -FilePath $Log -Append }

    & python -m pytest -q @Files 2>&1 |
        Tee-Object -FilePath $Log -Append
    $Code = $LASTEXITCODE

    $Status = if ($Code -eq 0) { "PASS" }
              elseif ($Code -eq 5) { "NOT VERIFIED" }
              else { "FAIL" }

    $script:Results += [pscustomobject]@{
        stage=$Stage; status=$Status
        detail="pytest exit code $Code; jumlah file tes $($Files.Count)"
    }
}

try {
    # Tahap 1: regresi Semantic Retriever
    Run-Tests "Semantic Retriever Regression" `
        "production_semantic_retriever|semantic_retriever"

    # Tahap 2: hydration dan integritas evidence
    Run-Tests "Evidence Integrity" `
        "hydrate_document_metadata|hydration|evidence|grounding"

    # Tahap 3A: tes RAG/API yang telah tersedia di repositori
    Run-Tests "RAG API Regression" `
        "TestClient|/v1/chat|health/detail|grounded|rag"

    # Tahap 3B: pemeriksaan health API (GET saja)
    try {
        $Health = Invoke-RestMethod `
            -Uri "http://127.0.0.1:8000/v1/health/detail" `
            -Method Get -TimeoutSec 5
        $Health | ConvertTo-Json -Depth 12 |
            Set-Content (Join-Path $Out "api-health.json") -Encoding utf8

        $Results += [pscustomobject]@{
            stage="API Health"; status="PASS"
            detail="Endpoint merespons; rincian ada di api-health.json"
        }
    }
    catch {
        $Results += [pscustomobject]@{
            stage="API Health"; status="NOT VERIFIED"
            detail=$_.Exception.Message
        }
    }

    # Tahap 4: simpan bukti dan hitung status
    $Failed = @($Results | Where-Object status -eq "FAIL").Count
    $Unknown = @($Results | Where-Object {
        $_.status -eq "NOT VERIFIED" -or $_.status -eq "PARTIAL"
    }).Count

    $Overall = if ($Failed -gt 0) { "FAIL" }
               elseif ($Unknown -gt 0) { "PARTIAL" }
               else { "PASS" }

    [pscustomobject]@{
        project=$Root
        generated_at=(Get-Date).ToString("o")
        overall_status=$Overall
        results=@($Results)
        note="PASS hanya berlaku untuk pemeriksaan yang benar-benar dijalankan."
    } | ConvertTo-Json -Depth 10 |
        Set-Content (Join-Path $Out "summary.json") -Encoding utf8

    $Results | Format-Table stage,status,detail -Wrap -AutoSize
    Write-Host "`nSTATUS AKHIR: $Overall"
    Write-Host "BUKTI: $Out"
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
