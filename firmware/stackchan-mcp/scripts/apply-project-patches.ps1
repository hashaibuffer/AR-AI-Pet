[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$moduleRoot = Split-Path -Parent $PSScriptRoot
$checkout = Join-Path $moduleRoot "upstream"
$lockPath = Join-Path $moduleRoot "source.lock.json"
$patchPaths = @(
    (Join-Path $moduleRoot "patches/0001-nanodrive-tx-only.patch"),
    (Join-Path $moduleRoot "patches/0002-nanodrive-gateway-tools.patch")
)

function Stop-WithError {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf) -or
    @($patchPaths | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) }).Count -gt 0 -or
    -not (Test-Path -LiteralPath (Join-Path $checkout ".git"))) {
    Stop-WithError "Locked source or project patch is missing. Run scripts/bootstrap.ps1 first."
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
$actualCommit = (& git -C $checkout rev-parse HEAD | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne [string]$lock.sourceCommit) {
    Stop-WithError "Source commit does not match source.lock.json."
}

$dirty = (& git -C $checkout status --porcelain --untracked-files=no | Out-String).TrimEnd()
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "Unable to inspect the pinned source checkout."
}
$allowedPaths = @(
    "firmware/main/boards/stackchan/stackchan.cc",
    "gateway/stackchan_mcp/stdio_server.py"
)
if ($dirty) {
    $unexpected = @(
        $dirty -split "`r?`n" |
        Where-Object { $_ -and ($allowedPaths -notcontains $_.Substring(3)) }
    )
    if ($unexpected.Count -gt 0) {
        Stop-WithError "Pinned source has tracked changes other than the project patches; nothing was overwritten."
    }
}

$appliedAny = $false
foreach ($patchPath in $patchPaths) {
    $savedErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & git -C $checkout apply --unidiff-zero --reverse --check $patchPath 2>$null
    $reverseCheckExitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedErrorActionPreference
    if ($reverseCheckExitCode -eq 0) {
        Write-Host "project patch: already applied $(Split-Path -Leaf $patchPath)"
        continue
    }

    & git -C $checkout apply --unidiff-zero --check $patchPath
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "Project patch does not apply cleanly: $(Split-Path -Leaf $patchPath)."
    }
    & git -C $checkout apply --unidiff-zero $patchPath
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "Project patch application failed: $(Split-Path -Leaf $patchPath)."
    }
    $appliedAny = $true
    Write-Host "project patch: applied $(Split-Path -Leaf $patchPath)"
}

if (-not $appliedAny) {
    Write-Host "project patches: already applied"
}
