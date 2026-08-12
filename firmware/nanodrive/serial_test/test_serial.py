#!/usr/bin/env python3
"""
NanoDrive 串口测试工具

用途：PC 通过 USB 串口（或 USB-TTL）直接发指令给 NanoDrive，交互式调试。

用法：
  # 连 NanoDrive 的 USB 口
  python serial_test.py COM7

  # 或通过 USB-TTL 连 UART1
  python serial_test.py COM8 --baud 115200

命令：
  fw 200    前进
  bw 150    后退
  tl 200    左转
  tr 200    右转
  st        停止
  gs        查询状态
  en 1      使能
  en 0      禁用
  vl 150,-200  分别控左右轮
  rs        复位编码器
  to 500    设超时
  q         退出
"""

import sys
import time
import serial
import serial.tools.list_ports

def list_ports():
    print("可用串口:")
    for p in serial.tools.list_ports.comports():
        print(f"  {p.device} - {p.description}")

def main():
    if len(sys.argv) < 2:
        list_ports()
        print("\n用法: python serial_test.py <COM口> [--baud 115200]")
        print("示例: python serial_test.py COM7")
        sys.exit(1)

    port = sys.argv[1]
    baud = 115200
    if "--baud" in sys.argv:
        idx = sys.argv.index("--baud")
        baud = int(sys.argv[idx + 1])

    ser = serial.Serial(port, baud, timeout=1)
    print(f"已连接 {port} @ {baud}")
    time.sleep(2)

    # 读启动信息
    while ser.in_waiting:
        line = ser.readline().decode().strip()
        if line:
            print(f"[BASE] {line}")

    print("\n命令: fw/bw/tl/tr/st/gs/en/vl/rs/to | q 退出\n")

    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd in ("q", "quit", "exit"):
            break

        if not cmd:
            continue

        # 转换简写 → 协议指令
        parts = cmd.split()
        op = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        mapping = {
            "fw": "FW", "bw": "BW", "tl": "TL", "tr": "TR",
            "st": "ST", "gs": "GS", "en": "EN", "rs": "RS", "to": "TO",
            "vl": "VL",
        }

        if op not in mapping:
            print(f"未知指令: {op}")
            continue

        proto = mapping[op]
        if arg:
            proto_cmd = f"{proto}:{arg}"
        else:
            proto_cmd = proto

        # 发送
        ser.write((proto_cmd + "\n").encode())
        print(f"[TX] {proto_cmd}")

        # 等应答
        time.sleep(0.1)
        while ser.in_waiting:
            line = ser.readline().decode().strip()
            if line:
                print(f"[RX] {line}")

    ser.close()
    print("已断开")

if __name__ == "__main__":
    main()
