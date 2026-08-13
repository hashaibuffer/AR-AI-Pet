# NanoDrive × StackChan 联调记录

## 最新结论（2026-08-12）

本次已完成“商家 A4950 基准固件 → 蓝牙透传 → StackChan BLE 接收端 → NanoDrive 实际运动”的最小闭环，物理运动结果由用户现场确认：**轮子转动，方向符合预期**。

| 项目 | 已确认结果 |
|---|---|
| 底座固件 | 商家 A4950 最小验证固件的 115200 变体；保留商家电机、编码器、PI 和方向定义 |
| 蓝牙模块 | BK3432/JDY-23A 类模块，广播名 `JDY-23A-BLE`，本次观测地址 `90:43:50:03:90:16` |
| BLE 特征 | 服务 `FFE0`，写入特征 `FFE1`；StackChan 使用无响应写入发送原始字符 |
| 模块 UART | 实机透传按 115200 8N1 工作；公开 JDY-23 资料的出厂默认 9600 仅作为参考，不能替代本套模块实测 |
| 控制字节 | `A/E/Z` 前进、后退、停止；`H/B/G/C/F/D` 为前后左右和原地转向；每次动作均以 `Z` 收尾 |
| 实机证据 | Nano 串口收到 `OK:Z`、`OK:A`、`OK:Z`、`OK:E`、`OK:Z`；用户确认轮子实际转动且方向正确 |
| 当前边界 | 遥控器 BASE 模式已完成 BLE 底座实机验证；Beam Pro、Agent 和 AR 游戏仍未接入 |

本轮继续验证：StackChan BLE/BASE 固件在 COM7 编译、烧录并启动成功；StackChan 自动连接 `JDY-23A-BLE` 后，遥控器 BASE 模式已实际驱动底座。前进、后退、左转、右转和松手停止均由用户现场确认符合预期。针对持续输入失效和方向切换迟钝，最终采用 BLE 无响应写入、方向变化立即发送、相同指令 250 ms 合并刷新，并保留遥控器 300 ms 输入超时和底座 2 s 看门狗。

本轮未进行 Beam Pro、Agent、Unity 或 AR 游戏联调；未改变商家 A4950 电机、编码器、PI 和方向定义。

蓝牙模块自身会向 Nano 串口输出 `+DISC:SUCCESS`、`CONNECTED` 等状态文本。商家固件会把这些非方向字符报告为 `ERR:UNKNOWN`，但不影响控制字节透传；后续可在固件中增加状态文本过滤，不能把这些日志误判为运动失败。

## 2026-08-13 固件恢复记录

本次不应重复阶段一：2026-08-12 的商家 A4950 → 蓝牙透传 → StackChan BLE → NanoDrive 实机闭环已经通过。本次因误读旧计划，临时把底座刷回了 9600 基准固件并重复发送了 `A/E/Z`，该动作不构成新的验收结论。

已恢复当前已验收路径：

- 使用 `vendor_a4950_ble_115200.ino` 编译成功；Flash 使用量 17%，RAM 使用量 17%。
- COM9 烧录成功，芯片签名 `1E 95 0F`，5308 字节 Flash 回读校验通过。
- 当前已发送 `Z`，底座保持停止；本次未重复观察物理方向。
- 蓝牙模块仍需人工接回、底座 USB 需人工拔下，之后才可继续已通过的 BLE 链路或进入下一阶段。

串口启动文字本次未可靠捕获，因此只记录为“编译/烧录/Flash 校验通过”，不把它表述为新的串口回执或物理运动验收。

## 历史直连路径结论（2026-08-11）

| 项目 | 状态 | 证据或边界 |
|---|---|---|
| 仓库与分支 | 通过 | `feat/nanodrive-stackchan-link` 基于 `origin/main` 403b9f0 |
| NanoDrive v0.9 烧录与静态验证 | 通过 | COM9、ATmega328P/LGT8F328P 签名 `1E 95 0F`；Flash 回读校验通过；`PING/GS/DI` 正常，已 `EN:0` |
| StackChan 正式固件 | 已验证 | 候选固件启动于 `ota_1` 并完成 `Marking firmware as valid`；COM7 日志正常 |
| StackChan 底座适配器 | 构建与调用通过 | GPIO17 TX-only、115200；网关已暴露 `base_move/base_drive/base_stop` |
| 底座电机与编码器 | 底座单机通过 | NanoDrive v0.9 的动力、编码器、急停和看门狗已由独立测试确认 |
| StackChan→NanoDrive 单向串口 | 已打通（TX 证据） | COM7 日志确认 `EN:1`、`FW/VL`、`ST` 均已发出；未接回读线 |
| NanoDrive→StackChan 状态返回 | 暂不实施 | 缺少 5V→3.3V 电平转换，绿线不接 |
| Beam Pro 链路 | 本阶段不做 | 当前窗口止于 StackChan→NanoDrive |

## 当前实现

- NanoDrive：D0/D1 硬件串口，115200，支持移动、差速、急停、看门狗和编码器诊断。
- StackChan：GPIO17（Port C 黄线）发送指令到 NanoDrive RX。
- 电脑：运行动作网关（`8765`）和 Streamable HTTP MCP（`8767`），通过 `base_move`、`base_drive`、`base_stop` 调用 StackChan。
- 安全：StackChan 侧速度限制 180；NanoDrive 运动超时 2000 ms 自动停车。

## 接线

| 线色 | 连接 |
|---|---|
| 黑 | StackChan GND ↔ NanoDrive G |
| 黄 | StackChan TX → NanoDrive RX |
| 绿 | 不接 |
| 红 | 不接，两端分别供电 |

## 实机执行顺序

1. 底座轮子悬空，NanoDrive 单独通过 USB（本次为 COM9）烧录 v0.9。
2. 已完成 `PING`、`EN:0`、`GS`、`DI` 静态验证；动力测试前确认轮子悬空或周围无障碍。
3. 断开 NanoDrive USB，连接黑线和黄线，底座独立供电。
4. 使用 ESP-IDF 5.5.4 运行正式构建入口，确认项目补丁和固件构建通过后再烧录，并保持连接电脑查看日志。
5. 电脑与 StackChan 在同一 Wi-Fi，依次发送低速前进、停止、后退、左右转。
6. 拔掉黄线或停止发指令，确认底座最迟约 2 秒停车。

## 2026-08-11 StackChan→NanoDrive 实机联调

- COM9 已断开，COM7 保持连接；底座通过独立电池供电，黑线和黄线保持连接。
- 候选固件运行在 `ota_1`，OTA 状态为 `seq=4/state=2 (valid)`。
- 动作网关已连接设备 `80:45:6b:54:7d:10`，发现 43 个设备工具。
- 网关补丁新增对外工具 `base_move`、`base_drive`、`base_stop`，并转发到固件的 `self.robot.*` 工具。
- 悬空轮测试通过：COM7 日志出现 `EN:1`、`FW:60`、`VL:60,60`、`VL:-60,-60`、`VL:-60,60`、`VL:60,-60` 及对应 `ST`。
- 当前仍是 TX-only：不读取 NanoDrive 回执，不把“调用返回 true”解释为底座回执；底座安全由本地看门狗和 `ST` 保证。

当前动作网关使用 Streamable HTTP `http://127.0.0.1:8767/mcp`，由 MCP 客户端调用 `base_move`、`base_drive`、`base_stop`。仓库中的 `Invoke-StackChanControl.ps1` 仍是官方设备 `8080/ws` 的旧直连测试入口，不作为本次底座控制命令。

历史直连命令（仅供旧链路参考）：

```powershell
.\tools\stackchan-control-test\Invoke-StackChanControl.ps1 -RobotHost <IP> -Action base_move -Direction forward -Speed 80
.\tools\stackchan-control-test\Invoke-StackChanControl.ps1 -RobotHost <IP> -Action base_stop
```

实机完成前，不能把“编译通过”写成“串口联调通过”。

## 2026-08-11 固件恢复

旧 `D:\sc` 构建曾误写 StackChan，导致 Bootloader、分区表、App、Assets 和 OTA 选择偏离正式基线。已使用主仓验收制品及误写前备份定点恢复，未写 NVS 和保留的 `ota_1`。

| 验证项 | 结果 |
|---|---|
| Boot、分区表、App、Assets | `esptool verify_flash` 通过 |
| App 身份 | ELF `2972178257309f8c18946d023697aaa3b20612b51cde74cc7f35bc29b7b6f1a4` |
| OTA | `ota_0` 启动并标记为 valid，独立重启后仍保持 |
| 设备基础状态 | 中文会话模式、触摸 PTT、联网正常 |

后续只从主仓锁定源码和验收制品开发、构建与烧录，不再使用独立旧源码目录。
