# Read COM7 for 20 seconds to capture StackChan full boot log
# Usage: Reset StackChan first, then run: powershell -ExecutionPolicy Bypass -File .\check_com7.ps1

Write-Host "Reading COM7 for 20 seconds. Make sure you pressed StackChan reset first." -ForegroundColor Yellow
Write-Host "Starting in 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$port = New-Object System.IO.Ports.SerialPort("COM7", 115200)
$port.ReadTimeout = 1000
try {
    $port.Open()
    $endTime = (Get-Date).AddSeconds(20)
    $buffer = ""
    while ((Get-Date) -lt $endTime) {
        try {
            $buffer += $port.ReadExisting()
            Start-Sleep -Milliseconds 100
        } catch {}
    }
    $port.Close()
} catch {
    Write-Host "COM7 error: $_" -ForegroundColor Red
    if ($port.IsOpen) { $port.Close() }
}

Write-Host ""
Write-Host "=== FULL COM7 OUTPUT ===" -ForegroundColor Cyan
Write-Host $buffer

Write-Host ""
Write-Host "=== PATTERN ANALYSIS ===" -ForegroundColor Cyan
if ($buffer -match "got ip[:\s]+([0-9.]+)") { Write-Host "Wi-Fi CONNECTED: $($Matches[1])" -ForegroundColor Green }
else { Write-Host "Wi-Fi: NOT CONNECTED (no 'got ip' found)" -ForegroundColor Red }

if ($buffer -match "action gateway.*connecting[:\s]+([^\s]+)") { Write-Host "Gateway URL: $($Matches[1])" -ForegroundColor Yellow }
else { Write-Host "Gateway URL: not found (McpActionClient may not be enabled)" -ForegroundColor Red }

if ($buffer -match "action gateway connected") { Write-Host "Gateway: CONNECTED" -ForegroundColor Green }
elseif ($buffer -match "action gateway.*timed out") { Write-Host "Gateway: TIMEOUT" -ForegroundColor Red }
elseif ($buffer -match "action gateway") { Write-Host "Gateway: mentioned but status unclear" -ForegroundColor Yellow }
else { Write-Host "Gateway: no mention (check if AI.AGENT app is open)" -ForegroundColor Red }

if ($buffer -match "AI\.AGENT|onOpen|xiaozhi") { Write-Host "AI.AGENT app: mentioned" -ForegroundColor Green }
else { Write-Host "AI.AGENT app: not mentioned (may need to open it manually)" -ForegroundColor Yellow }

Write-Host ""
Write-Host "=== MCP TOOLS FOUND ===" -ForegroundColor Cyan
$tools = [regex]::Matches($buffer, "Add tool: (\S+)")
foreach ($t in $tools) { Write-Host "  $($t.Groups[1].Value)" }

Write-Host ""
Write-Host "=== EXPECTED GATEWAY URL ===" -ForegroundColor Cyan
Write-Host "ws://192.168.50.133:8090/ws/device"
Write-Host "Compare with the 'Gateway URL' shown above."
