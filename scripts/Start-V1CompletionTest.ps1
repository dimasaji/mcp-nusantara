param([switch]$Restart)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$run=Join-Path $root 'artifacts/nusantara-e2e-20261016-1018'
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
if($Restart){
 $listener=Get-NetTCPConnection -State Listen -LocalPort 8766 -ErrorAction SilentlyContinue
 if($listener){
  $owned=Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
  if($owned.CommandLine -notlike '*serve_v1_completion_isolated.py*'){throw 'Port 8766 is not owned by this test launcher.'}
  Stop-Process -Id $listener.OwningProcess
  Wait-Process -Id $listener.OwningProcess -Timeout 10 -ErrorAction SilentlyContinue
 }
}
if ($Restart -or -not (Get-NetTCPConnection -State Listen -LocalPort 8766 -ErrorAction SilentlyContinue)) {
 Start-Process -FilePath "$root/.venv/Scripts/python.exe" -ArgumentList @('scripts/serve_v1_completion_isolated.py') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput "$run/isolated-backend-$stamp.stdout.log" -RedirectStandardError "$run/isolated-backend-$stamp.stderr.log"
}
if (-not (Get-NetTCPConnection -State Listen -LocalPort 5180 -ErrorAction SilentlyContinue)) {
 $env:NUSANTARA_BACKEND_URL='http://127.0.0.1:8766'
 Start-Process -FilePath 'C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' -ArgumentList @('node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5180') -WorkingDirectory "$root/control-plane" -WindowStyle Hidden -RedirectStandardOutput "$run/isolated-frontend.stdout.log" -RedirectStandardError "$run/isolated-frontend.stderr.log"
}
