# StackChan × Kimito × Xiaozhi 正式固件基线

## 作用与边界

本模块固定已经通过真机验收的产品链：

```text
AI.AGENT / Xiaozhi：语音、ASR、会话和自动轮次的唯一所有者
                    │ 主语音 WebSocket
                    ▼
StackChan 实体：麦克风、扬声器、触摸、屏幕、舵机和安全执行
                    ▲
                    │ 本地 MCP 工具
Kimito 行为层：表情、头部动作、陪伴反馈，不接管语音会话
```

Beam Pro、Unity、AR 和独立动作 MCP 网关仍是后续消费者；当前语音演示使用 StackChan 主语音、本地 Emoji/灯光/头部工具，NanoDrive 蓝牙透传和遥控器 BASE 模式已经完成实机闭环。固定剧本不驱动底座。

## 固定来源

机器可读来源见 [`source.lock.json`](source.lock.json)。当前锁定：

- 可获取源码：<https://github.com/lingxin2316/stackchan-mcp/tree/21ab663644d3cc3e24492ec11fd8ef222dc8e24a>
- 上游评审：<https://github.com/kisaragi-mochi/stackchan-mcp/pull/370>
- 源码提交：`21ab663644d3cc3e24492ec11fd8ef222dc8e24a`
- 上游基点：`23792aa3ec00d23a3a86146aafe60f949bb2c4d3`
- 工具链：ESP-IDF `v5.5.4`，ESP32-S3，`stackchan` 板型

在上游 PR 合并前，正式项目以锁定的可获取提交为准；合并后再单独更新锁文件，不跟随分支浮动。

## 新成员复现

### 1. 获取固定源码并运行主机测试

在 AR-AIPet 仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\stackchan-mcp\scripts\bootstrap.ps1
```

脚本会：

1. 克隆公开源码到被忽略的 `firmware/stackchan-mcp/upstream/`；
2. 以 detached HEAD 检出锁定 commit，并核对完整 SHA；
3. 运行固件脚本单元测试；
4. 构建并运行固件主机 CTest。

已有源码目录如果含本地改动，脚本会停止，不会覆盖成员工作。
同一入口也由 `.github/workflows/stackchan-mcp-repro.yml` 在 Windows runner 上执行，持续检查锁定提交仍可获取且 57 个 Python 测试和 17 个固件主机测试可复现。

### 2. 在电脑端选择已验收配置并构建

打开 **ESP-IDF 5.5.4 PowerShell**，在仓库根目录执行：

```powershell
.\firmware\stackchan-mcp\scripts\build-accepted-baseline.ps1 `
  -GatewayUrl "ws://<运行动作网关的电脑IP>:8765/"
```

脚本会拒绝其他 ESP-IDF 版本，然后原样选择：

```text
voice       = xiaozhi-conversational
audio       = wakenet
transport   = xiaozhi-plus-action
firmware    = zh-cn
Agent       = zh
touch PTT   = enabled
```

构建入口会先幂等应用 [`patches/0001-nanodrive-tx-only.patch`](patches/0001-nanodrive-tx-only.patch) 和网关工具映射补丁 [`patches/0002-nanodrive-gateway-tools.patch`](patches/0002-nanodrive-gateway-tools.patch)，再执行完整构建并在被忽略的 `artifacts/local-consistency/` 生成“配置—模型—固件”一致性报告，但不会调用 `flash`、`esptool` 或写入任何分区。

### 主语音 + 官方 OTA/激活 + 内置 Emoji

如果本轮需要恢复官方 Xiaozhi 主语音链路，同时保留 StackChan 本体的 Emoji、灯光、舵机和遥控能力，可执行：

```powershell
.\firmware\stackchan-mcp\scripts\build-voice-emoji.ps1
```

该配置保留官方 OTA/NVS WebSocket、激活流程、唤醒词和语音会话；主会话只注册演示所需的本体工具，可调用 `self.display.set_emotion`（内置 LVGL Emoji）、灯光、舵机，以及 `self.scene.play` / `self.scene.stop`（七个固定实体小剧场）。诊断/维护工具、外部 I²C 和 Port B/C 工具在语音演示配置中关闭，以减少 MCP 工具列表和重连时的 SRAM 峰值；内置 Emoji、LED、头部舵机、顶部触摸、ESP-NOW 遥控和 NanoDrive BLE 保留。本地动作网关地址与令牌为空，不启动第二条动作 WebSocket。`Application::OnIncomingJson` 仍由内置 LVGL Emoji 渲染情绪，Avatar 覆盖层、口型动画和 Avatar MCP 工具在编译期关闭。脚本只配置和构建，不会刷机。

这条配置只证明“主语音 + 本体动作工具 + Emoji + 本地固定场景播放器”基线；它不启动独立动作网关。需要第二条动作 WebSocket 时使用 `build-action-gateway.ps1`；`self.scene.play` 只负责本机时间轴，不代表已经完成 Agent/Beam Pro 的真实下发验收。

#### 演示版方向与控制边界

当前演示配置新增 `0015-demo-direction-and-base-calibration.patch`：

- 语音 Agent 使用 `self.robot.head_pose` 处理抬头、低头、左右看；它把自然语言方向转换为物理方向，避免直接解释舵机正负角度。
- `self.robot.set_head_angles` 保留为低层接口，提示 Agent 优先使用 `head_pose`。
- 演示版不向语音 Agent 注册 `base_move`、`base_drive`、`base_stop`；底座只由实体遥控器控制，避免语音误触发移动。
- 遥控脑袋 yaw 在 StackChan 接收端统一修正一次；舵机底层 `YawDegToPos`、`PitchDegToPos` 不修改。
- 遥控底座降低转向增益，并保留左右轮 trim 参数；trim 初始为 1.000，需在实机直行测试后按偏转方向调整。
- Agent 的固定剧本只调用 Emoji、灯光和脑袋动作，不再调用底座；底座只由实体遥控器控制，避免剧本或语音误触发移动。

本次修改只完成代码和主机测试，方向、直行偏差、左右轮 trim 必须在烧录后按 `docs/07-测试与Demo验收.md` 的实机表格确认，不能把编译通过当作物理方向通过。

## 独立动作网关固件配置

现在需要让 Agent/Robot Bridge 直接调用实体动作时，使用：

```powershell
$env:STACKCHAN_ACTION_GATEWAY_URL = "ws://<运行 Robot Bridge 的电脑 IP>:8765"
$env:STACKCHAN_ACTION_GATEWAY_TOKEN = "" # 可选
.\scripts\build-action-gateway.ps1
```

该配置使用官方 Xiaozhi OTA/NVS 作为主语音连接，另开一条只承载 MCP 动作的 WebSocket；内置 Emoji、顶部触摸、灯光、舵机、ESP-NOW 遥控和 NanoDrive BLE 均保留，Avatar 覆盖层关闭。脚本只构建，不自动刷机。

#### 当前构建基线（2026-08-15）

- 当前固件使用 `0014-richer-scene-timelines.patch` 的七场景时间轴（它覆盖了 `0013` 的中间版本）及 `0015`—`0022` 补丁；已完成 ESP-IDF `v5.5.4` 构建，`xiaozhi.bin` 为 3,285,808 字节，应用分区约 20% 空闲。当前烧录基线为 `xiaozhi-voice-only`，独立动作网关未启用。
- `0016` 将 `CONFIG_STACKCHAN_AGENT_DIAGNOSTIC_TOOLS` 与 `CONFIG_STACKCHAN_AGENT_PERIPHERAL_TOOLS` 在 `xiaozhi-voice-only` 中关闭；`CONFIG_STACKCHAN_AGENT_BASE_TOOLS` 同样关闭。内置 Emoji、LED、头部舵机、顶部触摸、ESP-NOW 遥控和 NanoDrive BLE 不受影响。这样可避免长时间运行或 WebSocket 重连时发送过大的 MCP 工具列表，降低 `esp-aes: Failed to allocate memory` 和 `SSL send failed` 的风险。
- `0017` 保留已保存 Wi-Fi 凭据时的断线重试，不再因连接超时自动进入配网；启动阶段只有长按 2 秒才进入配网。官方 OTA/激活检查失败最多快速重试 3 次，避免长时间阻塞主语音启动；ESP-NOW 遥控和 NanoDrive BLE 延后到激活完成后启动，显示屏仍可按空闲策略变暗但不自动关机。
- `0018` 将主语音 MCP 工具收敛为 `scene.play`、`scene.stop`、`display.set_emotion`、`robot.set_head_angles`、`led.set_color` 五项；关闭通用状态/摄像头/维护工具。NanoDrive BLE 改为首次底座动作时按需启动，扫描去重、缓存上限和扫描任务栈同步收缩，并增加内部 SRAM/PSRAM/最大连续块日志。
- 本次已刷写 COM7 并完成分区校验。启动日志确认检测到 8MB Quad PSRAM；激活后内部 SRAM 约 81KB、PSRAM 约 8.0MB，语音与 ESP-NOW 运行约 45 秒后内部 SRAM 仍约 51.7KB，未再出现 `esp-aes: Failed to allocate memory` 或 `SSL send failed`。本次观察未触发底座动作，因此 NanoDrive BLE 尚未启动，需单独验证首次底座操作。
- 已在 COM7 完成刷写和分区校验，设备自动重启；当前 `CONFIG_STACKCHAN_ACTION_GATEWAY` 未启用，`CONFIG_STACKCHAN_AGENT_BASE_TOOLS` 未启用，底座由实体遥控器控制。
- 只有重新启用独立动作网关配置时，才需要填写运行 Robot Bridge 的电脑 IPv4；固件里的 `127.0.0.1` 只代表机器人自身，不能用于连接电脑，烧录前必须替换。
- 当前电脑 WLAN IPv4 已确认是 `192.168.50.133`，本轮目标地址为：

  ```text
  ws://192.168.50.133:8765
  ```

- 该地址只有在 Robot Bridge 监听 `0.0.0.0:8765` 且电脑与机器人处于同一局域网时有效。烧录前先确认端口：

  ```powershell
  Test-NetConnection 192.168.50.133 -Port 8765
  ```

- 如果电脑重新连网导致 IPv4 变化，必须重新确认地址、重建固件后再烧录；不要把旧地址或 `127.0.0.1` 带入实机。

顶部 Si12T 触摸互动仍在固件中：轻触触发 `surprised` 与 `touch/tap`，滑动/长触发触发 `embarrassed`、头部摇摆与 `touch/stroke`；LCD 触摸 PTT 由 `CONFIG_STACKCHAN_TOUCH_PTT=y` 保留。

### NanoDrive 项目变体

#### NanoDrive BLE 运行路径（2026-08-13）

StackChan BLE 接收端扫描并连接目标 `JDY-23A-BLE`，使用 `FFE0/FFE1`，NanoDrive 侧模块 UART 为 115200。遥控器 BASE 模式经这一路径控制 NanoDrive v0.9，用户已确认前进、后退、左右转向和松手停止符合预期。

正式实现使用 NanoDrive v0.9 行协议：BLE 写入能力由 `NanoDriveBleScanner::SendCommand()` 发送最多 20 字节的换行指令；首次运动或急停后把 `EN:1` 与首条运动命令合并发送，后续直接发送连续差速 `VL:left,right`。方向或明显速度变化立即发送，相同状态按 250 ms 刷新，松手、退出 BASE 或失联发送 `ST`。

模块的 `CONNECTED`、`+DISC:SUCCESS` 等状态文本可能被 v0.9 固件报告为 `ERR:UNKNOWN`，这是透传链路的日志噪声，不是动作失败。底座 2 秒安全超时和每轮动作末尾的 `ST` 必须保留。

旧的 GPIO17 直连 UART 变体仍保留为历史/对照路径，不与当前 BLE 实机验收混用。

- 旧的 GPIO17（Port C 黄线）115200 单向 UART 仅用于历史直连变体；当前已验收的 BLE 路径不使用 StackChan 与底座之间的 UART 线。
- 每次移动先发送 `EN:1`，再发送 `FW`、`BW`、`TL`、`TR` 或 `VL`；停止发送 `ST`，底座看门狗为 2000 ms。
- `self.robot.base_move`、`base_drive`、`base_stop` 返回成功仅表示串口已写入，不代表底座回执。
- 商家单字符 `A/E/Z` 仅保留为 2026-08-12 的 A4950 方向与 BLE 透传基准，不作为当前运行协议。
- GPIO17 被底座占用时，本项目变体不启用 Port C WS2812。

### 3. 绑定成员自己的 Xiaozhi Agent

固件语言 `zh-cn`、WakeNet 模型和云端 Agent `language=zh` 是三项独立配置。构建脚本只记录要求，不会在未经成员授权时修改云端 Agent。

需要更新时，在源码的 `firmware/` 目录中先设置临时环境变量，再显式执行：

```powershell
$env:XIAOZHI_ACCESS_TOKEN = "<当前登录会话取得的临时访问令牌>"
python .\scripts\xiaozhi_agent_config.py --agent-id <成员自己的AgentID> --apply
Remove-Item Env:XIAOZHI_ACCESS_TOKEN
```

工具会先读取当前 Agent，只更新 `language`，随后再次读取并校验角色、模型、记忆、音色和 MCP 配置未变化；令牌、Agent ID、设备 MAC 和审计文件均不提交。

## 已验收 A 基线

- App SHA256：`ac22644043bd09d0724f813bedcdb3c3cbcbe349df1424e76680866277611984`
- App ELF SHA256：`2972178257309f8c18946d023697aaa3b20612b51cde74cc7f35bc29b7b6f1a4`
- Assets SHA256：`96f804117e749d3bacd938a5039b4aab47629ebe5cd6010792497b0bfe8c9d98`
- 分区表 SHA256：`4811619cacae08ef2e0e71b7220c6033a346ca5da7ca179082408c963ef530b5`
- 烧录前完整 16 MiB 备份 SHA256：`906aedfcadd9244d6701d462e152e44ebc92b69afac280c23d8d80d12b14d3df`

真机通过项目：直接中文唤醒与提问、连续中文追问、触摸 PTT、主语音 → 本地 MCP → 实体头部动作。串口还确认了 WakeNet `wn9_nihaoxiaozhi_tts`、Xiaozhi 主会话和默认 AFE AEC 路径；独立动作 MCP 只属于可选构建，不作为当前演示基线。

完整备份和串口原始日志可能包含设备专属信息，只保存在验收机本地，不上传 Git。仓库只记录不可逆推出原始内容的哈希、结论和复现步骤。

## MultiNet 与 AEC 决策

普通 WakeNet A 已满足本轮用户体验底线，因此不再把中文 MultiNet 作为正式基线前置条件。`wakenet-mn6-flag`、`custom-multinet`、`wakenet-device-aec` 和 `wakenet-server-aec` 仍保留为诊断配置，出现明确回归时再构建比较，不继续无目标烧录。
