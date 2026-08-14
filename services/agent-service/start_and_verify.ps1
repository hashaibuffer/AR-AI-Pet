# AR-AIPet: Start unified service + verify StackChan action gateway
# Run this in PowerShell on your Windows machine
# Usage: powershell -ExecutionPolicy Bypass -File .\start_and_verify.ps1

$ErrorActionPreference = "Continue"
$ProjectRoot = "D:\projects\AR-AIPet"

Write-Host "=== 1. Start Docker unified service ===" -ForegroundColor Cyan
Set-Location "$ProjectRoot\services\agent-service"

# Start unified profile (postgres + qdrant + ar-aipet-server)
# Docker writes progress to stderr; use cmd to avoid PowerShell error
cmd /c "docker compose --profile unified up --build -d 2>&1"

Write-Host ""
Write-Host "=== 2. Wait for services to be healthy ===" -ForegroundColor Cyan
$attempts = 0
$maxAttempts = 30
while ($attempts -lt $maxAttempts) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8090/health" -TimeoutSec 3
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
Write-Host "=== 3. Get Windows LAN IP ===" -ForegroundColor Cyan
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "vEthernet|Loopback" -and $_.PrefixOrigin -eq "Dhcp" } | Select-Object -First 1).IPAddress
if (-not $lanIp) {
    $lanIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "Loopback" } | Select-Object -First 1).IPAddress
}
Write-Host "Windows LAN IP: $lanIp"
Write-Host "Agent service: http://${lanIp}:8090/health"
Write-Host "/ws/device endpoint: ws://${lanIp}:8090/ws/device"

Write-Host ""
Write-Host "=== 4. Check COM7 (StackChan serial) ===" -ForegroundColor Cyan
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

    # Check for key patterns
    if ($buffer -match "got ip") { Write-Host "Wi-Fi: CONNECTED" -ForegroundColor Green }
    else { Write-Host "Wi-Fi: not found in recent output (may need to reset StackChan)" -ForegroundColor Yellow }

    if ($buffer -match "action gateway.*connecting") { Write-Host "McpActionClient: connecting" -ForegroundColor Green }
    if ($buffer -match "action gateway connected") { Write-Host "McpActionClient: CONNECTED" -ForegroundColor Green }
    if ($buffer -match "action gateway.*timed out") { Write-Host "McpActionClient: TIMEOUT (check URL config)" -ForegroundColor Red }
} catch {
    Write-Host "COM7 access failed: $_" -ForegroundColor Yellow
    Write-Host "You may need to close other serial monitors first."
}

Write-Host ""
Write-Host "=== 5. Test MCP tool call (head action) ===" -ForegroundColor Cyan
$body = @{ jsonrpc = "2.0"; id = 1; method = "tools/call"; params = @{ name = "robot.react"; arguments = @{ intent = "wave"; parameters = @{ motion = "happy" } } } } | ConvertTo-Json -Depth 5
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8090/mcp" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Host "MCP response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "MCP call failed: $_" -ForegroundColor Yellow
    Write-Host "This is expected if StackChan hasn't connected yet."
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "Agent service is running on port 8090."
Write-Host "Next steps:"
Write-Host "1. Open AI.AGENT app on StackChan screen"
Write-Host "2. Check COM7 logs for 'action gateway connected'"
Write-Host "3. If McpActionClient URL is wrong, need to rebuild firmware with correct URL"
Write-Host "   The firmware URL should be: ws://${lanIp}:8090/ws/device"
Write-Host ""
Write-Host "Press Enter to view service logs, or Ctrl+C to exit."
Read-Host
docker compose --profile unified logs --tail=50 ar-aipet-server
