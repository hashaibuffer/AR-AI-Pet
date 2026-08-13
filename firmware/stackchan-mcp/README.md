# StackChan × Kimito × Xiaozhi 正式固件基线

## 作用与边界

本模块固定已经通过真机验收的产品链：

```text
AI.AGENT / Xiaozhi：语音、ASR、会话和自动轮次的唯一所有者
                    │ 主语音 WebSocket
                    ▼
StackChan 实体：麦克风、扬声器、触摸、屏幕、舵机和安全执行
                    ▲
                    │ 独立动作 MCP WebSocket
Kimito 行为层：表情、头部动作、陪伴反馈，不接管语音会话
```

Beam Pro、Unity、AR 和其他 MCP 客户端仍是后续消费者；NanoDrive 蓝牙透传和遥控器 BASE 模式已经完成实机闭环，Agent/Beam Pro 链路仍待接入。

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

真机通过项目：直接中文唤醒与提问、连续中文追问、触摸 PTT、Agent → MCP → 实体头部动作。串口还确认了 WakeNet `wn9_nihaoxiaozhi_tts`、Xiaozhi 主会话、动作 MCP 独立连接以及默认 AFE AEC 路径。

完整备份和串口原始日志可能包含设备专属信息，只保存在验收机本地，不上传 Git。仓库只记录不可逆推出原始内容的哈希、结论和复现步骤。

## MultiNet 与 AEC 决策

普通 WakeNet A 已满足本轮用户体验底线，因此不再把中文 MultiNet 作为正式基线前置条件。`wakenet-mn6-flag`、`custom-multinet`、`wakenet-device-aec` 和 `wakenet-server-aec` 仍保留为诊断配置，出现明确回归时再构建比较，不继续无目标烧录。
