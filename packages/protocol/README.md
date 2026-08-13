# 跨端协议

本目录是 Agent、Unity/XREAL、StackChan 和底座之间事件与动作消息的单一事实来源。

## 当前状态

Agent 体验编排相关协议已冻结到 `schemas/`；`examples/` 是可读样例。Python Agent 运行时直接加载这些 JSON Schema 校验，不再维护第二套手写字段规则。

当前版本为 `0.1`。新增字段必须兼容旧消费者；破坏性变更需要提升协议版本并同时更新 Schema、样例、Mock 和测试。

## 文件入口

- `schemas/`：正式 JSON Schema。
- `examples/`：与 Schema 同版本的有效消息样例。
- `mocks/`：尚未建立独立目录；当前 Mock 客户端在 `services/agent-service/scripts/mock_clients.py`。

## 关键消息

- `agent-turn-result`：Agent 的文字结果、内心 OS 和工具摘要。
- `experience-event`：一次可投递给 Unity、机器人和 App 的体验事件。
- `action-result`：设备动作的 `accepted → started → dispatched/completed/failed/timeout/cancelled` 生命周期；`dispatched` 只表示真实网关已接收写入，不表示实体动作已完成。
- `sensor-observation`：带真实来源的传感器观察。

语义动作只描述 `dance`、`wave`、`farm_tend`、`stop` 等能力，不暴露 PWM、电压或电机细节。

`experience-event.xr.expression` 是人格表现的统一结果，包含语义情绪、表情名、Emoji 和强度。Unity/XREAL 消费该字段；机器人动作参数只接收同一事件派生出的语义情绪和表情名，具体屏幕与舵机映射由 Robot Bridge/固件负责。

## 验证

在 Agent 服务目录运行：

```text
python -m unittest discover -s tests -v
python -m json.tool ../../packages/protocol/examples/agent-turn-result.json
```

当前 Schema/Mock 验证不等于 Unity/XREAL、StackChan、NanoDrive 实机验收。

## 当前交接边界

- `experience-event.xr.displayActionId` 只用于 Unity/XR 显示确认，机器人动作使用独立 ID。
- 快艇骰子的规则、骰子和计分以 Unity 为权威；服务只保存 Unity 快照。
- `robot.command.stop` 必须经 Agent Gateway 交给 Robot Bridge；数据库取消记录不能代替设备停止。
