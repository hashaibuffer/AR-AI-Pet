#!/usr/bin/env python3
"""NanoDrive 诊断"""
import serial, time, sys

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM8"

ser = serial.Serial(PORT, 115200, timeout=1)
ser.reset_input_buffer()
time.sleep(3)

def readlines(sec=1.0):
    ser.timeout = sec
    out = []
    deadline = time.time() + sec
    while time.time() < deadline:
        b = ser.read_until(b'\n')
        if b:
            line = b.decode(errors='replace').strip()
            if line:
                out.append(line)
    return out

def cmd(c):
    ser.reset_input_buffer()
    ser.write((c + '\n').encode())
    time.sleep(0.25)
    lines = readlines(1.0)
    clean = [l for l in lines if not l.startswith('[')]
    return clean[-1] if clean else (lines[-1] if lines else '')

# flush startup
for l in readlines(2.0):
    print(f"BOOT: {l}")

print("\n1. 使能 + 前进 (观察轮子是否转动) ---")
print(cmd("EN:1"))
time.sleep(0.2)
print(cmd("FW:80"))
print("(等待 2 秒观察轮子...)")
time.sleep(2)
print(cmd("ST"))

print("\n2. 编码器读数 ---")
print(cmd("GS"))

print("\n3. 手转轮子测试 (请手动转左右轮 5 秒) ---")
start = time.time()
while time.time() - start < 5:
    v = cmd("GS")
    if v:
        print(f"  {time.time()-start:.1f}s: {v}")
    time.sleep(0.3)

print("\n4. 禁用 ---")
print(cmd("EN:0"))
ser.close()
print("完成")
