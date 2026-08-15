# Robot Bridge

Robot Bridge 是 Agent Gateway 与实体设备之间的动作执行边界。

当前同时保留两个适配器：`MockRobotAdapter` 用于软件验收，`StackChanAdapter` 通过独立动作网关调用真实设备。

```text
Agent Gateway
→ experience.event
→ Robot Bridge
→ 语义动作执行
→ experience.action.result
→ Agent Gateway / PostgreSQL
```

Bridge 不连接 PostgreSQL，不运行模型，也不决定日程、农场或游戏规则。它只消费高层动作意图，并把执行结果回传。

```text
Agent Gateway ──experience.event──> Robot Bridge ──semantic MCP──> StackChan
                                      │                         ↑
                                      └─ independent action WS ─┘
```

StackChan 主语音仍连接官方 Xiaozhi/AI.AGENT；第二条 WebSocket 只承载动作 MCP，不传语音，不改变对话状态。

## 启动

在 `services/agent-service` 下启动全部服务：

```powershell
docker compose up -d --build robot-bridge
```

默认连接 `ws://agent-runtime:8082/ws`，设备 ID 为 `mock-robot`。动作网关默认监听 `0.0.0.0:8765`。

## 本机运行

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:AGENT_GATEWAY_WS_URL='ws://127.0.0.1:8082/ws'
$env:ROBOT_ADAPTER='device' # mock | device
$env:ACTION_GATEWAY_PORT='8765'
python -m app.main
```

## 实体适配器与时间轴

`StackChanAdapter` 已实现。StackChan 启动独立动作客户端后，连接：

```text
ws://<运行 Robot Bridge 的电脑 IP>:8765
```

适配器只发送 `self.display.set_emotion`、`self.led.set_all`、`self.robot.set_head_angles`、`self.robot.base_move`、`self.robot.base_stop` 和 `self.scene.stop` 等现有高层工具，不发送 PWM、电压或电机寄存器参数。设备执行结果会回到 `experience.action.result`。

`scene.play` 由 Bridge 的时间轴执行器按 `atMs` 调度。相同时间点的底座、屏幕和灯光动作会并行下发；同一通道内仍保持顺序。当前不处理打断优先级，保留既有 `robot.command.stop` 路径。语音仍由主 Xiaozhi 链路在剧本前后播放，不与头部动作强行并行。

Adapter 只接收 `nod`、`wave`、`dance`、`scene.play`、`farm_tend`、`stop` 等语义动作，不接收 PWM、电压或电机寄存器参数。

`scene.play` 的参数是 `sceneId`、`durationMs` 和语义 `steps`，首版最大时长为 60 秒，正式七个场景控制在 4—14 秒。现在 `SceneStepMapper` 已把它编译成当前固件已有的高层工具调用：

| 场景目标 | 当前工具 |
|---|---|
| Emoji / 图标 | `self.display.set_emotion` |
| 灯光效果 | `self.led.set_all` / `self.led.clear` |
| 头部姿态 | `self.robot.set_head_angles` |
| 底座移动 | `self.robot.base_move` / `self.robot.base_stop` |

灯光渐变在 Bridge 侧展开为定时的 `set_all` 调用；点头、摇摆等姿态展开为多次安全角度调用；底座移动没有明确停止时，映射器会在场景结束时自动补 `base_stop`。Mock 会在 `measuredResult.mappedCommands` 中返回完整映射，便于先验收动作序列，再替换实体传输。

固件配置由 `firmware/stackchan-mcp/scripts/build-action-gateway.ps1` 生成，使用 `xiaozhi-action-emoji` 配置：官方语音/OTA 保留，独立动作网关启用，内置 Emoji 保留，Avatar 覆盖层关闭。令牌只从环境变量或脚本参数传入，不写入仓库。

## Mock 阶段验证

```powershell
docker compose -f services/agent-service/docker-compose.yml up -d --build robot-bridge
docker compose -f services/agent-service/docker-compose.yml exec -T robot-bridge python scripts/bridge_smoke.py
```

成功输出 `ROBOT_BRIDGE_SMOKE_OK` 表示 Agent Gateway → Robot Bridge → MockRobotAdapter → `experience.action.result` → 数据服务查询闭环通过。该结果不等同于 StackChan 或 NanoDrive 实机通过。

映射单测：

```powershell
docker compose -f services/agent-service/docker-compose.yml build robot-bridge
docker compose -f services/agent-service/docker-compose.yml run --rm robot-bridge python -m unittest discover -s tests -q
```

实体适配器必须在 StackChan 已连接动作网关后运行；如果设备未连接，结果会明确返回 `device_not_connected`，不会伪报成功。
