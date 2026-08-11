#!/usr/bin/env python3
"""NanoDrive 编码器专项诊断 — 确认轮子转动 + 编码器计数"""
import serial, time, sys

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM8"

def drain(ser):
    ser.timeout = 0.2
    lines = []
    for _ in range(10):
        try:
            l = ser.read_until(b'\n').decode(errors='replace').strip()
            if l: lines.append(l)
        except: break
    return lines

def send(ser, cmd):
    ser.write((cmd + "\n").encode())

def query(ser):
    """发 GS，返回解析后的 (L, R, V)"""
    drain(ser)
    send(ser, "GS")
    time.sleep(0.15)
    lines = drain(ser)
    for l in lines:
        if l.startswith("ST:"):
            parts = l.split(",")
            enc_l = enc_r = vbat = 0
            for p in parts:
                if p.startswith("L"): enc_l = int(p[1:])
                elif p.startswith("R"): enc_r = int(p[1:])
                elif p.startswith("V"): vbat = int(p[1:])
            return enc_l, enc_r, vbat
    return None, None, None

try:
    ser = serial.Serial(PORT, 115200, timeout=2)
    time.sleep(3)
    drain(ser)  # 吞启动消息

    print("=" * 60)
    print("NanoDrive 编码器专项诊断")
    print("=" * 60)

    # 1. 启动状态
    l, r, v = query(ser)
    print(f"\n[启动] L={l}, R={r}, Vbat={v}mV")

    # 2. 使能
    drain(ser); send(ser, "EN:1"); time.sleep(0.3)
    resp = drain(ser)
    print(f"[使能] {' '.join(resp)}")

    # 3. 清零编码器
    drain(ser); send(ser, "RS"); time.sleep(0.3)
    resp = drain(ser)
    print(f"[清零] {' '.join(resp)}")
    l, r, v = query(ser)
    print(f"[清零后] L={l}, R={r}  (应为 0,0)")

    # 4. 编码器原始读数（不动时）
    print(f"\n[静止时编码器采样] (电机未动，编码器应不变)")
    for i in range(5):
        l, r, v = query(ser)
        print(f"  #{i}: L={l}, R={r}, V={v}mV")
        time.sleep(0.3)

    # 5. 前进 3 秒 + 连续采样
    print(f"\n[前进 FW:180 — 3 秒]")
    print("   ⚠️ 请肉眼确认两轮是否前转！")
    drain(ser); send(ser, "FW:180")
    for i in range(6):
        time.sleep(0.5)
        l, r, v = query(ser)
        arrow_l = "↑" if l > 0 else ("↓" if l < 0 else "·")
        arrow_r = "↑" if r > 0 else ("↓" if r < 0 else "·")
        print(f"  t={0.5*(i+1):.1f}s  L={l:>5d} {arrow_l}  R={r:>5d} {arrow_r}  V={v}mV")

    # 停止
    drain(ser); send(ser, "ST"); time.sleep(0.3)
    resp = drain(ser)
    l, r, v = query(ser)
    print(f"\n[停止] {' '.join(resp)}")
    print(f"[停止后] L={l}, R={r}")

    # 6. 后退测试
    print(f"\n[后退 BW:180 — 2 秒]")
    drain(ser); send(ser, "BW:180")
    for i in range(4):
        time.sleep(0.5)
        l, r, v = query(ser)
        arrow_l = "↑" if l > 0 else ("↓" if l < 0 else "·")
        arrow_r = "↑" if r > 0 else ("↓" if r < 0 else "·")
        print(f"  t={0.5*(i+1):.1f}s  L={l:>5d} {arrow_l}  R={r:>5d} {arrow_r}  V={v}mV")

    drain(ser); send(ser, "ST"); time.sleep(0.3); drain(ser)

    # 7. 转向测试
    print(f"\n[左转 TL:120 — 1.5 秒]")
    drain(ser); send(ser, "TL:120")
    for i in range(3):
        time.sleep(0.5)
        l, r, v = query(ser)
        print(f"  t={0.5*(i+1):.1f}s  L={l:>5d}  R={r:>5d}  V={v}mV")
    drain(ser); send(ser, "ST"); time.sleep(0.3); drain(ser)

    print(f"\n[右转 TR:120 — 1.5 秒]")
    drain(ser); send(ser, "TR:120")
    for i in range(3):
        time.sleep(0.5)
        l, r, v = query(ser)
        print(f"  t={0.5*(i+1):.1f}s  L={l:>5d}  R={r:>5d}  V={v}mV")
    drain(ser); send(ser, "ST"); time.sleep(0.3); drain(ser)

    # 8. 诊断结论
    print(f"\n{'='*60}")
    l, r, v = query(ser)
    print(f"最终状态: L={l}, R={r}, Vbat={v}mV")
    print(f"{'='*60}")

    if l == 0 and r == 0:
        print("\n⚠️ 编码器全程为 0，可能原因：")
        print("  1. 轮子根本没转 — 检查电池是否接好、电量是否充足")
        print("  2. 编码器接线与引脚定义不匹配 — 检查 A/B 相是否接对")
        print("  3. 编码器供电问题（通常需要 5V/VCC）")
        print("  4. 中断引脚 (D2/D3) 被其他功能占用")
    else:
        print(f"\n✓ 编码器工作正常！L={l}, R={r}")

    # 禁用
    drain(ser); send(ser, "EN:0"); time.sleep(0.3); drain(ser)
    ser.close()

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
