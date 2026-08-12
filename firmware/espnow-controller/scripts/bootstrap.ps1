[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$moduleRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $moduleRoot)
$lock = Get-Content -LiteralPath (Join-Path $moduleRoot 'source.lock.json') -Raw -Encoding utf8 | ConvertFrom-Json
$checkout = Join-Path $repoRoot 'firmware/stackchan/upstream'

if (Test-Path -LiteralPath $checkout) {
    if (-not (Test-Path -LiteralPath (Join-Path $checkout '.git'))) {
        throw "Existing path is not a Git checkout: $checkout"
    }
    $changes = (& git -C $checkout status --porcelain | Out-String).Trim()
    if ($changes) {
        throw 'StackChan upstream has local changes. Nothing was overwritten.'
    }
} else {
    git clone $lock.sourceRepository $checkout
    if ($LASTEXITCODE -ne 0) { throw 'Unable to clone the StackChan source.' }
}

git -C $checkout fetch origin $lock.sourceCommit
if ($LASTEXITCODE -ne 0) { throw 'Unable to fetch the pinned source commit.' }
git -C $checkout checkout --detach $lock.sourceCommit
if ($LASTEXITCODE -ne 0) { throw 'Unable to check out the pinned source commit.' }

Write-Host "StackChan remote source ready: $($lock.sourceCommit)"
