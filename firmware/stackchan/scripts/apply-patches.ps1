param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot
)

$ErrorActionPreference = "Stop"
$moduleRoot = Split-Path -Parent $PSScriptRoot
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$patchRoot = Join-Path $moduleRoot "patches"

function Fail([string]$Message) {
    throw $Message
}

if (-not (Test-Path -LiteralPath (Join-Path $SourceRoot ".git") -PathType Container)) {
    Fail "SourceRoot is not a Git checkout: $SourceRoot"
}

$rootStatus = & git -C $SourceRoot status --porcelain
if ($rootStatus) {
    Fail "StackChan source has local changes; refusing to apply project patches. Commit or clean only this checkout first."
}

function ApplyPatch([string]$Repo, [string]$PatchPath, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Repo -PathType Container)) {
        Fail "$Label repository not found: $Repo"
    }

    & git -C $Repo apply --check $PatchPath 2>$null
    if ($LASTEXITCODE -eq 0) {
        & git -C $Repo apply $PatchPath
        if ($LASTEXITCODE -ne 0) { Fail "$Label patch application failed." }
        Write-Output "$Label PATCH_APPLIED"
        return
    }

    & git -C $Repo apply --reverse --check $PatchPath 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Output "$Label PATCH_ALREADY_APPLIED"
        return
    }

    Fail "$Label patch does not apply cleanly and is not already applied: $PatchPath"
}

ApplyPatch $SourceRoot (Join-Path $patchRoot "0003-stackchan-control-adapter.patch") "stackchan-adapter"
ApplyPatch $SourceRoot (Join-Path $patchRoot "0005-mcp-action-client.patch") "stackchan-action-client"

$xiaozhi = Join-Path $SourceRoot "firmware\xiaozhi-esp32"
if (Test-Path -LiteralPath $xiaozhi -PathType Container) {
    $changed = @(git -C $xiaozhi diff --name-only)
    $protected = @("main/mcp_server.cc", "main/mcp_server.h")
    if (@($changed | Where-Object { $protected -contains $_ }).Count -gt 0) {
        Fail "Xiaozhi MCP server files already contain unreviewed local changes; refusing to apply 0004."
    }
    ApplyPatch $xiaozhi (Join-Path $patchRoot "0004-xiaozhi-mcp-reply-routing.patch") "xiaozhi-mcp-routing"
} else {
    Fail "Xiaozhi dependency checkout not found. Run firmware/fetch_repos.py first."
}

Write-Output "STACKCHAN_PROJECT_PATCHES_OK"
