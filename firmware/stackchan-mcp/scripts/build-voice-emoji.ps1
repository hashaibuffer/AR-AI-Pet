[CmdletBinding()]
param(
    [string]$AgentLanguage = "zh"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$moduleRoot = Split-Path -Parent $PSScriptRoot
$lock = Get-Content -LiteralPath (Join-Path $moduleRoot "source.lock.json") -Raw -Encoding utf8 | ConvertFrom-Json
$checkout = Join-Path $moduleRoot "upstream"
$firmware = Join-Path $checkout "firmware"

function Stop-WithError {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments, [string]$Step)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "$Step failed with exit code $LASTEXITCODE."
    }
}

if (-not (Test-Path -LiteralPath $firmware -PathType Container)) {
    Stop-WithError "Pinned source is missing. Run scripts/bootstrap.ps1 first."
}

$actualCommit = (& git -C $checkout rev-parse HEAD | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne [string]$lock.sourceCommit) {
    Stop-WithError "Source commit does not match source.lock.json."
}

& (Join-Path $PSScriptRoot "apply-project-patches.ps1")
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "Project patch preparation failed."
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    Stop-WithError "python was not found in the ESP-IDF environment."
}

$idf = Get-Command idf.py -ErrorAction SilentlyContinue
if ($null -eq $idf) {
    Stop-WithError "idf.py was not found. Run this script from ESP-IDF v5.5.4 PowerShell."
}
# On Windows, idf.py may resolve to Espressif's idf-exe wrapper.  Use the
# active Python environment to query the actual script version; the wrapper's
# own version (for example v1.0.3) is not the ESP-IDF version.
$idfScript = Join-Path $env:IDF_PATH "tools/idf.py"
$idfVersion = (& $python.Source $idfScript --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $idfVersion -notmatch 'v5\.5\.4') {
    Stop-WithError "Expected ESP-IDF v5.5.4, got: $idfVersion"
}

Push-Location $firmware
try {
    Invoke-Checked $python.Source @(
        "./scripts/configure_stackchan.py",
        "--voice-mode", "xiaozhi-conversational",
        "--audio-profile", "wakenet",
        "--transport-profile", "xiaozhi-voice-only",
        "--language", "zh-cn",
        "--agent-language", $AgentLanguage
    ) "Voice-Emoji profile configuration"
    Invoke-Checked $python.Source @(
        "./scripts/release.py", "stackchan"
    ) "ESP-IDF release build"

    $reportDir = Join-Path $moduleRoot "artifacts/voice-emoji-consistency"
    Invoke-Checked $python.Source @(
        "./scripts/build_consistency_report.py",
        "--firmware-root", $firmware,
        "--output-dir", $reportDir
    ) "Consistency report"
}
finally {
    Pop-Location
}

Write-Host "ESP-IDF: $idfVersion"
Write-Host "source commit: $actualCommit"
Write-Host "profile: xiaozhi-conversational / wakenet / xiaozhi-voice-only / zh-cn / Agent $AgentLanguage"
Write-Host "OTA/activation: official flow enabled"
Write-Host "local demo tools: minimal voice set (scene/emotion/head/LED); common/base/diagnostic/peripheral disabled; separate action gateway: disabled; avatar overlay: disabled; built-in Emoji/LED/head/touch: enabled; pitch boot=30, operating range=10..40"
Write-Host "demo base control: physical ESP-NOW remote; fixed scenes do not emit base movement; Agent NanoDrive tools: disabled"
Write-Host "consistency report: $(Join-Path $moduleRoot 'artifacts/voice-emoji-consistency/latest.md')"
Write-Host "flash: not invoked"
