# Robot Bridge

Robot Bridge 是 Agent Gateway 与实体设备之间的动作执行边界。

当前实现是 `MockRobotAdapter`，用于先验证：

```text
Agent Gateway
→ experience.event
→ Robot Bridge
→ 语义动作执行
→ experience.action.result
→ Agent Gateway / PostgreSQL
```

Bridge 不连接 PostgreSQL，不运行模型，也不决定日程、农场或游戏规则。它只消费高层动作意图，并把执行结果回传。`stop`、断线和事件取消会取消正在执行的 Mock 动作。

## 启动

在 `services/agent-service` 下启动全部服务：

```powershell
docker compose up -d --build robot-bridge
```

默认连接 `ws://agent-runtime:8082/ws`，设备 ID 为 `mock-robot`。

## 本机运行

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:AGENT_GATEWAY_WS_URL='ws://127.0.0.1:8082/ws'
python -m app.main
```

## 替换为实体适配器

后续保留 `RobotBridge` 的 WebSocket和动作结果协议，只替换 `MockRobotAdapter`：

- `StackChanAdapter`：语音、表情、灯光、转头、舞蹈。
- `BaseAdapter`：移动、停止、底座状态和距离结果。

Adapter 只接收 `nod`、`wave`、`dance`、`scene.play`、`farm_tend`、`stop` 等语义动作，不接收 PWM、电压或电机寄存器参数。

`scene.play` 的参数是 `sceneId`、`durationMs` 和语义 `steps`。现在 `SceneStepMapper` 已把它编译成当前固件已有的高层工具调用：

| 场景目标 | 当前工具 |
|---|---|
| Emoji / 图标 | `self.display.set_emotion` |
| 灯光效果 | `self.led.set_all` / `self.led.clear` |
| 头部姿态 | `self.robot.set_head_angles` |
| 底座移动 | `self.robot.base_move` / `self.robot.base_stop` |

灯光渐变在 Bridge 侧展开为定时的 `set_all` 调用；点头、摇摆等姿态展开为多次安全角度调用；底座移动没有明确停止时，映射器会在场景结束时自动补 `base_stop`。Mock 会在 `measuredResult.mappedCommands` 中返回完整映射，便于先验收动作序列，再替换实体传输。

当前实体传输仍未接通：`voice-emoji` 固件已经提供本地 `self.display.set_emotion`、灯光、舵机和 NanoDrive 工具，但该配置不启动独立动作 WebSocket。后续 `StackChanAdapter` 只需要消费同一组 `DeviceCommand`，不需要修改场景或 Agent 接口。

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
