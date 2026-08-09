[CmdletBinding()]
param(
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$moduleRoot = Split-Path -Parent $PSScriptRoot
$lockPath = Join-Path $moduleRoot "source.lock.json"
$checkout = Join-Path $moduleRoot "upstream"

function Stop-WithError {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

function Invoke-Checked {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [string]$Step,
        [string]$WorkingDirectory = ""
    )

    if ($WorkingDirectory) {
        Push-Location $WorkingDirectory
    }
    try {
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) {
            Stop-WithError "$Step failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        if ($WorkingDirectory) {
            Pop-Location
        }
    }
}

if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
    Stop-WithError "Source lock not found: $lockPath"
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
$expectedCommit = [string]$lock.sourceCommit
$sourceRepository = [string]$lock.sourceRepository

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Stop-WithError "git was not found on PATH."
}

if (Test-Path -LiteralPath $checkout) {
    if (-not (Test-Path -LiteralPath (Join-Path $checkout ".git"))) {
        Stop-WithError "Existing upstream path is not a Git checkout: $checkout"
    }
    $dirty = (& git -C $checkout status --porcelain | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "Unable to inspect the existing source checkout."
    }
    if ($dirty) {
        Stop-WithError "Source checkout has local changes. Preserve or remove them before bootstrap; nothing was overwritten."
    }
}
else {
    Invoke-Checked "git" @(
        "clone", "--filter=blob:none", "--no-checkout",
        $sourceRepository, $checkout
    ) "Source clone"
}

Invoke-Checked "git" @("-C", $checkout, "fetch", "origin", $expectedCommit) "Pinned commit fetch"
Invoke-Checked "git" @("-C", $checkout, "checkout", "--detach", $expectedCommit) "Pinned commit checkout"

$actualCommit = (& git -C $checkout rev-parse HEAD | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $expectedCommit) {
    Stop-WithError "Source identity mismatch. Expected $expectedCommit, got $actualCommit."
}

if (-not $SkipTests) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        Stop-WithError "python was not found on PATH."
    }
    Invoke-Checked $python.Source @(
        "-m", "unittest", "discover", "-s", "firmware/scripts",
        "-p", "test_*.py", "-v"
    ) "Firmware Python tests" $checkout

    $cmake = Get-Command cmake -ErrorAction SilentlyContinue
    $ctest = Get-Command ctest -ErrorAction SilentlyContinue
    if ($null -eq $cmake -or $null -eq $ctest) {
        Stop-WithError "cmake and ctest are required for host tests."
    }
    $hostBuild = Join-Path $checkout "firmware/host_test/build-repro"
    Invoke-Checked $cmake.Source @(
        "-S", "firmware/host_test", "-B", $hostBuild,
        "-DCMAKE_BUILD_TYPE=Release"
    ) "Host-test configure" $checkout
    Invoke-Checked $cmake.Source @("--build", $hostBuild, "--config", "Release") "Host-test build" $checkout
    Invoke-Checked $ctest.Source @(
        "--test-dir", $hostBuild, "-C", "Release", "--output-on-failure"
    ) "Host tests" $checkout
}

Write-Host "source: $sourceRepository"
Write-Host "commit: $actualCommit"
Write-Host "tests: $(if ($SkipTests) { 'skipped by request' } else { 'passed' })"
Write-Host "next: open ESP-IDF v5.5.4 PowerShell and run scripts/build-accepted-baseline.ps1"
