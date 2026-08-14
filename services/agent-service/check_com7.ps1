# AR-AIPet: Verify that the StackChan firmware gateway URL matches the PC's
# current LAN IP and the correct /ws/device endpoint.
#
# This script does NOT require hardware to print the expected URL. It only
# needs COM7 access to COMPARE the device's reported URL against the expected
# one — that comparison is the HUMAN/HARDWARE step.
#
# Usage:
#   1. Start the unified agent-service (docker compose --profile unified up -d)
#   2. Reset StackChan, then within 3 seconds run:
#      powershell -ExecutionPolicy Bypass -File .\check_com7.ps1
#   3. Read the "CONFIG MISMATCH" or "CONFIG OK" line at the bottom.

$ErrorActionPreference = "Continue"

# --- Detect PC LAN IP (same logic as start_and_verify.ps1) ---
$lanIp = $null
try {
    $lanIp = (Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.InterfaceAlias -notmatch "vEthernet|Loopback" -and $_.PrefixOrigin -eq "Dhcp" } |
        Select-Object -First 1).IPAddress
} catch {}
if (-not $lanIp) {
    $lanIp = (Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.InterfaceAlias -notmatch "Loopback" } |
        Select-Object -First 1).IPAddress
}

$unifiedPort = $env:UNIFIED_PORT; if (-not $unifiedPort) { $unifiedPort = "8090" }
$expectedUrl = "ws://${lanIp}:${unifiedPort}/ws/device"

Write-Host "=== PC LAN IP ===" -ForegroundColor Cyan
if ($lanIp) {
    Write-Host "Detected PC LAN IP: $lanIp" -ForegroundColor Green
    Write-Host "Expected firmware gateway URL: $expectedUrl" -ForegroundColor Green
} else {
    Write-Host "Could NOT detect PC LAN IP. Set it manually." -ForegroundColor Red
    Write-Host "Expected format: ws://<YOUR_PC_IP>:${unifiedPort}/ws/device"
}

Write-Host ""
Write-Host "=== Known Firmware Config (from build artifacts) ===" -ForegroundColor Cyan
Write-Host "The last-built firmware had:"
Write-Host '  CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL="ws://192.168.50.133:8765"' -ForegroundColor Yellow
Write-Host "  (port 8765 = old Scheme B gateway; no /ws/device path)" -ForegroundColor Yellow
Write-Host "  If this does not match the Expected URL above, the device will"
Write-Host "  connect to the wrong endpoint and no session will be established."
Write-Host ""

Write-Host "=== Reading COM7 (20 s) ===" -ForegroundColor Yellow
Write-Host "Press StackChan reset NOW if you haven't already."
Start-Sleep -Seconds 3

$buffer = ""
try {
    $port = New-Object System.IO.Ports.SerialPort("COM7", 115200)
    $port.ReadTimeout = 1000
    $port.Open()
    $endTime = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $endTime) {
        try {
            $buffer += $port.ReadExisting()
            Start-Sleep -Milliseconds 100
        } catch {}
    }
    $port.Close()
} catch {
    Write-Host "COM7 error: $_" -ForegroundColor Red
    if ($port -and $port.IsOpen) { $port.Close() }
}

Write-Host ""
Write-Host "=== FULL COM7 OUTPUT ===" -ForegroundColor Cyan
Write-Host $buffer

Write-Host ""
Write-Host "=== PATTERN ANALYSIS ===" -ForegroundColor Cyan

# Wi-Fi
$deviceIp = $null
if ($buffer -match "got ip[:\s]+([0-9.]+)") {
    $deviceIp = $Matches[1]
    Write-Host "Wi-Fi CONNECTED: device IP = $deviceIp" -ForegroundColor Green
} else {
    Write-Host "Wi-Fi: NOT CONNECTED (no 'got ip' in serial output)" -ForegroundColor Red
    Write-Host "  -> Check: Is the AP configured? Is it 2.4 GHz? Was reset pressed?" -ForegroundColor Red
}

# Firmware-reported gateway URL
$deviceUrl = $null
if ($buffer -match "connecting action gateway[:\s]+([^\s\r\n]+)") {
    $deviceUrl = $Matches[1]
    Write-Host "Firmware gateway URL: $deviceUrl" -ForegroundColor Yellow
} elseif ($buffer -match "action gateway disabled") {
    Write-Host "Firmware gateway URL: DISABLED (empty CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL)" -ForegroundColor Red
} else {
    Write-Host "Firmware gateway URL: not found in serial output" -ForegroundColor Red
    Write-Host "  -> This usually means AI.AGENT app is NOT open." -ForegroundColor Yellow
    Write-Host "     The Mooncake firmware only calls startMcpActionClient()" -ForegroundColor Yellow
    Write-Host "     AFTER requestXiaozhiStart(), which only fires in AI.AGENT onOpen()." -ForegroundColor Yellow
}

# Connection status
if ($buffer -match "action gateway connected") {
    Write-Host "Gateway session: CONNECTED" -ForegroundColor Green
} elseif ($buffer -match "action gateway.*timed out") {
    Write-Host "Gateway session: TIMEOUT (URL wrong or server not listening)" -ForegroundColor Red
} elseif ($buffer -match "action gateway") {
    Write-Host "Gateway session: mentioned but status unclear" -ForegroundColor Yellow
} else {
    Write-Host "Gateway session: no mention (AI.AGENT app likely not open)" -ForegroundColor Red
}

# AI.AGENT lifecycle
if ($buffer -match "AI\.AGENT|onOpen|xiaozhi.*start|requestXiaozhiStart") {
    Write-Host "AI.AGENT app: lifecycle mentioned (good)" -ForegroundColor Green
} else {
    Write-Host "AI.AGENT app: NOT mentioned — open it on the device screen" -ForegroundColor Yellow
}

# MCP tools
Write-Host ""
Write-Host "=== MCP TOOLS FOUND ===" -ForegroundColor Cyan
$tools = [regex]::Matches($buffer, "Add tool:\s*(\S+)")
if ($tools.Count -gt 0) {
    foreach ($t in $tools) { Write-Host "  $($t.Groups[1].Value)" }
} else {
    Write-Host "  (none found in serial output)"
}

# Final config comparison
Write-Host ""
Write-Host "=== CONFIG COMPARISON ===" -ForegroundColor Cyan
if ($deviceUrl -and $expectedUrl) {
    if ($deviceUrl -eq $expectedUrl) {
        Write-Host "CONFIG OK: firmware URL matches PC's expected URL" -ForegroundColor Green
    } else {
        Write-Host "CONFIG MISMATCH:" -ForegroundColor Red
        Write-Host "  Firmware says:   $deviceUrl" -ForegroundColor Red
        Write-Host "  PC expects:      $expectedUrl" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Fix: rebuild firmware with the correct URL, or use"
        Write-Host "  gateway_config_set to update the device's fallback URL."
        Write-Host "  See docs/13-动作网关会话恢复步骤.md for exact commands."
    }
} elseif (-not $deviceUrl) {
    Write-Host "Cannot compare: firmware did not report a gateway URL." -ForegroundColor Yellow
    Write-Host "  Steps: (1) confirm Wi-Fi connected, (2) open AI.AGENT app," -ForegroundColor Yellow
    Write-Host "  (3) re-run this script after reset." -ForegroundColor Yellow
} else {
    Write-Host "Cannot compare: PC LAN IP not detected." -ForegroundColor Yellow
}
