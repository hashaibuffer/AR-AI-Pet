# NanoDrive × StackChan 联调记录

## 当前结论

| 项目 | 状态 | 证据或边界 |
|---|---|---|
| 仓库与分支 | 通过 | `feat/nanodrive-stackchan-link` 基于 `origin/main` 403b9f0 |
| NanoDrive v0.9 烧录与静态验证 | 通过 | COM9、ATmega328P/LGT8F328P 签名 `1E 95 0F`；Flash 回读校验通过；`PING/GS/DI` 正常，已 `EN:0` |
| StackChan 正式固件 | 已恢复 | `stackchan-mcp` 验收 App，`ota_0` ELF `297217825730…` |
| StackChan 底座适配器 | 构建通过 | 已作为可复现补丁接入锁定的 `stackchan-mcp` 源码；`xiaozhi.bin` 约 26% 空闲 |
| 底座电机与编码器 | 待安全确认 | v0.9 已烧录；尚未发送会转动轮子的命令 |
| StackChan→NanoDrive 单向串口 | 待实机 | 当前没有连接中的设备串口 |
| NanoDrive→StackChan 状态返回 | 暂不实施 | 缺少 5V→3.3V 电平转换，绿线不接 |
| Beam Pro 链路 | 本阶段不做 | 当前窗口止于 StackChan→NanoDrive |

## 当前实现

- NanoDrive：D0/D1 硬件串口，115200，支持移动、差速、急停、看门狗和编码器诊断。
- StackChan：GPIO17（Port C 黄线）发送指令到 NanoDrive RX。
- 电脑：复用现成 WebSocket→MCP 控制入口，触发 `base_move`、`base_drive`、`base_stop`。
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

测试命令：

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
