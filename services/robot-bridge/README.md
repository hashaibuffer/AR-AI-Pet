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

Adapter 只接收 `nod`、`wave`、`dance`、`farm_tend`、`stop` 等语义动作，不接收 PWM、电压或电机寄存器参数。

## Mock 阶段验证

```powershell
docker compose -f services/agent-service/docker-compose.yml up -d --build robot-bridge
docker compose -f services/agent-service/docker-compose.yml exec -T robot-bridge python scripts/bridge_smoke.py
```

成功输出 `ROBOT_BRIDGE_SMOKE_OK` 表示 Agent Gateway → Robot Bridge → MockRobotAdapter → `experience.action.result` → 数据服务查询闭环通过。该结果不等同于 StackChan 或 NanoDrive 实机通过。
