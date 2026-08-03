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
├─ deck-site/      当前 Web 展示 Deck
└─ xr-client/      A 负责的正式 Unity/XREAL 客户端
services/
└─ agent-service/  B 负责
firmware/
├─ stackchan/      B 负责
└─ nanodrive/      B 负责
content/           C 负责
competition/       C 负责
packages/protocol/ 按模块主责定义，受影响人员确认
```

## 开发与文档入口

- [项目 PRD](docs/01-项目PRD.md)
- [技术架构与可行性方案](docs/02-技术架构与可行性方案.md)
- [两周开发计划](docs/03-两周开发计划.md)
- [接口协议](docs/04-A-B接口协议.md)
- [开源验证清单](docs/06-开源项目验证清单.md)
- [测试与 Demo 验收](docs/07-测试与Demo验收.md)
- [协作规范](CONTRIBUTING.md)

## 入口

- Web 展示 Deck：[apps/deck-site/](apps/deck-site/)
- 正式 XR 客户端：[apps/xr-client/](apps/xr-client/)
- Agent 服务：[services/agent-service/](services/agent-service/)
- StackChan 固件：[firmware/stackchan/](firmware/stackchan/)
- NanoDrive 固件：[firmware/nanodrive/](firmware/nanodrive/)
- 跨端协议：[packages/protocol/](packages/protocol/)

## 当前状态

项目结构和职责已就绪；正式工程实现及开源项目验证均待对应负责人开始。
