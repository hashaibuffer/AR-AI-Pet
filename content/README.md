# 内容交付

## 模块用途

本目录保存 C 主责的人格、规则、交互体验、数值、文案和正式资源。

## 主责人

C。A、B确认内容能否由各自模块实现和读取。

## 当前状态

首版正式人格、触发规则、内心 OS、快艇骰子与农场运行时基线已建立，位于 `design/` 与 `runtime/`。C 后续仍可按同一格式修订内容，但不需要等待内容文件才能启动 Agent Mock 闭环。

## 文件格式

- Markdown：规则、人格、交互流程和体验说明的编辑源。
- XLSX：游戏数值、文案、状态和映射的编辑源，不能作为程序唯一数据源。
- CSV 或 JSON：与 Markdown/XLSX 在同一 PR 成对交付，供程序运行时读取。
- PNG、SVG、音频、模型：正式资源。

运行时文件固定放在 `content/runtime/`：

| 文件 | 用途 |
|---|---|
| `personas.json` | 正式人格与行为权重，供 PersonaLoader 读取 |
| `behaviors.json` | 触发条件、优先级、冷却与行为意图 |
| `dialogue-lines.json` | 口播文案及人格变体 |
| `inner-os-lines.json` | XR/Beam Pro 内心 OS 文案及约束 |
| `emotion-actions.json` | 情绪、语义动作与 XR 表现映射 |
| `yahtzee.json` | 《六面星河》固定规则与 AI 难度边界 |
| `farming.json` | 《一寸春》回合结算与机器人自主农场规则 |
| `virtual-life.json` | 机器人独立生活状态与主动活动 |
| `virtual-life.json` | 家园/生活扩展配置（接入后新增） |
| `resources.json` | 正式资源清单（接入资产后新增） |

A、B 的运行时代码只读取 CSV 或 JSON，不直接读取 Markdown 或 XLSX。

## 资源要求

每项资源必须有稳定的英文 `resourceId`，并写入 `content/runtime/resources.json`。规则、文案和映射通过 `resourceId` 引用资源；代码不能依赖可随意修改的中文文件名。

交付时注明用途、版本和是否可直接进入 Demo。尚未确认的内容标记为“待负责人确认”。

## 安装或运行方式

无独立运行命令。Agent 服务通过 `PERSONA_ROOT` 读取 `runtime/`；内容 JSON 必须可被 UTF-8 解析。编辑源可以是 Markdown/XLSX，但不能作为程序唯一数据源。

## 配置入口

运行时入口为 `content/runtime/`；文件内容随对应任务补充。

## 依赖的协议

涉及跨端状态与事件时引用 [`packages/protocol/`](../packages/protocol/)。

## 验证方式

A、B验证程序可读取的 CSV 或 JSON；C验证规则、文案和资源表现。

## 运行时约束

- A、B 只读取 `runtime/`，不从 Markdown/XLSX 推断规则。
- 规则计算、农场结算和骰子计分由确定性代码负责；Agent 不能覆盖结果。
- 文案缺失时使用固定 fallback；动作能力不足时返回失败，不伪造完成。
- 资源尚未提交时，运行时可使用文本或占位表现，但稳定 `resourceId` 不能省略。
