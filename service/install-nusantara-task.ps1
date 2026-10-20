param([switch]$Uninstall, [switch]$PlanOnly, [System.Management.Automation.PSCredential]$Credential)
try {
    if (-not $PlanOnly -and -not $Uninstall) {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = [Security.Principal.WindowsPrincipal]::new($identity)
        if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
            throw 'Administrator required for the Windows boot trigger. Run this installer from PowerShell Administrator; no UAC bypass is attempted.'
        }
    }
    & "$PSScriptRoot/task-registration.ps1" -Uninstall:$Uninstall -PlanOnly:$PlanOnly -Credential $Credential
} catch {
    $config = Get-Content "$PSScriptRoot/../config/local-services.json" -Raw | ConvertFrom-Json
    $stateDirectory = "$PSScriptRoot/../data/service-v1"
    if (-not $PlanOnly -and -not $Uninstall -and (Test-Path $stateDirectory) -and -not (Get-ScheduledTask -TaskName $config.taskName -ErrorAction SilentlyContinue)) {
        'disabled' | Set-Content (Join-Path $stateDirectory 'monitor-state')
    }
    Write-Error -Message $_.Exception.Message -ErrorAction Continue
    exit 1
}
