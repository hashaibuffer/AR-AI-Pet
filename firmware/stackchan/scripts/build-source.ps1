param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot
)

$ErrorActionPreference = "Stop"
$moduleRoot = Split-Path -Parent $PSScriptRoot
$verify = Join-Path $PSScriptRoot "verify-source.ps1"
& powershell -ExecutionPolicy Bypass -File $verify -SourceRoot $SourceRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$idf = Get-Command idf.py -ErrorAction SilentlyContinue
if ($null -eq $idf) { throw "idf.py not found. Open ESP-IDF v5.5.4 PowerShell first." }
$idfVersion = (& $idf.Source --version | Out-String).Trim()
if ($idfVersion -notmatch "5\.5\.4") { throw "Expected ESP-IDF 5.5.4, got: $idfVersion" }

$firmware = Join-Path (Resolve-Path -LiteralPath $SourceRoot).Path "firmware"
if (-not (Test-Path -LiteralPath $firmware -PathType Container)) { throw "Firmware directory missing: $firmware" }
Push-Location $firmware
try {
    if (Test-Path -LiteralPath ".\fetch_repos.py" -PathType Leaf) {
        & python .\fetch_repos.py
        if ($LASTEXITCODE -ne 0) { throw "fetch_repos.py failed." }
    }
    $apply = Join-Path $moduleRoot "scripts\apply-patches.ps1"
    & powershell -ExecutionPolicy Bypass -File $apply -SourceRoot $SourceRoot
    if ($LASTEXITCODE -ne 0) { throw "Project patch application failed." }
    & idf.py set-target esp32s3
    if ($LASTEXITCODE -ne 0) { throw "idf.py set-target failed." }
    & idf.py build
    if ($LASTEXITCODE -ne 0) { throw "idf.py build failed." }
}
finally {
    Pop-Location
}
Write-Output "STACKCHAN_SOURCE_BUILD_OK"
