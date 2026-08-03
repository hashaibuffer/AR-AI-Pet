# 内容交付

## 模块用途

本目录保存 C 主责的人格、规则、交互体验、数值、文案和正式资源。

## 主责人

C。A、B确认内容能否由各自模块实现和读取。

## 当前状态

交付格式已定义；具体规则和资源待 C 提交。

## 文件格式

- Markdown：规则、人格、交互流程和体验说明的编辑源。
- XLSX：游戏数值、文案、状态和映射的编辑源，不能作为程序唯一数据源。
- CSV 或 JSON：与 Markdown/XLSX 在同一 PR 成对交付，供程序运行时读取。
- PNG、SVG、音频、模型：正式资源。

运行时文件固定放在 `content/runtime/`，随实际内容任务创建，不预先提交空文件：

- `pet-personality.json`
- `yahtzee.json`
- `farming.json`
- `virtual-life.json`
- `emotion-actions.json`
- `interaction-lines.json`
- `resources.json`：正式资源清单

A、B 的运行时代码只读取 CSV 或 JSON，不直接读取 Markdown 或 XLSX。

## 资源要求

每项资源必须有稳定的英文 `resourceId`，并写入 `content/runtime/resources.json`。规则、文案和映射通过 `resourceId` 引用资源；代码不能依赖可随意修改的中文文件名。

交付时注明用途、版本和是否可直接进入 Demo。尚未确认的内容标记为“待负责人确认”。

## 安装或运行方式

无独立运行命令。Markdown/XLSX 到 CSV/JSON 的导出方式待 C 与使用方确认。

## 配置入口

运行时入口为 `content/runtime/`；文件内容随对应任务补充。

## 依赖的协议

涉及跨端状态与事件时引用 [`packages/protocol/`](../packages/protocol/)。

## 验证方式

A、B验证程序可读取的 CSV 或 JSON；C验证规则、文案和资源表现。

## 已知问题

当前没有正式规则、内容数据或资产，不应由开发人员自行补写。
