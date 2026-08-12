param(
    [string]$UnityPath = 'D:\Program Files\Unity Hub\Edit\2022.3.62f3\Editor\Unity.exe',
    [string]$ProjectPath = "$PSScriptRoot\..\Project"
)

$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath $ProjectPath).Path
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$compileLog = Join-Path $root 'unity_compile.log'
$playLog = Join-Path $root 'unity_playmode_smoke.log'
$result = Join-Path $project 'Library\AgentPlayModeSmokeResult.json'

if (-not (Test-Path -LiteralPath $UnityPath)) {
    throw "Unity executable not found: $UnityPath"
}

function Invoke-Unity([string[]]$Arguments) {
    $process = Start-Process -FilePath $UnityPath -ArgumentList $Arguments -WindowStyle Hidden -PassThru -Wait
    if ($process.ExitCode -ne 0) {
        throw "Unity exited with code $($process.ExitCode). See the log passed to -logFile."
    }
}

Invoke-Unity @(
    '-batchmode', '-nographics', '-quit', '-accept-apiupdate',
    '-projectPath', $project, '-logFile', $compileLog
)

if (Select-String -LiteralPath $compileLog -Pattern 'error CS|Compilation failed' -Quiet) {
    throw "Unity script compilation failed. See $compileLog"
}

Remove-Item -LiteralPath $result -Force -ErrorAction SilentlyContinue
Invoke-Unity @(
    '-batchmode', '-nographics', '-accept-apiupdate',
    '-projectPath', $project,
    '-executeMethod', 'ARAIPet.Editor.AgentPlayModeSmoke.Run',
    '-logFile', $playLog
)

if (-not (Test-Path -LiteralPath $result)) {
    throw "Play Mode smoke did not write $result"
}

$smoke = Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
if (-not $smoke.passed) {
    throw "Unity-Agent Play Mode smoke failed. See $playLog"
}

Write-Output "UNITY_AGENT_SMOKE_OK $result"
