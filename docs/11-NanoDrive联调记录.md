# NanoDrive × StackChan 联调记录

## 当前结论（2026-08-13）

`遥控器 → ESP-NOW → StackChan → BLE 透明串口 → NanoDrive v0.9 → A4950 底座` 已完成实体闭环。用户现场确认前进、后退、左转、右转和松手停止符合预期。

| 环节 | 状态 | 证据或边界 |
|---|---|---|
| NanoDrive v0.9 | 通过（实体） | Arduino Nano，115200 8N1，`EN/VL/ST`，本地 2000 ms 看门狗；COM9 烧录、`PING/GS/EN:0`、动力、编码器、急停和超时停车已验证。 |
| 商家 A4950 基准 | 通过（实体） | 商家电机、编码器、PI 和方向定义未改动；115200 单字符 `A/E/Z` 曾用于确认蓝牙透传与方向。 |
| BLE 链路 | 通过（实体） | BK3432/JDY-23A 类模块，`FFE0/FFE1`，模块 UART 为 115200；StackChan 已连接并可写入。 |
| StackChan / 遥控器 | 通过（实体） | ESP-IDF 5.5.4 完整构建并烧录至 COM7；BASE 模式前后左右与松手停止由用户确认。 |
| 当前安全 | 通过（实体） | 连接后先 `ST`；首次运动将 `EN:1` 与首条 `VL` 合并写入；松手、退出 BASE、失联均发 `ST`；遥控器 300 ms 输入超时与底座 2 s 看门狗共同兜底。 |
| 未接入 | 待验证 | Beam Pro、Unity/AR、项目 Agent/Robot Bridge 对此实体链路的调用，以及 BLE 状态回传。 |

## 当前运行协议

```text
ESP-NOW 遥控器
  → StackChan（BASE 模式）
  → BLE FFE1 无响应写入
  → JDY-23A/BK3432 UART（115200 8N1）
  → NanoDrive v0.9
```

- 首次运动或急停后：同一 BLE 写入内发送 `EN:1\nVL:left,right\n`。
- 持续运动：发送 `VL:left,right\n`；方向或明显速度变化立即发送，相同输入每 250 ms 刷新。
- 停止：发送 `ST\n`。BLE 写入成功只代表请求被 GATT 接受，不代表 NanoDrive 已回执。
- StackChan 侧最大速度为 180；NanoDrive 固件可接受范围仍为 `-255..255`。

正式字段与命令见 [`packages/protocol/schemas/nanodrive_uart_protocol.md`](../packages/protocol/schemas/nanodrive_uart_protocol.md)。

## 本轮验证记录

### NanoDrive 单机（COM9）

```text
PING  -> OK:PONG:v0.9
GS    -> ST:L0,R0,V7734,E0,M0
EN:0  -> OK:EN:0
```

动力与保护测试的串口结果包含 `BW/TL/TR/VL` 的 `OK:EN:1`、运动状态和 `OK:ST`；`TO:500` 后收到 `ERR:TIMEOUT`。用户确认各方向和超时停车符合预期。最终恢复为 `ST`，看门狗为 2000 ms。

### StackChan / BLE / 遥控器

StackChan 启动日志确认发现 `FFE0` 服务与 `FFE1` 写特征、成功连接蓝牙模块并完成安全 `ST` 写入。随后用户在 BASE 模式确认前进、后退、左转、右转和松手停止。针对早期左右切换迟钝，当前实现采用方向变化立即发送与 250 ms 刷新；本轮结果符合预期。

## 可复现入口

| 目的 | 文件或入口 |
|---|---|
| NanoDrive 正式固件 | [`firmware/nanodrive/nanodrive_firmware/nanodrive_firmware.ino`](../firmware/nanodrive/nanodrive_firmware/nanodrive_firmware.ino) |
| StackChan 补丁 | [`firmware/stackchan-mcp/patches/0007-nanodrive-v09-ble-protocol.patch`](../firmware/stackchan-mcp/patches/0007-nanodrive-v09-ble-protocol.patch) |
| StackChan 构建与补丁应用 | [`firmware/stackchan-mcp/README.md`](../firmware/stackchan-mcp/README.md) |
| 遥控器工程 | [`firmware/espnow-controller/`](../firmware/espnow-controller/) |
| 完整验收表 | [`docs/07-测试与Demo验收.md`](07-测试与Demo验收.md) |

## 历史记录与不采用路径

- 2026-08-11 的 StackChan GPIO17 → NanoDrive RX 直连 UART 仅保留为排障记录；当前产品运行不接 StackChan 与底座之间的 UART 线。
- 2026-08-12 的商家 `A/E/Z/H/B/G/C/F/D` 单字符固件用于确认 A4950 方向和蓝牙透明传输；不再作为正式运行协议。
- 本记录不把“编译通过”“GATT 写入成功”表述为物理运动通过；本次物理运动结论来自用户现场确认。
