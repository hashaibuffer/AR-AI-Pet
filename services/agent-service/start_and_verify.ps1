# AR-AIPet: Start the unified agent-service and verify the StackChan
# action-gateway session.
#
# Usage: powershell -ExecutionPolicy Bypass -File .\start_and_verify.ps1
#
# This script:
#   1. Starts the Docker unified profile
#   2. Waits for the health endpoint
#   3. Detects the PC LAN IP and prints the firmware gateway URL the
#      device should be pointing to
#   4. Checks /health/device for an active device session
#   5. Reads COM7 serial output and compares the device's reported URL
#   6. Optionally sends a test MCP action

$ErrorActionPreference = "Continue"
$ProjectRoot = "D:\projects\AR-AIPet"

Write-Host "=== 1. Start Docker unified service ===" -ForegroundColor Cyan
Set-Location "$ProjectRoot\services\agent-service"

cmd /c "docker compose --profile unified up --build -d 2>&1"

Write-Host ""
Write-Host "=== 2. Wait for service to be healthy ===" -ForegroundColor Cyan
$unifiedPort = $env:UNIFIED_PORT; if (-not $unifiedPort) { $unifiedPort = "8090" }
$attempts = 0
$maxAttempts = 30
while ($attempts -lt $maxAttempts) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:${unifiedPort}/health" -TimeoutSec 3
        Write-Host "Health check: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
        break
    } catch {
        $attempts++
        Write-Host "  Waiting for service... ($attempts/$maxAttempts)"
        Start-Sleep -Seconds 2
    }
}
if ($attempts -ge $maxAttempts) {
    Write-Host "Service did not become healthy in time. Check logs:" -ForegroundColor Red
    docker compose --profile unified logs --tail=30
    exit 1
}

Write-Host ""
Write-Host "=== 3. Detect PC LAN IP ===" -ForegroundColor Cyan
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
$expectedUrl = "ws://${lanIp}:${unifiedPort}/ws/device"
Write-Host "Windows LAN IP: $lanIp"
Write-Host "Agent service:   http://${lanIp}:${unifiedPort}/health"
Write-Host "/ws/device:      $expectedUrl"
Write-Host ""
Write-Host "The firmware MUST have CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL"
Write-Host "set to this exact URL for the device session to come up."
Write-Host "Known stale config: ws://192.168.50.133:8765 (old Scheme B, wrong port+path)"

Write-Host ""
Write-Host "=== 4. Check device session ===" -ForegroundColor Cyan
try {
    $dev = Invoke-RestMethod -Uri "http://localhost:${unifiedPort}/health/device" -TimeoutSec 3
    if ($dev.sessionCount -gt 0) {
        Write-Host "Device session: ACTIVE ($($dev.sessionCount) connected)" -ForegroundColor Green
        $dev.deviceSessions | ForEach-Object { Write-Host "  deviceId=$($_.deviceId) protocol=$($_.protocol)" }
    } else {
        Write-Host "Device session: NONE (no real StackChan connected)" -ForegroundColor Red
        Write-Host "  The device has not established a /ws/device session." -ForegroundColor Yellow
        Write-Host "  Check: (a) Wi-Fi on same 2.4GHz network? (b) AI.AGENT app open?" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Device session check failed: $_" -ForegroundColor Yellow
    Write-Host "  /health/device may not be available in this service version." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 5. Read COM7 (StackChan serial) ===" -ForegroundColor Cyan
try {
    $port = New-Object System.IO.Ports.SerialPort("COM7", 115200)
    $port.ReadTimeout = 5000
    $port.Open()
    Write-Host "COM7 opened, reading for 5 seconds..."
    $endTime = (Get-Date).AddSeconds(5)
    $buffer = ""
    while ((Get-Date) -lt $endTime) {
        try {
            $buffer += $port.ReadExisting()
            Start-Sleep -Milliseconds 200
        } catch {}
    }
    $port.Close()
    Write-Host "COM7 output (last 500 chars):"
    Write-Host $buffer.Substring([Math]::Max(0, $buffer.Length - 500))

    # Pattern checks
    if ($buffer -match "got ip") { Write-Host "Wi-Fi: CONNECTED" -ForegroundColor Green }
    else { Write-Host "Wi-Fi: not found (reset StackChan or check AP)" -ForegroundColor Yellow }

    if ($buffer -match "connecting action gateway:\s*(\S+)") {
        $devUrl = $Matches[1]
        Write-Host "Firmware gateway URL: $devUrl" -ForegroundColor Yellow
        if ($devUrl -eq $expectedUrl) {
            Write-Host "  CONFIG OK: matches expected URL" -ForegroundColor Green
        } else {
            Write-Host "  CONFIG MISMATCH: expected $expectedUrl" -ForegroundColor Red
            Write-Host "  Fix: rebuild firmware or use gateway_config_set" -ForegroundColor Red
            Write-Host "  See docs/13-动作网关会话恢复步骤.md" -ForegroundColor Red
        }
    } elseif ($buffer -match "action gateway disabled") {
        Write-Host "Gateway: DISABLED (empty URL in Kconfig)" -ForegroundColor Red
    } else {
        Write-Host "Gateway URL: not in serial output (AI.AGENT app may not be open)" -ForegroundColor Yellow
    }

    if ($buffer -match "action gateway connected") {
        Write-Host "Gateway session: CONNECTED" -ForegroundColor Green
    } elseif ($buffer -match "action gateway.*timed out") {
        Write-Host "Gateway session: TIMEOUT" -ForegroundColor Red
    }
} catch {
    Write-Host "COM7 access failed: $_" -ForegroundColor Yellow
    Write-Host "Close other serial monitors first."
}

Write-Host ""
Write-Host "=== 6. Test MCP tool call (head action) ===" -ForegroundColor Cyan
$body = @{ jsonrpc = "2.0"; id = 1; method = "tools/call"; params = @{ name = "robot.react"; arguments = @{ intent = "wave"; parameters = @{ motion = "happy" } } } } | ConvertTo-Json -Depth 5
try {
    $response = Invoke-RestMethod -Uri "http://localhost:${unifiedPort}/mcp" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Host "MCP response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "MCP call failed: $_" -ForegroundColor Yellow
    Write-Host "Expected if StackChan hasn't connected yet."
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "Agent service: http://localhost:${unifiedPort}"
Write-Host "Device endpoint: $expectedUrl"
Write-Host ""
Write-Host "If the device session is not established:"
Write-Host "1. Confirm StackChan and PC are on the same 2.4 GHz Wi-Fi"
Write-Host "2. Open AI.AGENT app on StackChan screen (required for Mooncake)"
Write-Host "3. Confirm firmware CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL = $expectedUrl"
Write-Host "4. If URL is wrong, rebuild firmware or use gateway_config_set"
Write-Host "5. See docs/13-动作网关会话恢复步骤.md for full steps"
