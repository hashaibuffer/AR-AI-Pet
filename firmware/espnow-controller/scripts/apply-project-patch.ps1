[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$moduleRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $moduleRoot)
$checkout = Join-Path $repoRoot 'firmware/stackchan/upstream'
$patch = Join-Path $moduleRoot 'patches/0001-controller-modes-and-protocol.patch'
$lock = Get-Content -LiteralPath (Join-Path $moduleRoot 'source.lock.json') -Raw -Encoding utf8 | ConvertFrom-Json

if (-not (Test-Path -LiteralPath (Join-Path $checkout '.git'))) {
    throw 'Pinned StackChan source is missing. Run bootstrap.ps1 first.'
}
$actual = (& git -C $checkout rev-parse HEAD | Out-String).Trim()
if ($actual -ne $lock.sourceCommit) { throw "Source mismatch: $actual" }

$oldPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
git -C $checkout apply --reverse --check $patch 2>$null
$alreadyApplied = $LASTEXITCODE -eq 0
$ErrorActionPreference = $oldPreference

if ($alreadyApplied) {
    Write-Host 'Controller patch already applied.'
    exit 0
}

git -C $checkout apply --check $patch
if ($LASTEXITCODE -ne 0) { throw 'Controller patch does not apply cleanly.' }
git -C $checkout apply $patch
if ($LASTEXITCODE -ne 0) { throw 'Controller patch application failed.' }
Write-Host 'Controller patch applied.'
