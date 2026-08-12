param(
    [Parameter(Mandatory = $true)]
    [string]$PackagePath,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $PackagePath).Path
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\Project')).Path
$packagesRoot = Join-Path $projectRoot 'Packages'
$target = Join-Path $packagesRoot 'com.xreal.xr'
$tempRoot = Join-Path (Split-Path -Parent $projectRoot) ('.xreal-sdk-' + [Guid]::NewGuid().ToString('N'))

if (Test-Path -LiteralPath $target) {
    if (-not $Force) {
        throw "XREAL SDK already exists at $target. Use -Force to replace it."
    }
    $resolvedTarget = (Resolve-Path -LiteralPath $target).Path
    if (-not $resolvedTarget.StartsWith($packagesRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to delete a path outside Packages: $resolvedTarget"
    }
    Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
}

try {
    if (Test-Path -LiteralPath $source -PathType Container) {
        $packageRoot = $source
    }
    else {
        New-Item -ItemType Directory -Path $tempRoot | Out-Null
        tar -xf $source -C $tempRoot
        $packageJson = Get-ChildItem -LiteralPath $tempRoot -Recurse -File -Filter package.json |
            Where-Object { (Get-Content -LiteralPath $_.FullName -Raw) -match '"name"\s*:\s*"com\.xreal\.xr"' } |
            Select-Object -First 1
        if ($null -eq $packageJson) { throw 'The archive does not contain com.xreal.xr/package.json.' }
        $packageRoot = Split-Path -Parent $packageJson.FullName
    }

    $manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'package.json') -Raw | ConvertFrom-Json
    if ($manifest.name -ne 'com.xreal.xr') { throw "Unexpected package name: $($manifest.name)" }
    Copy-Item -LiteralPath $packageRoot -Destination $target -Recurse
    Write-Output "XREAL_SDK_READY $($manifest.version) $target"
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}
