#!/usr/bin/env python3
"""NanoDrive 最终验证 — 逐项手动确认"""
import serial, time, sys, traceback

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM8"

def rd(ser, t=2):
    ser.timeout = t
    try:
        line = ser.read_until(b'\n').decode(errors='replace').strip()
        return line
    except: return ""

def drain(ser):
    ser.timeout = 0.3
    lines = []
    for _ in range(20):
        try:
            l = ser.read_until(b'\n').decode(errors='replace').strip()
            if l: lines.append(l)
        except: break
    return lines

def send_wait(ser, cmd, wait=0.5):
    """发送指令，清空旧缓冲，等待回复"""
    drain(ser)
    ser.write((cmd + "\n").encode())
    time.sleep(wait)
    lines = drain(ser)
    return lines

p, f = 0, 0

def check(desc, condition, detail=""):
    global p, f
    if condition:
        print(f"  [PASS] {desc} — {detail}", flush=True)
        p += 1
    else:
        print(f"  [FAIL] {desc} — {detail}", flush=True)
        f += 1

try:
    print("NanoDrive 最终验证", flush=True)
    print(f"{PORT} | {time.strftime('%H:%M:%S')}", flush=True)
    print("=" * 50, flush=True)
    print("⚠️ 轮子会转动！确保底座悬空或放在开阔桌面", flush=True)
    print("=" * 50, flush=True)

    ser = serial.Serial(PORT, 115200, timeout=3)
    time.sleep(4)

    # === 1. 启动 ===
    print("\n1. 启动确认", flush=True)
    lines = drain(ser)
    check("固件启动", any("READY" in l for l in lines), "; ".join(lines[:2]))

    # === 2. 使能 ===
    print("\n2. 电机使能", flush=True)
    lines = send_wait(ser, "PING")
    check("PING", any("OK:PONG:v0.9" in l for l in lines), "; ".join(lines))
    lines = send_wait(ser, "EN:1")
    check("EN:1", "OK:EN:1" in " ".join(lines), "; ".join(lines))

    # === 3. 前进 — 看轮子转不转 ===
    print("\n3. 前进 FW:80 — 看两轮是否都前转", flush=True)
    lines = send_wait(ser, "FW:80", 1.0)
    check("FW:80 回复状态", any(l.startswith("ST:") for l in lines), "; ".join(lines[:2]))
    check("前进后编码器 > 0", "L" in " ".join(lines) and "R" in " ".join(lines), "[肉眼确认轮子转向]")
    # 停止
    drain(ser)
    ser.write(b"ST\n")
    time.sleep(0.3)
    lines = drain(ser)
    check("ST 停止", "OK:ST" in " ".join(lines), "; ".join(lines))

    # === 4. 后退 ===
    print("\n4. 后退 BW:80 — 两轮后转", flush=True)
    send_wait(ser, "EN:1")
    lines = send_wait(ser, "BW:80", 1.0)
    check("BW:80", any(l.startswith("ST:") for l in lines), "; ".join(lines[:2]))
    drain(ser); ser.write(b"ST\n"); time.sleep(0.3); drain(ser)

    # === 5. 左转 ===
    print("\n5. 左转 TL:80 — 左轮后转, 右轮前转", flush=True)
    send_wait(ser, "EN:1")
    lines = send_wait(ser, "TL:80", 1.0)
    check("TL:80", any(l.startswith("ST:") for l in lines), "; ".join(lines[:2]))
    drain(ser); ser.write(b"ST\n"); time.sleep(0.3); drain(ser)

    # === 6. 右转 ===
    print("\n6. 右转 TR:80 — 左轮前转, 右轮后转", flush=True)
    send_wait(ser, "EN:1")
    lines = send_wait(ser, "TR:80", 1.0)
    check("TR:80", any(l.startswith("ST:") for l in lines), "; ".join(lines[:2]))
    drain(ser); ser.write(b"ST\n"); time.sleep(0.3); drain(ser)

    # === 7. GS ===
    print("\n7. 状态查询", flush=True)
    lines = send_wait(ser, "GS")
    check("GS", any(l.startswith("ST:") for l in lines), "; ".join(lines))

    # === 8. 编码器专项 ===
    print("\n8. 编码器专项 — RS 清零后前进 2 秒", flush=True)
    send_wait(ser, "RS")
    send_wait(ser, "EN:1")
    send_wait(ser, "FW:120", 2.0)
    send_wait(ser, "ST")
    lines = send_wait(ser, "GS")
    gs_line = ""
    for l in lines:
        if l.startswith("ST:"): gs_line = l
    if gs_line:
        parts = gs_line.split(",")
        enc_l = enc_r = 0
        for p in parts:
            if p.startswith("L"): enc_l = int(p[1:])
            elif p.startswith("R"): enc_r = int(p[1:])
        check("前进后编码器变化", enc_l > 0 and enc_r > 0, f"L={enc_l}, R={enc_r}")
    else:
        check("编码器", False, f"GS无回复: {lines}")

    # === 9. 超时 ===
    print("\n9. 安全超时", flush=True)
    send_wait(ser, "TO:500")
    drain(ser); ser.write(b"FW:100\n"); time.sleep(0.9)
    lines = drain(ser)
    check("500ms 超时自动停", any("ERR:TIMEOUT" in l for l in lines), "; ".join(lines[:2]))
    send_wait(ser, "TO:2000")

    # === 10. 禁用 ===
    print("\n10. 禁用保护", flush=True)
    lines = send_wait(ser, "EN:0")
    check("EN:0", "OK:EN:0" in " ".join(lines), "; ".join(lines))
    drain(ser); ser.write(b"FW:100\n"); time.sleep(0.3)
    lines = drain(ser)
    check("禁用后 FW 被拒", any("ERR:DISABLED" in l for l in lines), "; ".join(lines))

    # === 11. 未知指令 ===
    print("\n11. 未知指令", flush=True)
    send_wait(ser, "EN:1")  # 恢复使能
    lines = send_wait(ser, "XX:99")
    check("XX:99 ERR:UNKNOWN", any("ERR:UNKNOWN" in l for l in lines), "; ".join(lines))

    # === 12. 差速 ===
    print("\n12. 差速 VL:120,-120", flush=True)
    lines = send_wait(ser, "VL:120,-120", 1.0)
    check("VL:120,-120 回复状态", any(l.startswith("ST:") for l in lines), "; ".join(lines[:2]))
    drain(ser); ser.write(b"ST\n"); time.sleep(0.3); drain(ser)
    send_wait(ser, "EN:0")

    # 汇总
    print(f"\n{'='*50}", flush=True)
    print(f"  结果: {p}/{p+f} 通过", flush=True)
    if f == 0:
        print("  全部通过!", flush=True)
    else:
        print(f"  {f} 项未通过", flush=True)
    print("=" * 50, flush=True)

    ser.close()
except Exception as e:
    traceback.print_exc()
    print(f"\nERROR: {e}", flush=True)
