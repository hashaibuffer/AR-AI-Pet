# WebSocket 试运行协议

本目录只服务于 `agent-service` 首版独立验收，协议状态为“试运行、未冻结”。

A 接入并确认真实 Unity 字段后，再将实际使用的消息迁移到 `packages/protocol/`。本目录不定义 StackChan、NanoDrive 或多人协议。

请求结构：

```json
{
  "requestId": "req-001",
  "type": "state.get",
  "payload": { "domain": "farm" }
}
```

响应结构：

```json
{
  "requestId": "req-001",
  "type": "state.get.result",
  "status": "ok",
  "payload": {}
}
```

`state.put` 必须带 `expectedRevision`。版本冲突时返回 `status: conflict`、`latestRevision` 和 `latestState`。

服务内后台扫描到期日程后推送 `schedule.reminder`；农场无论由后台循环、`bootstrap.get` 还是 `state.get(farm)` 补算，统一推送 `farm.state.changed`。

`game-session.save` 在 `status = completed` 时必须同时提供 `result` 对象和 `endedAt`；`playing` 状态不能提供 `endedAt`。
