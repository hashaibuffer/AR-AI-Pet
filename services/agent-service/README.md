# Agent 服务

## 模块用途

提供 AgentOS、数据、记忆、语音、宠物状态和虚拟生活服务。

## 主责人

B。

## 当前状态

已完成 QwenPaw 2.0.1 的隔离部署与 Web Console 基线验证（2026-08-05）：

- Python 3.12.11 虚拟环境：`.venv/`（不提交）。
- QwenPaw 工作目录：`runtime/qwenpaw/`（不提交）。
- 本地 Console：`http://127.0.0.1:8088/`。
- 健康检查：`GET /api/healthz` 返回 HTTP 200。
- 全局模型配置：`siliconflow-cn/deepseek-ai/DeepSeek-V3.2`；当前 `default` Agent 的按 Agent 覆盖模型为 `siliconflow-cn/Qwen/Qwen3.5-35B-A3B`。
- QwenPaw Web Console 已完成真实模型对话：日志记录 `has_response=True`，并记录了 token usage；此前独立 raw provider 探测得到的 402 不能代表 Web Console 会话结果。
- QwenPaw 自带工作区初始化已完成：Web 会话实际读写了 `SOUL.md`、`PROFILE.md`，并调用过内置 `Read`、`Edit`、`Glob`、`Bash` 等工具。
- 以上只证明 QwenPaw 自身的 Web/内置能力；本项目的自定义工具、Agent—宠物状态接口和正式协议仍未实现，不能据此标记项目 Agent 服务或端到端闭环通过。

## 安装或运行方式

在本目录执行以下命令可重建隔离环境（需要 Python 3.12 或其他满足 QwenPaw 要求的 Python 3.11–3.13）：

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe qwenpaw
```

初始化并指定本模块内的运行数据目录：

```powershell
$env:QWENPAW_WORKING_DIR = (Join-Path (Get-Location) 'runtime\qwenpaw')
$env:QWENPAW_SECRET_DIR = (Join-Path (Get-Location) 'runtime\qwenpaw.secret')
.venv\Scripts\qwenpaw.exe init --defaults --accept-security
```

启动 Console：

```powershell
.venv\Scripts\qwenpaw.exe app --host 127.0.0.1 --port 8088
```

验证：

```powershell
.venv\Scripts\qwenpaw.exe doctor
curl.exe http://127.0.0.1:8088/api/healthz
```

密钥只写入 QwenPaw 的 secret 目录或本地环境变量，不得提交到 Git。模型可用性必须单独记录，不能由 Console/healthz 的通过替代。

## 配置入口

待负责人补充。密钥只能放在被忽略的本地环境文件中。

## 依赖的协议

跨端事件和状态以 [`packages/protocol/`](../../packages/protocol/) 为准。

## 验证方式

按 [`docs/06-开源项目验证清单.md`](../../docs/06-开源项目验证清单.md) 和 [`docs/07-测试与Demo验收.md`](../../docs/07-测试与Demo验收.md) 记录结果。

## 已知问题

QwenPaw 与 AgentScope 尚未完成限时二选一；QwenPaw 的项目自定义工具扩展尚未验证；`packages/protocol/` 的 Agent—宠物状态接口尚未冻结；Mem0 尚未验证。

## MVP 数据服务（当前执行入口）

本阶段先独立跑通 PostgreSQL、Alembic 和 WebSocket 数据服务，不等待 Unity、StackChan、Agent 或 Mem0。

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

本阶段只启动 PostgreSQL 和数据服务。Mem0 仅保留 `memory_jobs`、`memory_refs`、`MemoryProvider` 与 Worker 入口，不启动容器、不调用模型。

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
```

`ws_smoke.py` 使用两个 WebSocket 连接验证农场补算后的主动推送，并验证日程写入、快艇骰子局面保存、游戏结束必填结果、对话写入和版本冲突。`maintenance_smoke.py` 验证日程扫描和对话过期清理。

需要验证空库时，仅针对本地测试数据执行：

```powershell
docker compose down -v
docker compose up --build -d
```

`down -v` 会删除本地 PostgreSQL 测试卷，不要在包含正式数据的环境执行。
