# Agent 与数据服务

## 模块用途

提供项目业务数据、虚拟生活、日程、游戏存档、MCP 工具和本地 Agent Runtime。当前先支持文字输入；语音协议网关属于后续工作。

## 主责人

B。

## 当前架构

- **本地 Agent Runtime**：负责文字会话、模型调用、MCP 工具编排和对话落库。
- **Xiaozhi AI.AGENT / StackChan 固件**：继续提供设备语音和实体能力；当前不作为本地文字闭环的运行时。
- **Kimito 行为层**：负责表情、头部动作和陪伴反馈，不保存业务状态。
- **数据服务**：唯一负责 PostgreSQL 业务事实、虚拟生活、日程、游戏存档和记忆任务。
- **MCP Hub**：通过 `DataServiceClient` 调用数据服务 WebSocket，不持有数据库连接；首批状态与日程工具已经通过真实 MCP 客户端验证。

QwenPaw 已废弃。`services/db/generated-runtime/qwenpaw/` 只保留历史验证材料，不是当前依赖或运行入口。AgentScope 也不是当前运行时。

## 当前状态

- PostgreSQL、Alembic、WebSocket 数据服务、空库初始化、持久化、健康检查和重启验证已通过。
- StackChan 的 Xiaozhi 会话、Kimito 行为 MCP 和实体头部动作子链路已通过。
- AR-AIPet MCP Hub 已建立首批项目工具；本地 Agent Runtime 的 Mock 文字闭环已通过。真实模型、语音协议网关、自托管 Mem0、Beam Pro 数据接入和完整端到端 Demo 尚未完成。

## 配置入口

数据服务配置见 [`.env.example`](.env.example)。数据库、模型和 Mem0 的地址或密钥只能放在本地环境变量中。

## 依赖的协议

跨端事件和状态以 [`packages/protocol/`](../../packages/protocol/) 为准。

## 验证方式

按 [`docs/06-开源项目验证清单.md`](../../docs/06-开源项目验证清单.md) 和 [`docs/07-测试与Demo验收.md`](../../docs/07-测试与Demo验收.md) 记录结果。

## 已知问题

`packages/protocol/` 尚未根据真实 Unity 消费字段冻结；真实模型和语音协议网关尚未接入；Mem0 尚未接入；StackChan 会话链路尚未自动读取项目长期记忆。

## MVP 数据服务（已跑通）

PostgreSQL、Alembic 和 WebSocket 数据服务已在不依赖 Unity、StackChan、Agent 或 Mem0 的条件下独立跑通。

### 运行

需要 Docker Desktop。在本目录执行：

```powershell
docker compose up --build -d
```

服务启动时会自动执行 Alembic 迁移并创建固定用户、固定宠物和 `pet`、`home`、`farm` 默认状态。

WebSocket 地址：

```text
ws://localhost:8080/ws
```

### 试运行协议

`contracts/` 是服务内试运行协议，当前未冻结。固定消息示例见 [`contracts/ws-message-examples.json`](contracts/ws-message-examples.json)，说明见 [`contracts/README.md`](contracts/README.md)。A 接入后，根据真实 Unity 字段再迁移到 `packages/protocol/`。

### 本地验收

```powershell
docker compose exec data-service python scripts/ws_smoke.py
```

成功输出 `WS_SMOKE_OK` 表示已验证：WebSocket 连接、数据库读写、农场时间补算、日程、骰子存档、对话原文和 `expectedRevision` 冲突响应。

### 数据库迁移

```powershell
docker compose exec data-service alembic current
docker compose exec data-service alembic history
```

当前 Compose 启动 PostgreSQL、数据服务、MCP Hub 和本地 Agent Runtime。默认 `AGENT_PROVIDER=mock` 仅用于自动化 smoke；正式部署应配置 `AGENT_PROVIDER=openai` 和外部 OpenAI-compatible 接口。Mem0 已预留 `memory_jobs`、`memory_refs`、`MemoryProvider` 与 Worker 入口，仍不在本次边界内。

## 本地环境与最小测试

首次运行可先复制环境样例：

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

服务内后台循环会按 `FARM_TICK_SECONDS` 执行三项工作：补算农场并统一推送 `farm.state.changed`、扫描到期日程并推送 `schedule.reminder`、删除超过 7 天的对话原文并同步 `message_count`。

最小验证：

```powershell
python -m compileall -q app migrations scripts
docker compose exec -T data-service python scripts/ws_smoke.py
docker compose exec -T data-service python scripts/maintenance_smoke.py
docker compose exec -T data-service alembic current
docker compose restart data-service
docker compose exec -T data-service python scripts/ws_smoke.py
python scripts/agent_smoke.py
```

`ws_smoke.py` 使用两个 WebSocket 连接验证农场补算后的主动推送，并验证日程写入、快艇骰子局面保存、游戏结束必填结果、对话写入和版本冲突。`maintenance_smoke.py` 验证日程扫描和对话过期清理。

`agent_smoke.py` 连接 `ws://localhost:8082/ws`，使用默认 Mock Provider 验证文字会话、日程工具调用、工具错误反馈和同一会话落库；真实模型需单独设置 `AGENT_PROVIDER=openai` 并提供兼容接口配置。

需要验证空库时，仅针对本地测试数据执行：

```powershell
docker compose down -v
docker compose up --build -d
```

`down -v` 会删除本地 PostgreSQL 测试卷，不要在包含正式数据的环境执行。

## AR-AIPet MCP Hub

正式数据流为：

```text
MCP Hub
  → DataServiceClient
  → WebSocket 数据服务
  → PostgreSQL
```

MCP Hub 不导入 `app.server`、`app.db`、`app.farm`，也不持有 `DATABASE_URL`。本地 Agent Runtime 通过 MCP Hub 获取工具，并通过数据服务保存用户和助手原文。当前只暴露四个首版工具：

| 工具 | 用途 |
|---|---|
| `system.health` | 确认服务和单用户数据可用 |
| `pet.state.get` | 读取宠物、家园或自主农场状态 |
| `schedule.list` | 查询有效日程 |
| `schedule.upsert` | 新建或更新日程 |

启动后地址为：

```text
http://localhost:8081/mcp
```

本地验证：

```powershell
docker compose up --build -d
docker compose exec -T mcp-hub python scripts/mcp_smoke.py
```

成功输出 `MCP_SMOKE_OK` 代表 MCP Hub → DataServiceClient → WebSocket 数据服务 → PostgreSQL 闭环通过；`AGENT_SMOKE_OK` 代表本地文字 Agent → MCP 工具 → 数据服务 → PostgreSQL → Agent 回复闭环通过。真实模型、语音、Mem0、机器人、底座和 Unity 仍需单独验收。
