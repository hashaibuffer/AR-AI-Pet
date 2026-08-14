param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot
)

$ErrorActionPreference = "Stop"
$moduleRoot = Split-Path -Parent $PSScriptRoot
$lockPath = Join-Path $moduleRoot "source.lock.json"

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) {
    Fail "SourceRoot not found: $SourceRoot"
}
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$lock = Get-Content -Raw -Encoding utf8 $lockPath | ConvertFrom-Json

$head = (& git -C $SourceRoot rev-parse HEAD 2>$null).Trim()
if ($LASTEXITCODE -ne 0 -or -not $head) {
    Fail "SourceRoot is not a valid Git checkout: $SourceRoot"
}
if ($head -ne $lock.sourceCommit) {
    Fail "Unexpected source commit '$head'; expected '$($lock.sourceCommit)'."
}

$dirty = & git -C $SourceRoot status --porcelain 2>$null
if ($LASTEXITCODE -ne 0) {
    Fail "Unable to read source worktree status."
}
if ($dirty) {
    Fail "Source worktree has local changes; refusing to use an unreviewed source."
}

foreach ($property in $lock.sourceFiles.psobject.Properties) {
    $path = Join-Path $SourceRoot ($property.Name -replace '/', '\\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Fail "Locked source file is missing: $($property.Name)"
    }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($actual -ne $property.Value.ToUpperInvariant()) {
        Fail "Source hash mismatch: $($property.Name)"
    }
}

$reposPath = Join-Path $SourceRoot "firmware\repos.json"
if (-not (Test-Path -LiteralPath $reposPath -PathType Leaf)) {
    Fail "Dependency manifest missing: firmware/repos.json"
}
$repos = Get-Content -Raw -Encoding utf8 $reposPath | ConvertFrom-Json
foreach ($dependency in $lock.dependencies) {
    $found = $repos | Where-Object { $_.url -eq $dependency.repository -and $_.path -eq $dependency.path -and $_.branch -eq $dependency.ref }
    if (-not $found) {
        Fail "Dependency pin mismatch: $($dependency.repository)@$($dependency.ref)"
    }
}

Write-Output "SOURCE_LOCK_OK"
Write-Output "source=$head"
Write-Output "projectVersion=$($lock.projectVersion)"
Write-Output "toolchain=$($lock.toolchain.espIdf),$($lock.toolchain.target),$($lock.toolchain.board)"
Write-Output "deviceIdentity=$($lock.deviceIdentity.status)"
