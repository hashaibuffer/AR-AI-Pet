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
    (Join-Path $moduleRoot "patches/0007-nanodrive-v09-ble-protocol.patch"),
    (Join-Path $moduleRoot "patches/0008-voice-emoji-profile.patch"),
    (Join-Path $moduleRoot "patches/0009-scene-emoji-tool.patch"),
    (Join-Path $moduleRoot "patches/0010-scene-playback.patch"),
    (Join-Path $moduleRoot "patches/0011-xiaozhi-action-emoji-profile.patch"),
    (Join-Path $moduleRoot "patches/0012-action-profile-configure.patch"),
    (Join-Path $moduleRoot "patches/0013-longer-scene-timelines.patch"),
    (Join-Path $moduleRoot "patches/0014-richer-scene-timelines.patch"),
    (Join-Path $moduleRoot "patches/0015-demo-direction-and-base-calibration.patch"),
    (Join-Path $moduleRoot "patches/0016-lite-voice-tools-memory.patch"),
    (Join-Path $moduleRoot "patches/0017-boot-reliability-and-deferred-transports.patch"),
    (Join-Path $moduleRoot "patches/0018-sram-budget-and-lazy-ble.patch"),
    (Join-Path $moduleRoot "patches/0019-head-pitch-operating-window.patch"),
    (Join-Path $moduleRoot "patches/0020-bounded-ble-reconnect.patch"),
    (Join-Path $moduleRoot "patches/0021-ble-psram-single-link-profile.patch"),
    (Join-Path $moduleRoot "patches/0022-scenes-no-base-actions.patch")
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
            $scanner = Join-Path $checkout "firmware/main/boards/stackchan/nanodrive_ble_scanner.cc"
            $header = Join-Path $checkout "firmware/main/boards/stackchan/nanodrive_ble_scanner.h"
            return ((Test-Path -LiteralPath $scanner -PathType Leaf) -and
                    (Test-Path -LiteralPath $header -PathType Leaf) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch '#include "nanodrive_ble_scanner.h"' -Quiet))
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
        "0008-voice-emoji-profile.patch" {
            $kconfig = Join-Path $checkout "firmware/main/Kconfig.projbuild"
            $config = Join-Path $checkout "firmware/configs/transport/xiaozhi-voice-only.defaults"
            $script = Join-Path $checkout "firmware/scripts/configure_stackchan.py"
            $report = Join-Path $checkout "firmware/scripts/build_consistency_report.py"
            return ((Test-Path -LiteralPath $config -PathType Leaf) -and
                    (Select-String -LiteralPath $kconfig -SimpleMatch "config STACKCHAN_AVATAR_OVERLAY" -Quiet) -and
                    (Select-String -LiteralPath $script -SimpleMatch '"xiaozhi-voice-only"' -Quiet) -and
                    (Select-String -LiteralPath $report -SimpleMatch "optional action gateway may be empty" -Quiet))
        }
        "0009-scene-emoji-tool.patch" {
            return (Select-String -LiteralPath $stackchan -SimpleMatch '"self.display.set_emotion"' -Quiet)
        }
        "0010-scene-playback.patch" {
            return ((Select-String -LiteralPath $stackchan -SimpleMatch '"self.scene.play"' -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "SceneTaskLoop()" -Quiet))
        }
        "0011-xiaozhi-action-emoji-profile.patch" {
            $config = Join-Path $checkout "firmware/configs/transport/xiaozhi-action-emoji.defaults"
            return ((Test-Path -LiteralPath $config -PathType Leaf) -and
                    (Select-String -LiteralPath $config -SimpleMatch "CONFIG_STACKCHAN_ACTION_GATEWAY=y" -Quiet) -and
                    (Select-String -LiteralPath $config -SimpleMatch "CONFIG_STACKCHAN_AVATAR_OVERLAY is not set" -Quiet))
        }
        "0012-action-profile-configure.patch" {
            $script = Join-Path $checkout "firmware/scripts/configure_stackchan.py"
            return (Select-String -LiteralPath $script -SimpleMatch '"xiaozhi-action-emoji"' -Quiet)
        }
        "0013-longer-scene-timelines.patch" {
            return (Select-String -LiteralPath $stackchan -SimpleMatch 'color_cycle_fast(8000)' -Quiet)
        }
        "0014-richer-scene-timelines.patch" {
            return ((Select-String -LiteralPath $stackchan -SimpleMatch 'emotion(1900, "surprised")' -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch 'std::stable_sort(steps.begin()' -Quiet))
        }
        "0015-demo-direction-and-base-calibration.patch" {
            return ((Select-String -LiteralPath $stackchan -SimpleMatch 'self.robot.head_pose' -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch 'CONFIG_STACKCHAN_AGENT_BASE_TOOLS' -Quiet))
        }
        "0016-lite-voice-tools-memory.patch" {
            return ((Select-String -LiteralPath $stackchan -SimpleMatch 'CONFIG_STACKCHAN_AGENT_DIAGNOSTIC_TOOLS' -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch 'CONFIG_STACKCHAN_AGENT_PERIPHERAL_TOOLS' -Quiet))
        }
        "0017-boot-reliability-and-deferred-transports.patch" {
            $wifi = Join-Path $checkout "firmware/main/boards/common/wifi_board.cc"
            $application = Join-Path $checkout "firmware/main/application.cc"
            return ((Select-String -LiteralPath $wifi -SimpleMatch "saved credentials; retrying station (not config mode)" -Quiet) -and
                    (Select-String -LiteralPath $application -SimpleMatch "board.OnApplicationReady();" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "companion_transports_started_" -Quiet))
        }
        "0018-sram-budget-and-lazy-ble.patch" {
            $mcp = Join-Path $checkout "firmware/main/mcp_server.cc"
            $scanner = Join-Path $checkout "firmware/main/boards/stackchan/nanodrive_ble_scanner.cc"
            $systemInfo = Join-Path $checkout "firmware/main/system_info.cc"
            return ((Select-String -LiteralPath $mcp -SimpleMatch "CONFIG_STACKCHAN_AGENT_MINIMAL_TOOLS" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "lazy-started on base use" -Quiet) -and
                    (Select-String -LiteralPath $scanner -SimpleMatch "BLE_SCAN_DUPLICATE_ENABLE" -Quiet) -and
                    (Select-String -LiteralPath $systemInfo -SimpleMatch "largest psram" -Quiet))
        }
        "0019-head-pitch-operating-window.patch" {
            return ((Select-String -LiteralPath $stackchan -SimpleMatch "BOOT_INIT_PITCH_DEG = 30" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "CONTROLLER_HEAD_PITCH_MIN_DEG = 10" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "CONTROLLER_HEAD_PITCH_MAX_DEG = 40" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "SAFE_PITCH_MIN = 10" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "SAFE_PITCH_MAX = 40" -Quiet))
        }
        "0020-bounded-ble-reconnect.patch" {
            $scanner = Join-Path $checkout "firmware/main/boards/stackchan/nanodrive_ble_scanner.cc"
            return ((Select-String -LiteralPath $scanner -SimpleMatch "kMaxScanCyclesPerRequest = 2" -Quiet) -and
                    (Select-String -LiteralPath $scanner -SimpleMatch "scanning paused until the next BASE-mode entry" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "transport.RequestScan();" -Quiet))
        }
        "0021-ble-psram-single-link-profile.patch" {
            $config = Join-Path $checkout "firmware/main/boards/stackchan/config.json"
            return ((Select-String -LiteralPath $config -SimpleMatch '"CONFIG_BT_ALLOCATION_FROM_SPIRAM_FIRST=y"' -Quiet) -and
                    (Select-String -LiteralPath $config -SimpleMatch '"CONFIG_BT_ACL_CONNECTIONS=1"' -Quiet) -and
                    (Select-String -LiteralPath $config -SimpleMatch '"# CONFIG_BT_BLE_SMP_ENABLE is not set"' -Quiet))
        }
        "0022-scenes-no-base-actions.patch" {
            return ((Select-String -LiteralPath $stackchan -SimpleMatch "enum class SceneStepKind : uint8_t { EMOTION, LED, HEAD };" -Quiet) -and
                    (Select-String -LiteralPath $stackchan -SimpleMatch "Base movement is controlled only by the physical remote." -Quiet) -and
                    -not (Select-String -LiteralPath $stackchan -SimpleMatch "SceneStepKind::BASE_MOVE" -Quiet))
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
    "firmware/main/boards/common/board.h",
    "firmware/main/boards/common/wifi_board.cc",
    "firmware/main/main.cc",
    "gateway/stackchan_mcp/stdio_server.py",
    "firmware/configs/transport/xiaozhi-voice-only.defaults",
    "firmware/configs/transport/xiaozhi-plus-action.defaults",
    "firmware/configs/transport/xiaozhi-action-emoji.defaults",
    "firmware/configs/transport/local-mcp.defaults",
    "firmware/main/Kconfig.projbuild",
    "firmware/main/application.cc",
    "firmware/main/mcp_server.cc",
    "firmware/main/system_info.cc",
    "firmware/main/audio/wake_words/afe_wake_word.cc",
    "firmware/scripts/configure_stackchan.py",
    "firmware/scripts/build_consistency_report.py"
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
