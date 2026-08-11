# NanoDrive 固件

## 模块用途

为 Arduino Nano 底座实现基础移动、停止和断连保护。

## 主责人

B。

## 目录结构

```
nanodrive/
├── nanodrive_firmware/
│   └── nanodrive_firmware.ino   Arduino 固件
├── serial_test/
│   └── test_serial.py            PC 串口测试工具
├── mock/
│   └── nanodrive_mock.py         无硬件模拟器
└── README.md
```

## 编译与烧录

1. Arduino IDE 安装 Nano 驱动（CH340/FT232）。
2. 打开 `nanodrive_firmware/nanodrive_firmware.ino`。
3. 核对 PIN MAP 段。
4. 选板型 "Arduino Nano" / ATmega328P (Old Bootloader)。
5. 编译 → 烧录 → 串口监视器看到 `NanoDrive v0.9` 和 `READY`。

## 快速测试

USB 串口监视器直接发指令：

```
EN:1     使能电机
FW:100   前进
TL:100   左转
ST       停止
GS       查编码器和电压
PING     查固件版本
EN:0     禁用
```

或跑 Python 脚本：

```bash
python serial_test/test_serial.py COM7
```

## UART1 接线

StackChan Port C → HY2.0-4P → NanoDrive UART1：

| 杜邦线 | UART1 | 说明 |
|---|---|---|
| 黑 | G | 共地 |
| 黄 | RX | Port C TX → NanoDrive RX |
| 绿 | TX | 当前不接；缺少 5V→3.3V 电平转换 |
| 红 | — | 不接，各自独立供电 |

当前采用单向控制：只接黑线和黄线。NanoDrive USB 用于烧录和单机诊断；接入 StackChan 运行时拔掉 NanoDrive USB，避免 D0/D1 与 CH340 同时驱动。

## StackChan 控制测试

StackChan 固件把 NanoDrive 动作注册为 MCP 工具。电脑与 StackChan 在同一 Wi-Fi 后执行：

```powershell
.\tools\stackchan-control-test\Invoke-StackChanControl.ps1 -RobotHost <StackChan-IP> -Action base_move -Direction forward -Speed 100
.\tools\stackchan-control-test\Invoke-StackChanControl.ps1 -RobotHost <StackChan-IP> -Action base_stop
```

电脑命令经 Wi-Fi 到 StackChan，再由 Port C UART 发送给底座。StackChan 可继续通过 USB 连接电脑查看日志。

## 串口参数

| 参数 | 值 |
|---|---|
| 波特率 | 115200 |
| 数据位 | 8 |
| 停止位 | 1 |
| 校验 | 无 |

## 协议

见 [`packages/protocol/schemas/nanodrive_uart_protocol.md`](../../packages/protocol/schemas/nanodrive_uart_protocol.md)。

## 联调

按 [`docs/11-NanoDrive联调记录.md`](../../docs/11-NanoDrive联调记录.md) 逐项验证并记录。

## 已知问题

- 底座本身没有 Wi-Fi，通过 StackChan 转发。
- 当前没有 NanoDrive→StackChan 状态返回；StackChan 日志中的“accepted”只表示 UART 已发出。
- 当前未使用 SERVO/SR04/CCD/PS2 接口。
