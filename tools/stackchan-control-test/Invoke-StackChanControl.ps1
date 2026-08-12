[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RobotHost,

    [ValidateSet('list_tools', 'play_motion', 'stop_motion', 'set_head_angles', 'base_move', 'base_drive', 'base_stop')]
    [string]$Action = 'list_tools',

    [ValidateSet('happy', 'robot', 'panic', 'look_around')]
    [string]$Name = 'happy',

    [int]$Yaw = 0,
    [int]$Pitch = 0,
    [ValidateRange(100, 1000)]
    [int]$Speed = 300,

    [ValidateSet('forward', 'backward', 'left', 'right')]
    [string]$Direction = 'forward',

    [ValidateRange(-180, 180)]
    [int]$Left = 0,

    [ValidateRange(-180, 180)]
    [int]$Right = 0,

    [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'

# StackChan's MCP parser currently accepts numeric JSON-RPC ids only.
$requestId = 1

switch ($Action) {
    'list_tools' {
        $method = 'tools/list'
        $arguments = @{}
    }
    'play_motion' {
        $method = 'tools/call'
        $arguments = @{ name = $Name }
    }
    'stop_motion' {
        $method = 'tools/call'
        $arguments = @{}
    }
    'set_head_angles' {
        $method = 'tools/call'
        $arguments = @{ yaw = $Yaw; pitch = $Pitch; speed = $Speed }
    }
    'base_move' {
        $method = 'tools/call'
        $arguments = @{ direction = $Direction; speed = [Math]::Min($Speed, 180) }
    }
    'base_drive' {
        $method = 'tools/call'
        $arguments = @{ left = $Left; right = $Right }
    }
    'base_stop' {
        $method = 'tools/call'
        $arguments = @{}
    }
}

$toolName = switch ($Action) {
    'play_motion' { 'self.robot.play_motion' }
    'stop_motion' { 'self.robot.stop_motion' }
    'set_head_angles' { 'self.robot.set_head_angles' }
    'base_move' { 'self.robot.base_move' }
    'base_drive' { 'self.robot.base_drive' }
    'base_stop' { 'self.robot.base_stop' }
    default { $null }
}

$params = if ($toolName) {
    @{ name = $toolName; arguments = $arguments }
} else {
    @{}
}

$message = @{
    jsonrpc = '2.0'
    id      = $requestId
    method  = $method
    params  = $params
}

$json = $message | ConvertTo-Json -Compress -Depth 8
$bytes = [Text.Encoding]::UTF8.GetBytes($json)
$socket = [System.Net.WebSockets.ClientWebSocket]::new()
$uri = [Uri]::new("ws://$RobotHost`:$Port/ws")

try {
    $socket.ConnectAsync($uri, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
    $segment = [ArraySegment[byte]]::new($bytes)
    $socket.SendAsync(
        $segment,
        [System.Net.WebSockets.WebSocketMessageType]::Text,
        $true,
        [Threading.CancellationToken]::None
    ).GetAwaiter().GetResult()

    # The official OttoRobot server forwards MCP replies through Xiaozhi's
    # protocol, so this first hardware test uses the StackChan serial log and
    # physical motion as execution evidence instead of waiting for a WebSocket
    # response that the official server does not send.
    Start-Sleep -Milliseconds 300

    [pscustomobject]@{
        Endpoint = $uri.AbsoluteUri
        Sent     = $json
        Evidence = 'Check StackChan serial log and physical response.'
    } | Format-List
}
finally {
    if ($socket.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
        $socket.CloseAsync(
            [System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure,
            'test complete',
            [Threading.CancellationToken]::None
        ).GetAwaiter().GetResult()
    }
    $socket.Dispose()
}
