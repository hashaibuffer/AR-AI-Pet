# StackChan 项目动作适配器

适配器只提供项目新增的 MCP 动作，不替代 StackChan 官方 Agent、MCP 或 WebSocket 实现。

## MCP 工具

```text
self.robot.play_motion(name)
self.robot.stop_motion()
```

`name` 只允许使用固件中已有的固定动作：`happy`、`robot`、`panic`、`look_around`。

## 通信链路

电脑或 AI.Agent 均通过官方 MCP 调用动作：

```text
电脑 → 官方 WebSocket /ws → McpServer → 本适配器
AI.Agent → McpServer → 本适配器
```

官方 WebSocket 源码位于 StackChan 工程的 `xiaozhi-esp32/main/boards/otto-robot/`，
项目只在 StackChan 的 CMake 和 HAL 启动流程中接入它，不另定义控制协议。
