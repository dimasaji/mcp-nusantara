Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$mutexType = [Threading.Mutex]
$rightsType = [System.Security.AccessControl.MutexRights]
$rightsMethod = $null
$minimalMethod = $null
foreach ($candidate in $mutexType.GetMethods([Reflection.BindingFlags]'Public,Static')) {
    if ($candidate.Name -ne 'OpenExisting') { continue }
    $parameters = $candidate.GetParameters()
    if ($parameters.Count -eq 2 -and $parameters[0].ParameterType -eq [string] -and $parameters[1].ParameterType -eq $rightsType) { $rightsMethod = $candidate }
    if ($parameters.Count -eq 1 -and $parameters[0].ParameterType -eq [string]) { $minimalMethod = $candidate }
}
if ($null -eq $rightsMethod -and $null -eq $minimalMethod) { throw 'No minimal-rights overload found.' }
$name = 'Global\NUSANTARA-OVERLOAD-PROBE-' + [guid]::NewGuid().ToString('N')
$created = New-Object Threading.Mutex($false, $name)
$opened = $null
try {
    if ($null -ne $rightsMethod) {
        $rights = [System.Security.AccessControl.MutexRights]::Synchronize -bor [System.Security.AccessControl.MutexRights]::Modify
        $opened = $rightsMethod.Invoke($null, [object[]]@($name, $rights))
        $selected = 'OpenExisting(string, MutexRights)'
    } else {
        $opened = $minimalMethod.Invoke($null, [object[]]@($name))
        $selected = 'OpenExisting(string)'
    }
    if (-not $opened.WaitOne(1000)) { throw 'Could not acquire the test mutex.' }
    $opened.ReleaseMutex()
    [pscustomobject]@{runtime=$PSVersionTable.PSVersion.ToString();selectedOverload=$selected;acquireRelease='PASS'}
} finally {
    if ($opened) { $opened.Dispose() }
    if ($created) { $created.Dispose() }
}
