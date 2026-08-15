# 测试与 Demo 验收

## 本轮阶段验收记录（2026-08-12）

| 项目 | 状态 | 证据与边界 |
| --- | --- | --- |
| XREAL SDK 3.1.0 本机安装 | 通过 | `apps/xr-client/Project/Packages/com.xreal.xr/` 已由官方压缩包安装；包体不提交仓库，其他机器执行安装脚本。 |
| Unity 2022.3.62f3 脚本编译 | 通过 | 批处理导入完成，无 C# 编译错误。 |
| Unity PC Play Mode → Agent Gateway WebSocket | 通过（PC Mock） | `Project/Library/AgentPlayModeSmokeResult.json` 为 `passed=true`；覆盖订阅、聊天、ExperienceEvent、显示层 ActionResult。 |
| Agent Gateway → Mock Robot Bridge | 通过（Mock） | `ROBOT_BRIDGE_SMOKE_OK`；覆盖语义动作执行、结果回传和数据服务查询。 |
| Beam Pro Android 运行与 XREAL 实机显示 | 待验证 | Windows Editor 的 `XREALXRPlugin` 缺失警告属于预期限制，不替代 Android/眼镜实机验收。 |
| Robot Bridge → StackChan / NanoDrive 实体动作 | 待验证 | 当前仍使用 MockRobotAdapter；实体适配器和底座安全链路另行验收。 |

状态和证据或问题为空，表示待验证；只记录实际运行结果。延迟和性能指标统一在实测后冻结。

| 场景                         | 主责人   | 通过标准                              | 状态  | 证据或问题 |
| -------------------------- | ----- | --------------------------------- | --- | ----- |
| Beam Pro 启动并显示 AR 宠物       | A     | 应用可启动并显示宠物；追踪稳定性与启动耗时待实测后冻结       |     |       |
| 同一事件驱动 AR 宠物与 StackChan 表现 | A、B   | 同一事件 ID 可驱动两端对应表现；端到端延迟待实测后冻结     |     |       |
| 快艇骰子完成一局                   | A、C   | 用户与宠物完成一局，合法操作和计分由游戏系统执行并正确结算     |     |       |
| 种菜完成完整闭环                   | A、B、C | 用户与宠物共同完成播种、照料、成长和收获，状态正确推进并保存    |     |       |
| 语音交互完整闭环                   | A、B、C | 完成语音输入、Agent 回答、字幕、播放和打断；延迟待实测后冻结 |     |       |
| NanoDrive 基础移动与保护          | B     | 完成基础移动、停止、指令超时停止和断连保护             | 通过（实体） | StackChan—BLE—NanoDrive v0.9；前后左右、松手停止与超时停车由现场确认。 |
| 服务或设备重启后的状态恢复              | A、B   | 重启后恢复约定的宠物、游戏、虚拟生活和设备状态，不产生重复事件   |     |       |
| 完整 Demo 连续运行三次             | B     | 按冻结脚本连续完成三次，不出现阻塞演示的问题            |     |       |

## 本轮动作网关固件烧录记录（2026-08-15）

| 项目 | 状态 | 证据与边界 |
| --- | --- | --- |
| Robot Bridge 动作网关地址 | 通过（地址确认） | 本机 WLAN IPv4 为 `192.168.50.133`；动作网关监听 `0.0.0.0:8765`，`Test-NetConnection 192.168.50.133 -Port 8765` 通过。 |
| 独立动作网关固件构建 | 通过 | 固件包含 `0014-richer-scene-timelines.patch`，ESP-IDF `v5.5.4` 构建成功；`xiaozhi.bin` 为 `0x343fb0`，应用分区约 17% 空闲，SHA256 为 `8847583f89920580153141622f83d223365b955a9f3afa5e8228f1a5ae8be676`。 |
| 固件动作网关配置 | 通过（构建配置） | `CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL="ws://192.168.50.133:8765"`；未写入动作网关 token。 |
| COM7 烧录与校验 | 通过 | `idf.py -p COM7 flash` 完成，bootloader、应用、分区表、OTA 数据和 assets 均写入并通过 SHA 校验，设备已硬复位。 |
| 烧录后设备启动 | 通过（启动子链路） | 串口观察到 StackChan 外设初始化、NanoDrive BLE `FFE0/FFE1` 连接、Wi-Fi 连接 `hashai` 并获取 `192.168.50.213`；动作 MCP 工具已注册。 |
| Robot Bridge—StackChan 动作调用 | 待验证 | 已观察到设备向 `192.168.50.133:8765` 发起连接；固定剧本、表情、灯光、舵机和底座动作的真实调用与结果回传仍需单独执行。 |

## StackChan 实机子项

以下只记录 StackChan 自身及其当前语音链路的实机结果，不代表完整 AR、Agent 或底座闭环通过。

| 子项 | 状态 | 证据或边界 |
| --- | --- | --- |
| ESP-IDF 5.5.4 + ESP32-S3 全量构建 | 通过 | 本地源码构建目录为 `D:\sc\firmware`；上游固定提交 `b72b3ede38b32d54f0b6ba51c62cfcef2ec3ae1e`。 |
| COM7 烧录与串口启动 | 通过 | `idf.py -p COM7 flash` 和串口监控已完成。 |
| 屏幕、摄像头、触摸、IMU、RTC、三麦、双舵机初始化 | 通过 | 启动日志中完成对应外设初始化。 |
| 中文唤醒与 Xiaozhi 云端对话 | 通过（当前产品基线） | 普通 WakeNet `wn9_nihaoxiaozhi_tts`、固件 `zh-cn`、绑定 Agent `language=zh`；真机无需英文前导即可直接中文提问，并能继续中文追问。 |
| MultiNet / AEC 比较 | 不进入当前烧录门槛 | 普通 WakeNet A 已满足用户体验底线；MultiNet 和显式 AEC 配置保留为出现明确回归时的诊断变体。启动日志已观察到默认 AFE `AEC(SR_HIGH_PERF)` 路径。 |
| Xiaozhi 联网、语音上传和服务器回答 | 通过（StackChan × Xiaozhi 子项） | 主语音 WebSocket 负责 ASR、会话和自动轮次；该结果仍不等于 AR、Unity、底座完整端到端闭环。 |
| 当前 4 MB assets 分区 | 通过 | 当前应用分区约 27% 空闲，assets 分区约 45% 空闲；早期 8 MB assets 方案仅作历史记录。 |
| 项目 Robot Adapter | 通过（控制动作子集） | 固件 1.4.5、ESP-IDF 5.5.4、COM7；实机验证 `play_motion`、`stop_motion`、`set_head_angles`。 |
| 电脑—StackChan 控制 | 通过（StackChan 子链路） | AI.AGENT 启动后，电脑经官方 `ws://192.168.50.213:8080/ws` 发送两轮 MCP 调用，动作与串口日志一致；Beam Pro 接入仍待验证。 |
| Xiaozhi Agent—独立动作 MCP—StackChan | 通过（当前产品子链路） | 用户中文要求摇头后，Agent 调用 `self.robot.set_head_angles`，实机先后执行左右头部动作；动作通道不接管语音会话。 |
| voice-emoji 固件内置七场景播放器 | 通过（编译与注册） | ESP-IDF 5.5.4 构建通过，应用分区约 17% 空闲；COM7 启动日志出现 `Scene playback task ready`，并注册 `self.scene.play` / `self.scene.stop`。 |
| 七个实体小剧场逐场执行 | 待验证 | 固件已刷入，仍需通过语音/Agent 实际触发并观察 Emoji、灯光、舵机和 NanoDrive 时间轴；工具注册不等于动作执行通过。 |
| MCP Hub—PostgreSQL | 通过（数据工具子链路） | `system.health`、`pet.state.get`、`schedule.list`、`schedule.upsert` 经真实 MCP 客户端通过，输出 `MCP_SMOKE_OK`。 |
| MCP Hub 启动门槛 | 通过 | data-service 和 mcp-hub 均通过 WebSocket/MCP healthcheck 后进入 healthy。 |
| 本地 Agent Runtime—MCP—数据服务 | 通过（Mock闭环） | `AGENT_SMOKE_OK` 已验证文字请求、日程读写、工具错误反馈和对话落库；真实模型与语音分别记录，本次不包含语音。 |
| 本地 Agent—短期上下文—Mock记忆 | 通过（Mock闭环） | `MEMORY_SMOKE_OK` 与 `CONVERSATION_RECENT_SMOKE_OK` 已验证 `conversation.get` 只返回最新 N 条并按时间正序返回，以及完成事件、memory_jobs、Worker、memory_refs 和跨会话记忆检索。 |
| Memory Service Provider 健康状态 | 通过（Mock/不可用边界） | `memory_health.py` 同时检查顶层 `status` 与 `providerStatus`；正常 Mock 为 `ok`，模拟不可用 Provider 为 `degraded`，Docker 进程仍存活但健康检查失败。 |
| Memory Service 停机降级 | 通过 | Memory Service 停止时 Agent 仍可完成普通对话和日程，返回 `memoryStatus=unavailable`；恢复后服务重新 healthy。 |
| Memory Worker 失败重试 | 通过（数据服务边界） | 任务失败记录 attempts/next_retry_at，恢复服务后可再次领取并完成；真实 Mem0/Qdrant 故障仍需凭据和实机环境复测。 |
| 真实 Mem0—Qdrant—LLM/Embedding | 待验证 | 当前环境没有真实 LLM 与 Embedding 凭据，不宣称真实 Mem0 已通过。 |
| 正式内容 JSON 加载 | 通过（本地/容器单元测试） | 三种人格、触发规则、口播、内心 OS、情绪动作、快艇骰子和农场配置可被 Agent Runtime 读取；固定文案缺失时有 fallback。 |
| 内容规则与 GDD 对齐 | 通过（静态审查） | 快艇骰子为五骰、双方各 11 回合、每回合最多 3 次投掷；农场含机器人自主小田；真实 Unity 规则执行仍待联调。 |
| Agent 体验编排—PC Unity/Mock Robot Bridge | 通过（分层闭环） | `AGENT_EXPERIENCE_SMOKE_OK`、`UNITY_AGENT_SMOKE_OK`、`ROBOT_BRIDGE_SMOKE_OK` 已分别验证 Persona、ExperienceEvent、PC Unity 显示回传、语义机器人动作和 PostgreSQL 事件落库；该 Agent 链路尚未接入已验收的 StackChan/NanoDrive 实体链路。 |
| Unity 干净环境打开 | 通过（本机） | XREAL SDK 3.1.0 已按脚本安装；Unity 2022.3.62f3 脚本编译通过。官方包体不提交仓库，其他机器需自行安装。 |
| Unity—Agent Gateway WebSocket | 通过（PC Play Mode） | 已验证真实 WebSocket 连接、订阅确认、`ExperienceEvent` 消费、XR `ActionResult` 回传；Beam Pro 仍待验证。 |
| 人格—表情—Emoji—内心 OS | 部分通过（PC Mock） | Unity 已消费统一 `xr.expression`、创建覆盖层并回传显示结果；Emoji 字形、中文字体、空间锚点和 Beam Pro 实机视觉效果仍待验证。 |
| Xiaozhi Agent—AR-AIPet MCP Hub | 待验证 | Hub 已可运行，但尚未挂载到当前 Xiaozhi Agent 配置并完成语音工具调用。 |
| 触摸 PTT | 通过（当前产品子链路） | LCD 触摸可开始/停止手动发言，自动 Xiaozhi 会话轮次仍由会话状态机所有。 |
| StackChan—NanoDrive BLE 透明串口 v0.9 | 通过（实体） | StackChan 连接 `FFE0/FFE1`，遥控器 BASE 模式驱动底座前后左右；松手停止与底座超时停车已现场确认。BLE 暂无设备状态回传。 |
| 完整 AR—Agent—机器人端到端闭环 | 待验证 | 当前只通过 StackChan 子链路，不得据此宣称完整闭环通过。 |
| 完整 Demo 连续运行三次 | 待验证 | 尚未按冻结 Demo 脚本完成三次连续验收。 |
