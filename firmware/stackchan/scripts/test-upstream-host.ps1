$ErrorActionPreference = "Stop"

$moduleRoot = Split-Path -Parent $PSScriptRoot
$upstream = Join-Path $moduleRoot "upstream"
$firmware = Join-Path $upstream "firmware"
$patch = Join-Path $moduleRoot "patches\0001-host-tests-cxx20-pi.patch"
$expectedSha = "b72b3ede38b32d54f0b6ba51c62cfcef2ec3ae1e"

function Stop-WithError {
    param([string]$Message)

    Write-Error $Message
    exit 1
}

function Resolve-Tool {
    param([string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        $scripts = (& $python.Source -c "import sysconfig; print(sysconfig.get_path('scripts', scheme='nt_user'))").Trim()
        if ($LASTEXITCODE -eq 0 -and $scripts) {
            $candidate = Join-Path $scripts ("{0}.exe" -f $Name)
            if (Test-Path -LiteralPath $candidate) {
                return $candidate
            }
        }
    }

    Stop-WithError "$Name not found. Install CMake (including ctest) and ensure it is on PATH."
}

function Invoke-Checked {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [string]$Step
    )

    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $Executable @Arguments
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
    if ($exitCode -ne 0) {
        Stop-WithError "$Step failed with exit code $exitCode."
    }
}

function Test-PatchCheck {
    param([string[]]$GitArguments)

    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & git -C $upstream apply @GitArguments 2>$null
        return ($LASTEXITCODE -eq 0)
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
}

if (-not (Test-Path -LiteralPath $upstream -PathType Container)) {
    Stop-WithError "upstream directory not found: $upstream. Clone StackChan into firmware/stackchan/upstream first."
}
if (-not (Test-Path -LiteralPath $firmware -PathType Container)) {
    Stop-WithError "upstream firmware directory not found: $firmware."
}
if (-not (Test-Path -LiteralPath $patch -PathType Leaf)) {
    Stop-WithError "patch file not found: $patch."
}

$head = (& git -C $upstream rev-parse HEAD 2>$null).Trim()
if ($LASTEXITCODE -ne 0 -or -not $head) {
    Stop-WithError "Unable to read upstream HEAD. Check that upstream is a Git checkout."
}
if ($head -ne $expectedSha) {
    Stop-WithError "Unexpected upstream HEAD '$head'. Expected '$expectedSha'. Update README or re-checkout the fixed baseline before running this script."
}

$patchStatus = "already applied"
if (-not (Test-PatchCheck @("--unidiff-zero", "--reverse", "--check", $patch))) {
    if (-not (Test-PatchCheck @("--unidiff-zero", "--check", $patch))) {
        Stop-WithError "Patch cannot be applied cleanly. Resolve the upstream baseline or patch first; no files were force-overwritten."
    }
    if (-not (Test-PatchCheck @("--unidiff-zero", $patch))) {
        Stop-WithError "Applying the patch failed. No conflict files were overwritten."
    }
    $patchStatus = "newly applied"
}

$cmake = Resolve-Tool "cmake"
$ctest = Resolve-Tool "ctest"

Push-Location $firmware
try {
    Invoke-Checked $cmake @("-S", "tests", "-B", "build-host-tests") "CMake configure"
    Invoke-Checked $cmake @("--build", "build-host-tests") "CMake build"

    $cache = Join-Path $firmware "build-host-tests\CMakeCache.txt"
    $generatorLine = if (Test-Path -LiteralPath $cache) {
        Select-String -LiteralPath $cache -Pattern '^CMAKE_GENERATOR:INTERNAL=' | Select-Object -First 1
    }
    $ctestArguments = @("--test-dir", "build-host-tests")
    if ($generatorLine -and $generatorLine.Line -match 'Visual Studio') {
        $ctestArguments += @("-C", "Debug")
    }
    $ctestArguments += "--output-on-failure"
    Invoke-Checked $ctest $ctestArguments "CTest"
}
finally {
    Pop-Location
}

Write-Host "upstream SHA: $head"
Write-Host "patch: $patchStatus"
Write-Host "build: passed"
Write-Host "CTest: passed"
