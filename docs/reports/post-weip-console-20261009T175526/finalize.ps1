$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path (Split-Path $PSScriptRoot))
Set-Location -LiteralPath $root
$base=Get-Content -LiteralPath ($PSScriptRoot+'/UI_BASELINE.json') -Raw | ConvertFrom-Json
$changed=@()
$hashes=@()
foreach($p in $base.files.PSObject.Properties){
  $after=(Get-FileHash -LiteralPath $p.Name -Algorithm SHA256).Hash.ToLower()
  $hashes+=@{path=$p.Name; before=$p.Value; after=$after}
  if($after -ne $p.Value){$changed+=$p.Name}
}
$added=@('control-plane/src/engineering-console.tsx','control-plane/src/engineering-console.css','control-plane/src/engineering-evidence.ts','control-plane/tests/engineering-console.test.tsx')
$unexpected=@($changed | Where-Object { $_.Replace('\','/') -ne 'control-plane/src/ui.tsx' })
$git='C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
$head=& $git rev-parse HEAD
& $git diff --check -- control-plane/src/ui.tsx control-plane/src/engineering-console.tsx control-plane/src/engineering-console.css control-plane/src/engineering-evidence.ts control-plane/tests/engineering-console.test.tsx
$diffExit=$LASTEXITCODE
$test=Get-Content -LiteralPath ($PSScriptRoot+'/UI_TEST_RESULTS_FINAL.json') -Raw | ConvertFrom-Json
$result=@{timestamp=(Get-Date -Format o); head=$head; changed_existing=$changed; unexpected_baseline_changes=$unexpected; added_source_test=@($added | ForEach-Object { @{path=$_; sha256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLower()} }); baseline_file_hashes=$hashes; git_diff_check_exit=$diffExit; tests=@{passed=$test.numPassedTests; failed=$test.numFailedTests; pending=$test.numPendingTests; total=$test.numTotalTests; exit_code=0}; typescript_exit_code=0; active_database_accessed=$false; runtime_operations=0; preservation_status='REVIEW_REQUIRED'; live_browser_validation='NOT_RUN'; frontend_build='NOT_RUN'; graph_cache_update='NOT_RUN_SCOPE_PRESERVATION'}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($PSScriptRoot+'/CHANGE_AUDIT.json') -Encoding utf8
$result | Select-Object head,changed_existing,unexpected_baseline_changes,tests,git_diff_check_exit | ConvertTo-Json -Depth 5
if($unexpected.Count -or $diffExit -ne 0){throw 'Scope audit requires review'}
