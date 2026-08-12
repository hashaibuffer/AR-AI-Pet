# ESP-NOW 遥控器

基于 M5Stack StackChan 官方遥控器，增加项目需要的四种控制模式和安全状态机。

| 模式 | 进入方式 | 遥控器输入用途 |
| --- | --- | --- |
| `HEAD` | 开机默认；实体模式键切换 | 保持原头部 yaw/pitch 映射 |
| `BASE` | 实体模式键切换 | 控制底座前后与转向 |
| `GAME_YAHTZEE` | StackChan/Agent 指令 | 快艇骰子操作 |
| `GAME_FARM` | StackChan/Agent 指令 | 种菜操作 |

实体模式键只在 `HEAD` 与 `BASE` 间切换。进入游戏前记住当前模式，游戏结束后恢复。离开 `BASE` 会先发停止标志；接收端超过 300 ms 未收到输入也必须自行停止。

## 当前交付

- `core/`：与硬件无关的协议、模式状态机、映射与接收端超时逻辑。
- `tests/`：本地 Mock 验证，不代表遥控器或 StackChan 实机通过。
- `source.lock.json`：官方遥控器来源和固定版本。
- `patches/`：对官方遥控器工程的可复现项目补丁。

协议采用固定 24 字节二进制帧，包含协议版本、消息类型、模式、序号、摇杆、原头部 yaw/pitch、按键保持状态、单次按键事件和 CRC8。Agent 游戏切换由 StackChan 通过反向 ESP-NOW 消息发送，遥控器收到状态回执后显示在线；1 秒无回执显示离线。

## 本地验证

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\espnow-controller\scripts\test-host.ps1
```

本地验证覆盖：原头部映射、摇杆映射、模式隔离、单次按键事件、离开底座停止、接收端断连超时停止和协议损坏拒收。

在 ESP-IDF PowerShell 中准备并构建遥控器固件：

```powershell
.\firmware\espnow-controller\scripts\bootstrap.ps1
.\firmware\espnow-controller\scripts\apply-project-patch.ps1
.\firmware\espnow-controller\scripts\build-firmware.ps1
```

## 实机边界

遥控器工程已经接入模式显示、在线状态、双向 ESP-NOW 收发和 30 ms 输入帧，并通过 ESP-IDF 5.5.4 全量编译。StackChan 接收端尚未接入，因此 Agent 自动切换、在线回执和实机控制仍待下一阶段分别烧录验收。未经实机观察，不将编译成功写成遥控器或底座控制通过。
