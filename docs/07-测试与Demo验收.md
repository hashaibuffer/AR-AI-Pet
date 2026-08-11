# 测试与 Demo 验收

状态和证据或问题为空，表示待验证；只记录实际运行结果。延迟和性能指标统一在实测后冻结。

| 场景                         | 主责人   | 通过标准                              | 状态  | 证据或问题 |
| -------------------------- | ----- | --------------------------------- | --- | ----- |
| Beam Pro 启动并显示 AR 宠物       | A     | 应用可启动并显示宠物；追踪稳定性与启动耗时待实测后冻结       |     |       |
| 同一事件驱动 AR 宠物与 StackChan 表现 | A、B   | 同一事件 ID 可驱动两端对应表现；端到端延迟待实测后冻结     |     |       |
| 快艇骰子完成一局                   | A、C   | 用户与宠物完成一局，合法操作和计分由游戏系统执行并正确结算     |     |       |
| 种菜完成完整闭环                   | A、B、C | 用户与宠物共同完成播种、照料、成长和收获，状态正确推进并保存    |     |       |
| 语音交互完整闭环                   | A、B、C | 完成语音输入、Agent 回答、字幕、播放和打断；延迟待实测后冻结 |     |       |
| NanoDrive 基础移动与保护          | B     | 完成基础移动、停止、指令超时停止和断连保护             |     |       |
| 服务或设备重启后的状态恢复              | A、B   | 重启后恢复约定的宠物、游戏、虚拟生活和设备状态，不产生重复事件   |     |       |
| 完整 Demo 连续运行三次             | B     | 按冻结脚本连续完成三次，不出现阻塞演示的问题            |     |       |

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
| MCP Hub—PostgreSQL | 通过（数据工具子链路） | `system.health`、`pet.state.get`、`schedule.list`、`schedule.upsert` 经真实 MCP 客户端通过，输出 `MCP_SMOKE_OK`。 |
| MCP Hub 启动门槛 | 通过 | data-service 和 mcp-hub 均通过 WebSocket/MCP healthcheck 后进入 healthy。 |
| 本地 Agent Runtime—MCP—数据服务 | 通过（Mock闭环） | `AGENT_SMOKE_OK` 已验证文字请求、日程读写、工具错误反馈和对话落库；真实模型与语音分别记录，本次不包含语音。 |
| Xiaozhi Agent—AR-AIPet MCP Hub | 待验证 | Hub 已可运行，但尚未挂载到当前 Xiaozhi Agent 配置并完成语音工具调用。 |
| 触摸 PTT | 通过（当前产品子链路） | LCD 触摸可开始/停止手动发言，自动 Xiaozhi 会话轮次仍由会话状态机所有。 |
| StackChan—NanoDrive 串口 | 待验证 | NanoDrive 实物、串口运动指令和安全停止尚未实测。 |
| 完整 AR—Agent—机器人端到端闭环 | 待验证 | 当前只通过 StackChan 子链路，不得据此宣称完整闭环通过。 |
| 完整 Demo 连续运行三次 | 待验证 | 尚未按冻结 Demo 脚本完成三次连续验收。 |
