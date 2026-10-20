param([switch]$IncludeChat, [string]$EvidenceDirectory)
. "$PSScriptRoot/../service/local-services.ps1"
if (-not $EvidenceDirectory) { $EvidenceDirectory = Join-Path $script:Repository ('artifacts/NCP-V1-AUTOSTART-001/live-' + (Get-Date -Format yyyyMMdd-HHmmss)) }
New-Item -ItemType Directory -Path $EvidenceDirectory -Force | Out-Null
$results = @()
foreach ($probe in @(
    @{name='backend';url='http://127.0.0.1:8000/health'},
    @{name='frontend';url='http://127.0.0.1:5180/'},
    @{name='proxy';url='http://127.0.0.1:5180/health'},
    @{name='model-api';url='http://127.0.0.1:5180/v1/control-plane/model-status'},
    @{name='knowledge-documents';url='http://127.0.0.1:8000/v1/knowledge/documents'},
    @{name='ollama';url='http://127.0.0.1:11434/api/version'}
)) {
    $ok = Test-Http $probe.url
    $results += [pscustomobject]@{name=$probe.name;status=$(if($ok){'PASS'}else{'FAIL'});url=$probe.url}
}
if ($IncludeChat) {
    # Dedicated new session: appends test history only, never edits existing conversations/SOPs.
    foreach ($question in @('Apa fungsi Nusantara?', 'Apa itu KTP-el?')) {
        $session = 'web-' + [Guid]::NewGuid().ToString()
        try {
            $body = @{user_input=$question;session_id=$session;request_id=[Guid]::NewGuid().ToString('N')} | ConvertTo-Json
            $reply = Invoke-RestMethod -Uri 'http://127.0.0.1:5180/v1/chat' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120
            $valid = -not [string]::IsNullOrWhiteSpace($reply.response)
            $results += [pscustomobject]@{name='chat';question=$question;session=$session;status=$(if($valid){'PASS'}else{'FAIL'});
                provider=$reply.provider_status;evidenceCount=@($reply.evidence).Count;grounded=$reply.grounding.grounded}
        } catch {
            $httpStatus = if ($_.Exception -is [Net.WebException] -and $_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { $null }
            $results += [pscustomobject]@{name='chat';question=$question;session=$session;status='FAIL';errorType=$_.Exception.GetType().Name;httpStatus=$httpStatus}
        }
    }
}
$status = Get-LocalStatus
$status | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $EvidenceDirectory 'runtime.json') -Encoding UTF8
$results | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $EvidenceDirectory 'checks.json') -Encoding UTF8
$results | Format-Table -AutoSize
if (@($results | Where-Object status -eq 'FAIL').Count) { exit 1 }
