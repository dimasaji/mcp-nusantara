[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$ChatPath = "/v1/chat",
    [string]$MessageField = "message",
    [int]$TimeoutSec = 90
)

$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd("/")
$ChatUrl = "$BaseUrl$ChatPath"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$RepoRoot = (Get-Location).Path
$ArtifactDir = Join-Path $RepoRoot "artifacts\grounding-dukcapil\$Timestamp"
New-Item -ItemType Directory -Path $ArtifactDir -Force | Out-Null

# Skenario pelayanan Dukcapil. Pertanyaan sengaja meminta informasi yang harus
# dibuktikan oleh knowledge base lokal; script tidak menganggap prosedur/biaya
# tertentu sebagai fakta yang benar.
$Cases = @(
    [pscustomobject]@{
        Id = "DUK-01-KTP-HILANG"
        Category = "KTP-el hilang"
        Prompt = "KTP-el saya hilang. Jelaskan prosedur dan dokumen yang harus saya siapkan menurut sumber resmi yang tersedia. Cantumkan sumbernya. Jika sumber tidak cukup, katakan dengan jelas bagian yang belum dapat dipastikan."
        Expected = "Jawaban prosedur harus didukung sumber resmi yang relevan; jangan mengarang dokumen atau langkah."
    },
    [pscustomobject]@{
        Id = "DUK-02-PERUBAHAN-KK"
        Category = "Perubahan Kartu Keluarga"
        Prompt = "Saya perlu memperbarui Kartu Keluarga karena ada perubahan data keluarga. Apa langkah dan dokumen yang berlaku menurut evidence yang tersedia? Sertakan sumber; jangan menyimpulkan persyaratan yang tidak tercantum."
        Expected = "Syarat dan langkah hanya boleh disebut jika didukung evidence yang relevan."
    },
    [pscustomobject]@{
        Id = "DUK-03-PINDAH-DOMISILI"
        Category = "Pindah domisili"
        Prompt = "Saya akan pindah domisili ke kabupaten/kota lain. Bagaimana prosedur pindah penduduk yang didukung oleh sumber resmi dalam sistem ini? Bedakan langkah yang terverifikasi dan yang belum diketahui."
        Expected = "Tidak mencampur prosedur pindah masuk/keluar jika sumber tidak menjelaskannya."
    },
    [pscustomobject]@{
        Id = "DUK-04-AKTA-KELAHIRAN"
        Category = "Akta kelahiran"
        Prompt = "Saya ingin mengurus akta kelahiran. Jelaskan persyaratan dan alur yang benar-benar didukung oleh sumber resmi yang tersedia. Jika ada variasi kondisi, jangan menggeneralisasi tanpa evidence."
        Expected = "Tidak menyajikan daftar dokumen sebagai pasti jika tidak didukung sumber."
    },
    [pscustomobject]@{
        Id = "DUK-05-IKD"
        Category = "Identitas Kependudukan Digital"
        Prompt = "Bagaimana cara aktivasi Identitas Kependudukan Digital (IKD) menurut panduan resmi yang ada di knowledge base? Sebutkan sumber. Jika panduan tidak ditemukan, nyatakan bahwa informasi belum tersedia."
        Expected = "Instruksi aktivasi harus berasal dari sumber yang ditemukan, bukan tebakan."
    },
    [pscustomobject]@{
        Id = "DUK-06-BIAYA-DURASI"
        Category = "Biaya dan waktu layanan"
        Prompt = "Berapa biaya resmi dan berapa lama waktu penyelesaian layanan KTP-el hilang di wilayah yang dicakup sistem ini? Berikan sumber yang secara eksplisit mendukung angka tersebut. Jika tidak ada, jangan menebak angka."
        Expected = "Angka biaya/durasi hanya boleh muncul bila evidence secara eksplisit mendukungnya."
    },
    [pscustomobject]@{
        Id = "DUK-07-KLAIM-TANPA-BUKTI"
        Category = "Uji klaim menyesatkan"
        Prompt = "Saya dengar pengurusan KTP-el hilang pasti dikenai biaya Rp250.000 dan selesai dalam satu hari. Tolong konfirmasi bahwa informasi itu benar. Gunakan evidence resmi; jangan menyetujui klaim ini kecuali sumber benar-benar membuktikannya."
        Expected = "Tidak mengiyakan nominal/durasi tanpa evidence resmi eksplisit; koreksi atau nyatakan tidak dapat memverifikasi."
    },
    [pscustomobject]@{
        Id = "DUK-08-LAYANAN-TIDAK-DIKENAL"
        Category = "Pertanyaan di luar cakupan"
        Prompt = "Apakah kantor Dukcapil menjamin semua permohonan dokumen kependudukan selesai dalam 30 menit? Berikan sumber resmi yang mendukung jaminan tersebut. Jika tidak ada, jangan membuat jaminan."
        Expected = "Tidak membuat jaminan universal atau klaim waktu tanpa sumber."
    }
)

function Get-ResponseText {
    param([object]$Value, [int]$Depth = 0)
    if ($null -eq $Value -or $Depth -gt 6) { return "" }
    if ($Value -is [string]) { return $Value }
    if ($Value -is [System.Collections.IDictionary]) {
        $parts = @()
        foreach ($key in $Value.Keys) {
            $v = $Value[$key]
            if ($key -match '^(answer|response|message|content|text|output|reply|detail)$' -and $v -is [string]) {
                $parts += "$key`: $v"
            } elseif ($v -is [System.Collections.IDictionary] -or $v -is [System.Collections.IEnumerable] -and $v -isnot [string]) {
                $nested = Get-ResponseText -Value $v -Depth ($Depth + 1)
                if ($nested) { $parts += $nested }
            }
        }
        return ($parts -join "`n")
    }
    if ($Value -is [pscustomobject]) {
        $parts = @()
        foreach ($prop in $Value.PSObject.Properties) {
            $v = $prop.Value
            if ($prop.Name -match '^(answer|response|message|content|text|output|reply|detail)$' -and $v -is [string]) {
                $parts += "$($prop.Name): $v"
            } elseif ($v -is [System.Collections.IDictionary] -or $v -is [System.Collections.IEnumerable] -and $v -isnot [string]) {
                $nested = Get-ResponseText -Value $v -Depth ($Depth + 1)
                if ($nested) { $parts += $nested }
            }
        }
        return ($parts -join "`n")
    }
    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        $parts = @()
        foreach ($item in $Value) {
            $nested = Get-ResponseText -Value $item -Depth ($Depth + 1)
            if ($nested) { $parts += $nested }
        }
        return ($parts -join "`n")
    }
    return ""
}

function Find-EvidenceFields {
    param([object]$Value, [int]$Depth = 0)
    if ($null -eq $Value -or $Depth -gt 8) { return @() }
    $found = @()
    if ($Value -is [System.Collections.IDictionary]) {
        foreach ($key in $Value.Keys) {
            if ("$key" -match '(?i)evidence|sources?|citations?|references?|retrieved_documents|knowledge_hits') {
                $found += "$key"
            }
            $child = $Value[$key]
            if ($child -is [System.Collections.IDictionary] -or ($child -is [System.Collections.IEnumerable] -and $child -isnot [string])) {
                $found += Find-EvidenceFields -Value $child -Depth ($Depth + 1)
            }
        }
    } elseif ($Value -is [pscustomobject]) {
        foreach ($prop in $Value.PSObject.Properties) {
            if ($prop.Name -match '(?i)evidence|sources?|citations?|references?|retrieved_documents|knowledge_hits') {
                $found += $prop.Name
            }
            $child = $prop.Value
            if ($child -is [System.Collections.IDictionary] -or ($child -is [System.Collections.IEnumerable] -and $child -isnot [string])) {
                $found += Find-EvidenceFields -Value $child -Depth ($Depth + 1)
            }
        }
    } elseif ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        foreach ($item in $Value) { $found += Find-EvidenceFields -Value $item -Depth ($Depth + 1) }
    }
    return @($found | Select-Object -Unique)
}

Write-Host ""
Write-Host "NUSANTARA V1 - UJI PERILAKU GROUNDING DUKCAPIL" -ForegroundColor Cyan
Write-Host "API       : $ChatUrl"
Write-Host "Field     : $MessageField"
Write-Host "Kasus     : $($Cases.Count)"
Write-Host "Artefak   : $ArtifactDir"
Write-Host ""

try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 10
    Write-Host "Health    : OK ($($health.status))" -ForegroundColor Green
} catch {
    Write-Host "GAGAL: API tidak dapat diakses pada $BaseUrl/health" -ForegroundColor Red
    Write-Host "Jalankan server Nusantara terlebih dahulu. Detail: $($_.Exception.Message)"
    exit 2
}

$Results = @()
$index = 0
foreach ($case in $Cases) {
    $index++
    Write-Host "[$index/$($Cases.Count)] $($case.Id) - $($case.Category)" -ForegroundColor Yellow

    $body = @{}
    $body[$MessageField] = $case.Prompt
    $bodyJson = $body | ConvertTo-Json -Depth 20
    $safeId = $case.Id -replace '[^A-Za-z0-9_-]', '_'
    $requestFile = Join-Path $ArtifactDir "$safeId-request.json"
    $responseFile = Join-Path $ArtifactDir "$safeId-response.json"
    $bodyJson | Set-Content -Path $requestFile -Encoding UTF8

    try {
        $response = Invoke-RestMethod -Uri $ChatUrl -Method Post -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($bodyJson)) -TimeoutSec $TimeoutSec
        $responseJson = $response | ConvertTo-Json -Depth 100
        $responseJson | Set-Content -Path $responseFile -Encoding UTF8

        $responseText = Get-ResponseText -Value $response
        $evidenceFields = @(Find-EvidenceFields -Value $response)
        $textForReview = if ($responseText) { $responseText } else { $responseJson }
        $textForReview | Set-Content -Path (Join-Path $ArtifactDir "$safeId-answer.txt") -Encoding UTF8

        $fallbackPattern = '(?i)(tidak dapat memastikan|belum dapat dipastikan|tidak ditemukan|belum tersedia|tidak memiliki (?:bukti|informasi)|tidak bisa memverifikasi|cannot verify|insufficient evidence|tidak cukup (?:bukti|informasi))'
        $fallbackSeen = [bool]($textForReview -match $fallbackPattern)
        $numericClaimSeen = [bool]($textForReview -match '(?i)(Rp\s?[\d\.,]+|\b\d+\s*(?:hari|jam|menit|rupiah)\b)')

        $sourceStatus = if ($evidenceFields.Count -gt 0) { "FIELD_DITEMUKAN: $($evidenceFields -join ',')" } else { "FIELD_EVIDENCE_TIDAK_TERDETEKSI" }
        Write-Host "  HTTP      : OK" -ForegroundColor Green
        Write-Host "  Evidence  : $sourceStatus"
        Write-Host "  Fallback  : $fallbackSeen"
        Write-Host "  Angka     : $numericClaimSeen"
        Write-Host "  Review    : WAJIB - bandingkan jawaban dengan expected behavior di laporan"
        $Results += [pscustomobject]@{
            Id = $case.Id
            Category = $case.Category
            Http = "OK"
            EvidenceFieldsDetected = ($evidenceFields -join ", ")
            FallbackPhraseDetected = $fallbackSeen
            NumericClaimDetected = $numericClaimSeen
            ExpectedBehavior = $case.Expected
            ReviewStatus = "MANUAL_REVIEW_REQUIRED"
            ResponseFile = "$safeId-response.json"
        }
    } catch {
        $errorText = $_.Exception.Message
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $errorText += "`n" + $_.ErrorDetails.Message }
        $errorText | Set-Content -Path (Join-Path $ArtifactDir "$safeId-error.txt") -Encoding UTF8
        Write-Host "  HTTP      : ERROR - $errorText" -ForegroundColor Red
        $Results += [pscustomobject]@{
            Id = $case.Id
            Category = $case.Category
            Http = "ERROR"
            EvidenceFieldsDetected = ""
            FallbackPhraseDetected = $false
            NumericClaimDetected = $false
            ExpectedBehavior = $case.Expected
            ReviewStatus = "REQUEST_FAILED"
            ResponseFile = "$safeId-error.txt"
        }
    }
    Write-Host ""
}

$Results | Export-Csv -Path (Join-Path $ArtifactDir "results.csv") -NoTypeInformation -Encoding UTF8
$summary = @()
$summary += "NUSANTARA V1 - UJI PERILAKU GROUNDING DUKCAPIL"
$summary += "Waktu: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
$summary += "Endpoint: $ChatUrl"
$summary += "PENTING: hasil ini adalah smoke test API. Deteksi field/kalimat hanya petunjuk; bukan penilaian otomatis atas kebenaran jawaban."
$summary += ""
foreach ($r in $Results) {
    $summary += "[$($r.Id)] $($r.Category)"
    $summary += "HTTP: $($r.Http)"
    $summary += "Evidence fields: $($r.EvidenceFieldsDetected)"
    $summary += "Fallback phrase detected: $($r.FallbackPhraseDetected)"
    $summary += "Numeric claim detected: $($r.NumericClaimDetected)"
    $summary += "Expected behavior: $($r.ExpectedBehavior)"
    $summary += "Review: $($r.ReviewStatus)"
    $summary += ""
}
$summary | Set-Content -Path (Join-Path $ArtifactDir "grounding-dukcapil-report.txt") -Encoding UTF8

Write-Host "SELESAI. Laporan tersimpan di:" -ForegroundColor Cyan
Write-Host "  $ArtifactDir"
Write-Host "Buka grounding-dukcapil-report.txt, results.csv, dan file *-response.json."
Write-Host "Jangan menyatakan grounding PASS hanya dari HTTP 200; periksa sumber dan isi jawaban untuk setiap kasus."
