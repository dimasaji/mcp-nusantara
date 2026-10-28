# Isolated lifecycle tests: every OS/process operation below is a fixture.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../service/local-services.ps1"
$script:StateDirectory = Join-Path $script:Repository ('artifacts/NCP-V1-AUTOSTART-001/test-' + [Guid]::NewGuid().ToString('N'))
Initialize-LocalState
$script:Processes = @()
$script:Listeners = @()
$script:Started = @()
$script:Stopped = @()
function Get-CimInstance { param($ClassName) return $script:Processes }
function Get-NetTCPConnection { param($State,$ErrorAction) return $script:Listeners }
function Test-Http { param($Uri) return $true }
function Get-RuntimePaths { [pscustomobject]@{python='fixture-python';node='fixture-node'} }
function Start-Process {
    param($FilePath,$ArgumentList,$WorkingDirectory,$WindowStyle,$RedirectStandardOutput,$RedirectStandardError)
    $script:Started += [pscustomobject]@{binary=$FilePath;arguments=$ArgumentList;directory=$WorkingDirectory}
}
function Stop-Process { param($Id,$ErrorAction) $script:Stopped += $Id }
function Assert-That($Condition,[string]$Message) { if (-not $Condition) { throw $Message }; Write-Output "PASS: $Message" }
$owned = [pscustomobject]@{Name='python.exe';ProcessId=101;CreationDate='fixture';CommandLine="`"$script:Repository\.venv\Scripts\python.exe`" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"}
$foreign = [pscustomobject]@{Name='python.exe';ProcessId=102;CreationDate='fixture';CommandLine='C:\other\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000'}
$script:Processes = @($owned,$foreign)
Assert-That (@(Get-ServiceProcesses backend).Count -eq 1) 'Ownership rejects another repository'
$script:Listeners = @([pscustomobject]@{LocalPort=8000;LocalAddress='127.0.0.1';OwningProcess=102})
$status = Get-LocalStatus
Assert-That ($status.services[0].status -eq 'HOLD') 'Foreign listener cannot pass health'
Start-LocalService backend
Assert-That ($script:Started.Count -eq 0) 'Occupied port never launches duplicate'
$script:Listeners = @()
Start-LocalService backend
Assert-That ($script:Started.Count -eq 0) 'Initializing owned process never launches duplicate'
$blocked = $false
try { Stop-LocalServices } catch { $blocked = $true }
Assert-That ($blocked -and $script:Stopped.Count -eq 0) 'Stop requires explicit permission'
Stop-LocalServices -AllowStop
Assert-That ($script:Stopped.Count -eq 1 -and $script:Stopped[0] -eq 101) 'Stop targets verified repository process only'
$script:Processes = @()
1..4 | ForEach-Object { Start-LocalService backend }
Assert-That ($script:Started.Count -eq 3) 'Recovery limited to three starts per window'
Assert-That ($script:Started[0].arguments -match '--host 127.0.0.1 --port 8000') 'Backend launch uses contract binding'
Start-LocalService frontend
Assert-That ($script:Started[-1].arguments -match '--port 5180 --strictPort') 'Frontend launch fixes port and refuses fallback'
Assert-That ($script:Started[-1].directory -like '*control-plane') 'Frontend directory spelling is correct'
Assert-That ($script:Stopped.Count -eq 1) 'Recovery never kills any process'
# Exercise actual task-registration orchestration in a disposable repository.
$fixtureRoot = Join-Path $script:StateDirectory 'registration-fixture'
New-Item -ItemType Directory -Path "$fixtureRoot/service","$fixtureRoot/config","$fixtureRoot/data/service-v1" -Force | Out-Null
Copy-Item "$PSScriptRoot/../service/local-services.ps1","$PSScriptRoot/../service/task-registration.ps1" "$fixtureRoot/service/"
Copy-Item "$PSScriptRoot/../config/local-services.json" "$fixtureRoot/config/"
$dummy = Join-Path $fixtureRoot 'dummy.exe'
'' | Set-Content $dummy
@{python=$dummy;node=$dummy} | ConvertTo-Json | Set-Content "$fixtureRoot/data/service-v1/runtime.json"
function Get-ScheduledTask {
    param($TaskName,$ErrorAction)
    if (-not $TaskName) { [pscustomobject]@{TaskName='Windows COM fixture';State='Ready';Actions=@([pscustomobject]@{ClassId='fixture'})} }
}
function New-ScheduledTaskAction {
    param($Execute,$Argument,$WorkingDirectory)
    $taskProbe['arguments'] = $Argument
    [pscustomobject]@{Execute=$Execute;Arguments=$Argument}
}
function New-ScheduledTaskTrigger { param([switch]$AtStartup) [pscustomobject]@{Delay=''} }
$taskProbe = @{}
function New-ScheduledTaskPrincipal {
    param($UserId,$LogonType,$RunLevel)
    $taskProbe['principal'] = [pscustomobject]@{UserId=$UserId;LogonType=$LogonType;RunLevel=$RunLevel}
    $taskProbe['principal']
}
function New-ScheduledTaskSettingsSet { param([switch]$StartWhenAvailable,[switch]$AllowStartIfOnBatteries,[switch]$DontStopIfGoingOnBatteries,$RestartCount,$RestartInterval,$ExecutionTimeLimit,$MultipleInstances) 'fixture-settings' }
function New-ScheduledTask { param($Action,$Trigger,$Principal,$Settings,$Description) 'fixture-task' }
function Export-ScheduledTask { param($InputObject) '<Task />' }
function Register-ScheduledTask {
    param($TaskName,$InputObject,$User,$Password,$ErrorAction)
    $taskProbe['credentialPassed'] = $User -eq 'fixture\user' -and $Password -eq 'fixture-only-not-a-real-password'
    throw 'fixture access denied'
}
function Start-ScheduledTask { param($TaskName,$ErrorAction) throw 'must never start after denied registration' }
$denied = $false
try { & "$fixtureRoot/service/task-registration.ps1" } catch { $denied = $_.Exception.Message -eq 'fixture access denied' }
Assert-That $denied 'Registration denial is propagated without attempting task start'
Assert-That (-not (Test-Path "$fixtureRoot/data/service-v1/monitor-state")) 'Failed registration never enables monitoring'
Assert-That ($taskProbe['principal'].LogonType -eq 'S4U' -and $taskProbe['principal'].RunLevel -eq 'Limited') 'Boot task plans least-privilege noninteractive user logon'
$fixtureCredential = [System.Management.Automation.PSCredential]::new('fixture\user', (ConvertTo-SecureString 'fixture-only-not-a-real-password' -AsPlainText -Force))
try { & "$fixtureRoot/service/task-registration.ps1" -Credential $fixtureCredential } catch {
    if ($_.Exception.Message -ne 'fixture access denied') { throw }
}
Assert-That ($taskProbe['principal'].LogonType -eq 'Password' -and $taskProbe['principal'].RunLevel -eq 'Limited' -and $taskProbe['credentialPassed']) 'Explicit credential mode preserves Limited rights and passes credentials only to scheduler'
Assert-That (-not ((Get-Content "$fixtureRoot/data/service-v1/autostart-plan.xml" -Raw).Contains('fixture-only-not-a-real-password'))) 'Task evidence never contains supplied password'
Assert-That ($taskProbe['arguments'] -match '-NonInteractive.*-WindowStyle Hidden' -and $taskProbe['arguments'] -notmatch 'Credential|Password|Authorization|OPENROUTER|api[_-]?key|fixture-only') 'Stored task arguments contain no credentials or API keys'
Write-Output 'ALL LIFECYCLE CONTRACT TESTS PASS'
