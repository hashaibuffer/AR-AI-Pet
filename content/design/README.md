# 首版内容设计

本目录是内容的可读编辑源；`runtime/` 是 Agent、Unity 和服务端实际读取的稳定 JSON。

## 权威顺序

```text
docs/docx/游戏 GDD → content/design/体验约束 → content/runtime/运行时配置 → 代码表现
```

GDD 决定玩法规则；本目录补充人格、触发、内心 OS 和文案表达。代码不从 Markdown 推断规则，也不让大模型临场修改计分或农场结算。

## 文件入口

| 文件 | 内容 | 运行时文件 |
|---|---|---|
| `personas.md` | 人格边界与三种正式人格 | `personas.json` |
| `proactive-rules.md` | 触发优先级、冷却和主动事件 | `behaviors.json` |
| `inner-os-style.md` | 内心 OS 约束与分层 | `inner-os-lines.json` |
| `copy-production.md` | 文案生产、审核与回退 | `dialogue-lines.json` |
| `game-authority.md` | 快艇骰子与农场的规则边界 | `yahtzee.json`、`farming.json` |
| `virtual-life.md` | 机器人独立生活状态与打扰边界 | `virtual-life.json` |

内容 ID 一旦被代码或数据库引用，不直接改名；修改行为先更新版本，再由 A/B 确认兼容性。
