$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path (Split-Path $PSScriptRoot))
Set-Location -LiteralPath $root
$evidenceRoot='docs/reports/weip-completion-20261009T104250Z'
$audit=Get-Content -LiteralPath ($evidenceRoot+'/CHANGE_AUDIT.json') -Raw | ConvertFrom-Json
$baseline=Get-Content -LiteralPath ($evidenceRoot+'/BASELINE.json') -Raw | ConvertFrom-Json
$report=Get-Content -LiteralPath ($evidenceRoot+'/IMPLEMENTATION_REPORT.md') -Raw
$refs=@('BASELINE.json','CHANGE_AUDIT.json','SCOPED_CHANGES.patch','IMPLEMENTATION_REPORT.md' | ForEach-Object { $evidenceRoot+'/'+$_ })
$refs+='docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json'
$tests=@()
foreach($test in $audit.tests){
  $ref=$test.evidence.Replace('\','/')
  [xml]$xml=Get-Content -LiteralPath $ref -Raw
  $suite=$xml.testsuites.testsuite
  $tests+=@{id=(Split-Path (Split-Path $ref) -Leaf); reference=$ref; tests=[int]$suite.tests; failures=[int]$suite.failures; errors=[int]$suite.errors; skipped=[int]$suite.skipped; exitCode=$test.guards.pytest_exit; status=$(if([int]$suite.failures -gt 0 -or [int]$suite.errors -gt 0){'FAIL'}else{'PASS'}); deselected=$(if($ref -like '*regression*'){6}else{53}); violations=@($test.guards.violations); historical=$true}
  $refs+=$ref
  $refs+=((Split-Path $ref).Replace('\','/')+'/guards.json')
}
$gates=@()
foreach($line in ($report -split "`n")){
  if($line -match '^\| (WEIP-\d{2}) ([^|]+)\| ([A-Z_]+) \| ([^|]+)\|'){
    $gates+=@{id=$Matches[1]; name=$Matches[2].Trim(); status=$Matches[3]; detail=$Matches[4].Trim(); reference=$evidenceRoot+'/IMPLEMENTATION_REPORT.md'}
  }
}
if($gates.Count -ne 12){throw 'Expected twelve documented WEIP gates'}
$sources=@($refs | Sort-Object -Unique | ForEach-Object { @{path=$_; sha256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLower()} })
$review=@{id='WEIP-COMP-DB-01'; status='REVIEW_REQUIRED'; attribution='NOT_VERIFIED'; reference=$evidenceRoot+'/CHANGE_AUDIT.json'; explanation='Bukti historis mencatat WAL/SHM tidak ditemukan pada pemeriksaan akhir. Penyebab dan pelaku tidak terbukti. Hash database utama saat itu tetap sama; ini tidak membuktikan keadaan logis database tetap sama.'; databaseInspectedNow=$false}
$data=@{capturedAt=$audit.at_utc; mode='HISTORICAL_ARTIFACT_SNAPSHOT'; v1='FAIL / HOLD'; v2='DEFERRED'; weip='PARTIAL / REVIEW_REQUIRED'; activeIntegration='NOT_AUTHORIZED'; head=$audit.head.stdout.Trim(); branch=$audit.branch.stdout.Trim(); diskFingerprint=$audit.disk_app_py_fingerprint; fingerprintScope=$audit.fingerprint_algorithm; runtimeIdentity='NOT_VERIFIED'; preservation=$review; tests=$tests; gates=$gates; sources=$sources; phases=@(0..21 | ForEach-Object { @{id=$_; status='NOT_VERIFIED'; detail='Bukti penerimaan yang terikat ke fase dan target build belum dipetakan. Status WEIP tidak mengesahkan fase ini.'} }); blockers=(Get-Content -LiteralPath 'docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json' -Raw | ConvertFrom-Json).gates}
('export default '+($data | ConvertTo-Json -Depth 12)+';') | Set-Content -LiteralPath control-plane/src/engineering-evidence.ts -Encoding utf8
$review | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath ($PSScriptRoot+'/PRESERVATION_REVIEW.json') -Encoding utf8
