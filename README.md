# AR&AIPet

AR&AIPet 是由 AgentOS、StackChan、XREAL 和 Beam Pro 组成的虚实融合 AI 宠物项目。

## 当前分工

| 负责人 | 职责 |
|---|---|
| B | 项目主要负责人，同时负责 AgentOS、数据、StackChan 和 NanoDrive。 |
| C | 游戏与交互体验主要负责人，同时负责人格、规则、内容、美术和比赛材料。 |
| A | XR 客户端负责人，负责 Beam Pro、XREAL、Unity、AR 和游戏实现。 |

## 项目目录

```text
apps/
├─ deck-site/      已归档展示 Deck
└─ xr-client/      A 负责的正式 Unity/XREAL 客户端
services/
└─ agent-service/  B 负责
firmware/
├─ stackchan/      B 负责
├─ espnow-controller/  B 负责的实体遥控器
└─ nanodrive/      B 负责
content/           C 负责
competition/       C 负责
packages/protocol/ 按模块主责定义，受影响人员确认
```

## 从哪里开始

| 需要确认什么 | 先读哪里 |
|---|---|
| 产品范围、什么不做 | [项目 PRD](docs/01-项目PRD.md) |
| 已确定的技术决策、硬件边界 | [技术架构与可行性方案](docs/02-技术架构与可行性方案.md)、[硬件与底座方案](docs/05-硬件与底座方案.md) |
| 当前阶段、谁做什么、产出什么 | [两周开发计划](docs/03-两周开发计划.md) |
| 当前比赛版本实现边界与执行顺序 | [首版实现边界与技术决策](docs/08-首版实现边界与技术决策.md) |
| 跨端状态、消息和 Mock | [接口协议](docs/04-A-B接口协议.md)、[`packages/protocol/`](packages/protocol/) |
| 开源项目是否已验证 | [开源验证清单](docs/06-开源项目验证清单.md) |
| 当前真实运行结果和 Demo 问题 | [测试与 Demo 验收](docs/07-测试与Demo验收.md) |
| 某个模块如何运行 | 对应模块 README（见下方） |

> 范围以 PRD 为准；技术决策以技术架构和硬件方案为准；当前执行以开发计划为准；字段与版本以 `packages/protocol/` 为准；实际状态以验证清单和验收表为准。

协作与 PR 规则见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 正式开发入口

- 正式 XR 客户端：[apps/xr-client/](apps/xr-client/)
- Agent 服务：[services/agent-service/](services/agent-service/)
- StackChan 固件：[firmware/stackchan/](firmware/stackchan/)
- StackChan 官方来源锁定：[firmware/stackchan/source.lock.json](firmware/stackchan/source.lock.json)
- ESP-NOW 遥控器：[firmware/espnow-controller/](firmware/espnow-controller/)
- NanoDrive 固件：[firmware/nanodrive/](firmware/nanodrive/)
- 跨端协议：[packages/protocol/](packages/protocol/)

## 归档与参考

- 已归档展示 Deck：[apps/deck-site/](apps/deck-site/)。保留源代码、构建说明和 CI；后续仅修复展示故障，不扩展产品功能。

## 当前状态

StackChan 基础固件和实体子链路已有独立验证记录；PostgreSQL、Alembic、WebSocket 数据服务和 MCP Hub 已完成独立验收。当前项目自有本地 Agent Runtime 的 Mock 文字输入与 MCP 工具调用闭环已通过。QwenPaw 已废弃；官方 Mooncake 源码与 Scheme B 参考固件已分开记录，当前设备固件与官方源码的完全对应仍待补齐，边界见开源验证清单和固件 README。

本地 Agent 的 Mock 记忆链路已通过。Unity 已完成官方 XREAL SDK 3.1.0 安装、Unity 脚本编译，以及 PC Play Mode 的 Agent Gateway WebSocket、`ExperienceEvent`、人格表情/Emoji/内心 OS 和显示结果回传闭环。StackChan—BLE—NanoDrive v0.9 的基础移动、停止和超时保护已完成实体验收；Robot Bridge 的真实 StackChan WebSocket Adapter 已完成软件映射和假网关测试，真实实体动作仍需现场确认。Beam Pro/XREAL 实机、真实模型、真实 Mem0、语音协议网关，以及完整 AR—Agent—机器人闭环仍待验证。具体证据和边界见 [XR 客户端 README](apps/xr-client/README.md)、[NanoDrive 联调记录](docs/11-NanoDrive联调记录.md) 和 [测试与 Demo 验收](docs/07-测试与Demo验收.md)。

当前已增加可选统一部署入口：`services/agent-service` 的 `unified` profile 将 Agent、数据服务、记忆服务、MCP 兼容入口和设备会话收敛到同一局域网服务；软件层已通过 Mock 设备、外部 `/mcp` 和 Scheme B 兼容 smoke，实体设备仍按实测结果更新。
