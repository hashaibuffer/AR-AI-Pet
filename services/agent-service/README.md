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

当前 `conversationId` 用于归档并读取最近短期上下文；长期记忆通过独立 Memory Service 异步处理。Mem0 真实 LLM/Embedding 尚未实测。

QwenPaw 已废弃。`services/db/generated-runtime/qwenpaw/` 只保留历史验证材料，不是当前依赖或运行入口。AgentScope 也不是当前运行时。

## 当前状态

- PostgreSQL、Alembic、WebSocket 数据服务、空库初始化、持久化、健康检查和重启验证已通过。
- StackChan 的 Xiaozhi 会话、Kimito 行为 MCP 和实体头部动作子链路已通过。
- AR-AIPet MCP Hub 已建立首批项目工具；本地 Agent Runtime 的 Mock 文字闭环已通过。真实模型、语音协议网关、真实自托管 Mem0、Beam Pro 数据接入和完整端到端 Demo 尚未完成。
- Mock 长期记忆链路已通过：对话完成事件 → memory_jobs → Memory Worker → memory_refs → memory.search。

## 配置入口

数据服务配置见 [`.env.example`](.env.example)。数据库、模型和 Mem0 的地址或密钥只能放在本地环境变量中。

## 依赖的协议

跨端事件和状态以 [`packages/protocol/`](../../packages/protocol/) 为准。

## 验证方式

按 [`docs/06-开源项目验证清单.md`](../../docs/06-开源项目验证清单.md) 和 [`docs/07-测试与Demo验收.md`](../../docs/07-测试与Demo验收.md) 记录结果。

## 已知问题

`packages/protocol/` 尚未根据真实 Unity 消费字段冻结；真实 LLM/Embedding 尚未实测；StackChan 会话链路尚未自动读取项目长期记忆。

## 当前记忆实现

| 组件 | 版本/入口 | 状态 |
|---|---|---|
| Mem0 OSS Python Library | [`mem0ai==2.0.17`](https://github.com/mem0ai/mem0) | 代码已接入；真实模型凭据缺失，未宣称真实通过 |
| Qdrant | [`qdrant/qdrant:v1.19.0`](https://qdrant.tech/documentation/) | Compose 固定版本、健康检查和持久化卷已通过 |
| Memory Worker | `app/memory/worker.py` | 通过数据服务 WebSocket 领取、完成、失败、忽略和恢复任务 |
| Memory Service | `ws://localhost:8083/ws` | 提供 `memory.health`、`memory.search`；不持有 `DATABASE_URL` |

正式记忆数据流为：

```text
Agent Runtime → Memory Service → Mem0/Qdrant
Memory Worker → DataService WebSocket → PostgreSQL
```

PostgreSQL 保存对话、事件、任务和 `memory_refs`，是业务事实来源；Mem0 只保存经规则筛选的长期语义记忆。`memory-service` 不直接连接 PostgreSQL，Agent 不因记忆服务不可用而停止普通对话或日程工具。

Mem0 的 LLM 与 Embedding 使用独立环境变量配置；`.env.example` 只含空占位符。默认 Compose 使用持久化文件 Mock Provider，便于无外部凭据时验收架构；设置 `MEMORY_PROVIDER=mem0`、`MEM0_ENABLED=true` 后才启用真实 Mem0。

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

当前 Compose 启动 PostgreSQL、数据服务、MCP Hub、本地 Agent Runtime、Qdrant 和 Memory Service。默认 `AGENT_PROVIDER=mock`、`MEMORY_PROVIDER=mock` 仅用于自动化 smoke；正式部署应配置真实模型和 Embedding 接口。

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

```powershell
docker compose exec -T memory-service python scripts/memory_health.py
python scripts/memory_smoke.py
```

`memory_smoke.py` 验证偏好对话产生任务、Worker 写入 Mock 记忆、`memory_refs` 生成、`conversation.get` 顺序和 Agent 跨会话检索。真实 Mem0 需要可用的 LLM 与 Embedding 凭据；本环境未提供，因此真实 Mem0 仍是待验证项。

`memory_health.py` 同时检查 WebSocket 响应的顶层 `status` 和 `payload.providerStatus`。默认 Mock Provider 正常时均为 `ok`；启用但初始化失败的真实 Mem0 返回 `degraded`，容器进程仍可运行但健康检查会失败。

最近短期上下文验证：

```powershell
docker compose exec -T agent-runtime python scripts/conversation_recent_smoke.py
```

该脚本验证 `conversation.get` 只返回最新 N 条消息，并按时间正序交给 Agent。

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
