[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ActionGatewayUrl = $env:STACKCHAN_ACTION_GATEWAY_URL,
    [Parameter(Mandatory = $false)]
    [string]$ActionGatewayToken = $env:STACKCHAN_ACTION_GATEWAY_TOKEN,
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

if ([string]::IsNullOrWhiteSpace($ActionGatewayUrl)) {
    Stop-WithError "Set STACKCHAN_ACTION_GATEWAY_URL or pass -ActionGatewayUrl, for example ws://192.168.50.10:8765."
}
if ($null -eq $ActionGatewayToken) {
    $ActionGatewayToken = ""
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
        "--transport-profile", "xiaozhi-action-emoji",
        "--language", "zh-cn",
        "--agent-language", $AgentLanguage,
        "--local-gateway-url", $ActionGatewayUrl,
        "--local-gateway-token", $ActionGatewayToken
    ) "Xiaozhi plus independent action gateway profile configuration"
    Invoke-Checked $python.Source @(
        "./scripts/release.py", "stackchan"
    ) "ESP-IDF release build"
    $reportDir = Join-Path $moduleRoot "artifacts/action-gateway-consistency"
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
Write-Host "profile: xiaozhi-conversational / wakenet / xiaozhi-action-emoji / zh-cn / Agent $AgentLanguage"
Write-Host "primary voice: official Xiaozhi OTA/NVS"
Write-Host "action gateway: $ActionGatewayUrl"
Write-Host "local Emoji/actions: enabled; Avatar overlay: disabled"
Write-Host "consistency report: $(Join-Path $moduleRoot 'artifacts/action-gateway-consistency/latest.md')"
Write-Host "flash: not invoked"
