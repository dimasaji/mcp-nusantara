[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

if (-not [string]::IsNullOrEmpty($env:NUSANTARA_ADMIN_TOKEN)) {
    throw 'NUSANTARA_ADMIN_TOKEN is already set in this PowerShell session. Refusing to replace it.'
}

$random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$bytes = New-Object byte[] 32
try {
    $random.GetBytes($bytes)
    $token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
} finally {
    $random.Dispose()
    [Array]::Clear($bytes, 0, $bytes.Length)
}

$env:NUSANTARA_ADMIN_TOKEN = $token
Write-Output $token
