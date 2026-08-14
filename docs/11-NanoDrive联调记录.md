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
| 项目 Agent/Robot Bridge | 软件适配器已接入，实体待验证 | `StackChanWebSocketAdapter` 已将语义动作转换为 StackChan MCP JSON-RPC，并保留速度/时长限制；尚未在现场由项目 Agent 触发并观察动作。 |
| Beam Pro / Unity / BLE 状态回传 | 待验证 | Beam Pro/XREAL 实机显示、Unity 完整链路以及底座实际状态回传仍未完成。 |

### 现场链路断点（待改善）

当前已确认“底座—BLE—StackChan”实体子链路，但还没有把它与项目 Agent 的控制入口配成同一条可复现链路。原因是仓库同时记录了两种方案：

```text
直接设备方案：Agent/Robot Bridge ── ws://StackChan:8080/ws ──> StackChan
Scheme B：StackChan ── ws://电脑:8765 ──> stackchan-mcp Gateway
          Agent/Robot Bridge ── http://电脑:8767/mcp ──> Gateway
```

待补证据：当前刷入固件的动作网关地址、设备与电脑的实际局域网 IP、8765/8767 监听情况、网关设备会话日志，以及一次由项目 Agent 发起的头部动作和底座短动作。补齐前，`ROBOT_BRIDGE_SMOKE_OK` 只能作为 Mock 证据，不能写成实体闭环通过。

### 2026-08-13 现场串口探测

| 检查 | 结果 | 结论 |
|---|---|---|
| COM7 启动日志 | 通过读取到启动日志 | StackChan 固件正常启动，MCP 工具已注册，包含 `self.robot.set_head_angles`、`base_move`、`base_stop`。 |
| StackChan → 底座 BLE | 通过 | 日志确认 GATT 连接、发现 `FFE0/FFE1`，并向 `FFE1` 写入安全停止 `ST`。 |
| StackChan → Wi-Fi | 未通过 | 本次启动连续出现 `Haven't to connect to a suitable AP now!`，未获得设备 IP。 |
| StackChan → 动作网关 | 未建立 | 因未连上 Wi-Fi，无法验证固件配置的 `8765` 网关地址；电脑端也不能据此宣称 8080 或 8767 已连通。 |
| COM9 USB → NanoDrive | 未形成证据 | 仅做过只读/停止探测，没有把 USB 串口当作正式运行链路，也未执行移动。 |

本次探测只证明“StackChan 与底座的近端 BLE 已连上”，没有改变上表中 Agent/Robot Bridge 实体待验证状态。下一次联调应先让 StackChan 连接与动作网关同一局域网，再记录设备 IP、网关监听和设备会话后，才允许做短时头部动作；底座移动仍需在头部动作成功后单独进行。

补充：当前刷入固件采用 Mooncake 应用结构，`AI.AGENT` 应用的 `onOpen()` 才会调用 `requestXiaozhiStart()`。因此“StackChan 已连 Wi-Fi”只代表网络层已就绪；必须打开 `AI.AGENT`（或启用其开机启动配置）后，才会启动语音/Agent WebSocket 会话和动作 MCP WebSocket。未打开应用时，动作网关没有设备会话是预期现象，不应误判为 Wi-Fi、BLE 或端口故障。软件诊断发现固件配置的网关 URL（`ws://192.168.50.133:8765`）与当前统一服务端点（`ws://<PC_IP>:8090/ws/device`）不匹配，恢复步骤见 [`docs/13-动作网关会话恢复步骤.md`](13-动作网关会话恢复步骤.md)。

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

## 固件来源边界（2026-08-13）

- 官方 Mooncake/StackChan 来源见 [`firmware/stackchan/source.lock.json`](../firmware/stackchan/source.lock.json)，可复现检查不会包含底座工具。
- `base_move`、`base_drive`、`base_stop` 和 NanoDrive BLE 运行实现来自 [`firmware/stackchan-mcp/`](../firmware/stackchan-mcp/) 的 Scheme B 参考补丁；当前设备虽有对应日志，源码与设备 ELF 尚未完全匹配。
- 下一阶段若要移植动作客户端，必须在官方 Mooncake 基线上建立独立补丁，不直接把 Scheme B 整棵源码覆盖进来。
