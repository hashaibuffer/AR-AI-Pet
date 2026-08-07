# StackChan MCP 控制测试

本工具只验证局域网电脑 → 官方 WebSocket → StackChan `McpServer` 的调用链路。
它不代表 Beam Pro、Unity 或底座已经接入。

前提：电脑和 StackChan 在同一 Wi-Fi，固件已启用 WebSocket server support，
StackChan 已启动 AI.Agent，官方服务监听 `8080/ws`。

```powershell
.\Invoke-StackChanControl.ps1 -RobotHost 192.168.1.20 -Action list_tools
.\Invoke-StackChanControl.ps1 -RobotHost 192.168.1.20 -Action play_motion -Name happy
.\Invoke-StackChanControl.ps1 -RobotHost 192.168.1.20 -Action stop_motion
.\Invoke-StackChanControl.ps1 -RobotHost 192.168.1.20 -Action set_head_angles -Yaw 20 -Pitch 5 -Speed 300
```

发送格式是官方 MCP JSON-RPC，不再使用项目自定义的 `action` 或 `robot.ping` 协议。
官方 WebSocket 不直接返回 MCP 结果；本轮以串口日志和机器人实际动作作为执行证据。
