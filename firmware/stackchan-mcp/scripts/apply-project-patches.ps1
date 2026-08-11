[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$moduleRoot = Split-Path -Parent $PSScriptRoot
$checkout = Join-Path $moduleRoot "upstream"
$lockPath = Join-Path $moduleRoot "source.lock.json"
$patchPath = Join-Path $moduleRoot "patches/0001-nanodrive-tx-only.patch"

function Stop-WithError {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $patchPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath (Join-Path $checkout ".git"))) {
    Stop-WithError "Locked source or project patch is missing. Run scripts/bootstrap.ps1 first."
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
$actualCommit = (& git -C $checkout rev-parse HEAD | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne [string]$lock.sourceCommit) {
    Stop-WithError "Source commit does not match source.lock.json."
}

$savedErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& git -C $checkout apply --unidiff-zero --reverse --check $patchPath 2>$null
$reverseCheckExitCode = $LASTEXITCODE
$ErrorActionPreference = $savedErrorActionPreference
if ($reverseCheckExitCode -eq 0) {
    Write-Host "project patch: already applied"
    exit 0
}

$dirty = (& git -C $checkout status --porcelain --untracked-files=no | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "Unable to inspect the pinned source checkout."
}
if ($dirty) {
    Stop-WithError "Pinned source has tracked changes other than the project patch; nothing was overwritten."
}

& git -C $checkout apply --unidiff-zero --check $patchPath
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "Project patch does not apply cleanly to the locked source."
}
& git -C $checkout apply --unidiff-zero $patchPath
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "Project patch application failed."
}

Write-Host "project patch: applied"
