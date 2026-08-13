[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$moduleRoot = Split-Path -Parent $PSScriptRoot
$checkout = Join-Path $moduleRoot "upstream"
$lockPath = Join-Path $moduleRoot "source.lock.json"
$patchPaths = @(
    (Join-Path $moduleRoot "patches/0001-nanodrive-tx-only.patch"),
    (Join-Path $moduleRoot "patches/0002-nanodrive-gateway-tools.patch"),
    (Join-Path $moduleRoot "patches/0003-espnow-controller-receiver.patch"),
    (Join-Path $moduleRoot "patches/0004-nanodrive-ble-scanner.patch"),
    (Join-Path $moduleRoot "patches/0005-nanodrive-ble-runtime.patch"),
    (Join-Path $moduleRoot "patches/0006-nanodrive-ble-rate-limit.patch"),
    (Join-Path $moduleRoot "patches/0007-nanodrive-v09-ble-protocol.patch")
)

function Stop-WithError {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

function Test-PatchMarker {
    param([string]$PatchName)

    $stackchan = Join-Path $checkout "firmware/main/boards/stackchan/stackchan.cc"
    $mainCmake = Join-Path $checkout "firmware/main/CMakeLists.txt"
    $gateway = Join-Path $checkout "gateway/stackchan_mcp/stdio_server.py"
    switch ($PatchName) {
        "0001-nanodrive-tx-only.patch" {
            return (Select-String -LiteralPath $stackchan -SimpleMatch "static constexpr gpio_num_t NANODRIVE_TX_PIN" -Quiet)
        }
        "0002-nanodrive-gateway-tools.patch" {
            return (Select-String -LiteralPath $gateway -SimpleMatch '"self.robot.base_drive"' -Quiet)
        }
        "0003-espnow-controller-receiver.patch" {
            return ((Select-String -LiteralPath $stackchan -SimpleMatch "InitializeEspNowController();" -Quiet) -and
                    (Select-String -LiteralPath $mainCmake -SimpleMatch "AR_CONTROLLER_CORE_DIR" -Quiet))
        }
        "0004-nanodrive-ble-scanner.patch" {
            return (Select-String -LiteralPath $stackchan -SimpleMatch "NanoDriveBleScanner::GetInstance().Start();" -Quiet)
        }
        "0005-nanodrive-ble-runtime.patch" {
            $scanner = Join-Path $checkout "firmware/main/boards/stackchan/nanodrive_ble_scanner.cc"
            return (Select-String -LiteralPath $scanner -SimpleMatch "bool NanoDriveBleScanner::SendCommand" -Quiet)
        }
        "0006-nanodrive-ble-rate-limit.patch" {
            return ((Select-String -LiteralPath $stackchan -SimpleMatch "controller_last_base_command_" -Quiet) -or
                    (Select-String -LiteralPath $stackchan -SimpleMatch "controller_last_base_left_" -Quiet))
        }
        "0007-nanodrive-v09-ble-protocol.patch" {
            $scanner = Join-Path $checkout "firmware/main/boards/stackchan/nanodrive_ble_scanner.cc"
            return ((Select-String -LiteralPath $scanner -SimpleMatch "bool NanoDriveBleScanner::IsMotionEnabled" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "controller_last_base_left_" -Quiet))
        }
        default { return $false }
    }
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
    "firmware/main/CMakeLists.txt",
    "firmware/main/boards/stackchan/config.json",
    "firmware/main/boards/stackchan/nanodrive_ble_scanner.cc",
    "firmware/main/boards/stackchan/nanodrive_ble_scanner.h",
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
    $patchName = Split-Path -Leaf $patchPath

    # A later project patch can legitimately change lines introduced by an
    # earlier patch, so reverse --check is not a reliable "already applied"
    # test.  Check the patch-specific marker first and never re-apply a patch
    # to a dirty pinned checkout.
    if (Test-PatchMarker $patchName) {
        Write-Host "project patch: marker confirms already applied $patchName"
        continue
    }

    $savedErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & git -C $checkout apply --recount --unidiff-zero --reverse --check $patchPath 2>$null
    $reverseCheckExitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedErrorActionPreference
    if ($reverseCheckExitCode -eq 0) {
        Write-Host "project patch: already applied $patchName"
        continue
    }

    & git -C $checkout apply --recount --unidiff-zero --check $patchPath
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "Project patch does not apply cleanly: $patchName."
    }
    & git -C $checkout apply --recount --unidiff-zero $patchPath
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "Project patch application failed: $(Split-Path -Leaf $patchPath)."
    }
    $appliedAny = $true
    Write-Host "project patch: applied $patchName"
}

if (-not $appliedAny) {
    Write-Host "project patches: already applied"
}

exit 0
