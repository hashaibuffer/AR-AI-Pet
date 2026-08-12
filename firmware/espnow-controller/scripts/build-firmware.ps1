[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$moduleRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $moduleRoot)
$project = Join-Path $repoRoot 'firmware/stackchan/upstream/remote/code'

& (Join-Path $PSScriptRoot 'test-host.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Host tests failed.' }
& (Join-Path $PSScriptRoot 'apply-project-patch.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Project patch failed.' }

if (-not (Get-Command idf.py -ErrorAction SilentlyContinue)) {
    throw 'idf.py is unavailable. Open ESP-IDF PowerShell, then run this script again.'
}
Push-Location $project
try {
    idf.py build
    if ($LASTEXITCODE -ne 0) { throw 'ESP-IDF firmware build failed.' }
} finally {
    Pop-Location
}
