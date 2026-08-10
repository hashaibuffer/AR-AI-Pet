# Arduino 底盤控制（Arduino Pedestal）

來源：R2miniQ 兩輪 PID 智能小車套件。

## 目錄結構

```
arduino-pedestal/
├── sketches/
│   ├── 01-speed-closed-loop/    # 兩輪速度閉環
│   ├── 02-bluetooth-remote/     # 藍牙遙控
│   ├── 03-ultrasonic-avoidance/ # 超聲波避障
│   ├── 04-ultrasonic-follow/    # 超聲波開環自動跟隨
│   ├── 05-ps2-remote/           # PS 手柄遙控
│   └── oled-display/            # OLED 顯示
└── docs/
    └── Arduino兩輪PID智能小車原理圖.pdf
```

## 第三方庫依賴

以下庫需通過 Arduino Library Manager 安裝，不隨倉庫提交：

| 庫名 | 用途 | 安裝方式 |
|------|------|---------|
| HC-SR04 | 超聲波測距 | Library Manager 搜索 "HC-SR04" |
| MsTimer2 | 定時中斷 | Library Manager 搜索 "MsTimer2" |
| PS2X_lib | PS2 手柄通訊 | Library Manager 搜索 "PS2X" |
| SSD1306 | OLED 顯示 | Library Manager 搜索 "SSD1306" / "Adafruit SSD1306" |
| R2miniQ_OLED | 小車 OLED 專用封裝 | 隨套件提供，見原始 `libraries/` |

## 硬件

- 主控：Arduino（R2miniQ 套件）
- 底盤：兩輪差分驅動 + PID 閉環
- 傳感器：HC-SR04 超聲波
- 通訊：藍牙 / PS2 無線手柄
