# 跨端协议

## 模块用途

本目录是 XR 客户端、Agent 服务、StackChan 和 NanoDrive 之间跨端协议的唯一事实来源。说明文档只能引用这里的定义。

## 主责人

每类协议由对应模块主责人提出，受影响人员确认。责任与冻结阶段见 [`docs/04-A-B接口协议.md`](../../docs/04-A-B接口协议.md)。

## 当前状态

目录结构与消息建议已准备；正式协议均为“Day 1 待确认”，尚未冻结。

## 通用消息结构建议

以下字段只是一份 Day 1 待确认的最小建议：

```text
version
messageId
timestamp
source
type
payload
```

示例（Day 1 待确认）：

```json
{
  "version": "0.1",
  "messageId": "evt-001",
  "timestamp": "2026-08-03T09:00:00Z",
  "source": "xr-client",
  "type": "game.action.requested",
  "payload": {
    "action": "roll"
  }
}
```

字段命名、必填性、错误结构和版本策略由 A、B、C 在 Day 1 按实际使用方确认。

## 安装或运行方式

待负责人根据最终协议实现方式补充。

## 配置入口

待负责人补充。

## 验证方式

每类协议至少提供一个示例和一个 Mock，由实际使用方完成解析验证。具体命令待负责人补充。

## 已知问题

当前只有消息结构建议，没有已冻结的代码定义。变更时必须同步协议、示例、Mock和使用方。
