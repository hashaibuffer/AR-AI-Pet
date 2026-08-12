$ErrorActionPreference = 'Stop'

$moduleRoot = Split-Path -Parent $PSScriptRoot
$buildDir = Join-Path $moduleRoot 'build-host'

cmake -S $moduleRoot -B $buildDir
if ($LASTEXITCODE -ne 0) { throw 'Host-test configure failed.' }
cmake --build $buildDir
if ($LASTEXITCODE -ne 0) { throw 'Host-test build failed.' }
ctest --test-dir $buildDir -C Debug --output-on-failure
if ($LASTEXITCODE -ne 0) { throw 'Host tests failed.' }
