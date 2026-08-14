# StackChan 项目动作适配

这里保存项目动作客户端的源码参考。正式固件通过 `patches/0003` 和 `patches/0005` 将它们加入锁定的 Mooncake/Kimito 上游源码，不直接提交完整上游目录。

## 保留的动作语义

```text
self.robot.play_motion(name)
self.robot.stop_motion()
```

`name` 只允许固件中已有的固定动作：`happy`、`robot`、`panic`、`look_around`。

## 两条连接

```text
AI.AGENT / Xiaozhi 语音连接
  负责唤醒、录音、TTS 和对话

AR-AIPet 统一服务 /ws/device
  负责动作 MCP 请求
  ↓
StackChan McpActionClient
  ↓
同一份本地 McpServer 工具
```

动作连接是可选的第二条 WebSocket，由 `CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL` 控制；不配置时不影响原有 StackChan 功能。NanoDrive 和底座动作仍属于后续设备链路，不在本适配器中伪造完成。
