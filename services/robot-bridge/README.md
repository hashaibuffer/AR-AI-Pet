# Robot Bridge

Robot Bridge 是 Agent Gateway 与实体设备之间的执行边界。它只消费高层语义动作，不决定日程、农场或游戏规则，也不直接操作 PWM、电机寄存器或 BLE 字节。

```text
Agent Gateway
  → experience.event
  → Robot Bridge
  → MockRobotAdapter 或 StackChanWebSocketAdapter
  → experience.action.result
  → Agent Gateway / PostgreSQL
```

## 运行模式

`ROBOT_ADAPTER` 有两种值：

- `mock`：默认模式，不需要机器人，供本地开发和 CI 使用。
- `stackchan`：连接 StackChan 的 MCP WebSocket，再由 StackChan 通过 BLE 控制 NanoDrive 底座。

真实模式至少配置：

```powershell
$env:ROBOT_ADAPTER = 'stackchan'
$env:ROBOT_DEVICE_ID = 'stackchan-robot'
$env:STACKCHAN_WS_URL = 'ws://192.168.50.213:8080/ws'
python -m app.main
```

实际地址应按现场设备填写，不要把局域网 IP 写进代码。完整变量见 [`.env.example`](.env.example)。

### 当前现场链路待改善

仓库同时保留两种 StackChan 控制路径，不能混用：

| 路径 | 连接方向 | 端口/入口 | 当前状态 |
| --- | --- | --- | --- |
| 直接设备 MCP | Robot Bridge → StackChan | `ws://设备IP:8080/ws` | 适配器已实现；需确认当前刷入固件是否启用该服务 |
| Scheme B 网关 | StackChan → 局域网 Gateway；Robot Bridge → Gateway | 设备侧 `ws://电脑IP:8765/`；网关 MCP `http://电脑IP:8767/mcp` | `stackchan-mcp` 参考固件采用此方向；当前设备与该源码的精确对应尚未证明，项目侧桥接尚未切换到此入口 |

因此，不能只看到 StackChan 已联网就判定 Robot Bridge 已接入。现场排查必须先记录：设备 IP、电脑局域网 IP、固件配置的动作网关 URL、8765/8767 监听状态和网关日志中的设备连接状态。当前缺少这组配对证据，列为后续实机联调待办；在确认前不要让底座执行移动动作。

## 语义动作映射

| Agent 动作 | StackChan MCP 工具 | 说明 |
| --- | --- | --- |
| `nod` | `self.robot.set_head_angles` 两次 | 点头序列 |
| `shake_head` | `self.robot.set_head_angles` 三次 | 摇头序列 |
| `look_at_user` | `self.robot.set_head_angles` | 使用受限 yaw/pitch |
| `wave`、`celebrate`、`dance`、`farm_tend` | `self.robot.play_motion` | 动作名可由参数指定 |
| `base_move`、`base_turn` | `self.robot.base_move` → `self.robot.base_stop` | 单次移动自动限时 |
| `base_drive` | `self.robot.base_drive` → `self.robot.base_stop` | 左右轮速度均限幅 |
| `base_stop`、`stop` | `base_stop`，`stop` 还会调用 `stop_motion` | 最高优先级 |

底座速度上限为 180，单次移动默认 0.5 秒、最大 1.5 秒。NanoDrive 自身的 watchdog 仍是最后一层保护。

## 动作结果边界

官方 StackChan WebSocket 通常只接受 MCP JSON-RPC 写入，不返回可靠的实体动作完成反馈。因此真实适配器使用：

- `completed`：Mock 适配器的模拟完成；
- `dispatched`：真实适配器已将指令发送给 StackChan 网关；
- `physicalConfirmed=false`：当前没有传感器或固件回执，不能声称实体动作已完成；
- `failed`、`cancelled`、`timeout`：通信或执行异常。

示例：

```json
{
  "status": "dispatched",
  "measuredResult": {
    "adapter": "stackchan-websocket",
    "transportAccepted": true,
    "physicalConfirmed": false,
    "confirmationReason": "stackchan_gateway_has_no_physical_feedback"
  }
}
```

任何取消、Agent 断线或远程停止都会先取消正在执行的语义动作，再尽力发送 `stop_motion` 和 `base_stop`。底座断链后的最终停止由 NanoDrive watchdog 保证。

## 本地验证

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

这组测试启动本地假的 StackChan WebSocket，只检查 JSON-RPC 映射、参数边界、停止和失败结果，不代表实体硬件通过。

项目级 Mock 闭环仍使用：

```powershell
docker compose -f services/agent-service/docker-compose.yml up -d --build robot-bridge
docker compose -f services/agent-service/docker-compose.yml exec -T robot-bridge python scripts/bridge_smoke.py
```

输出 `ROBOT_BRIDGE_SMOKE_OK` 只代表 Agent Gateway → Robot Bridge → Mock 的软件闭环。StackChan/NanoDrive 实机证据记录在 [`docs/11-NanoDrive联调记录.md`](../../docs/11-NanoDrive联调记录.md)。
