"""Raw debug - see exactly what comes back"""
import serial, time, sys

ser = serial.Serial("COM8", 115200, timeout=3)
time.sleep(4)
print("=== DRAIN ===", flush=True)
ser.timeout = 0.3
for _ in range(30):
    try:
        line = ser.read_until(b'\n').decode(errors='replace')
        if line.strip():
            print(f"  DRAIN: {line.strip()}", flush=True)
    except: break

print("=== SEND EN:1 ===", flush=True)
ser.write(b"EN:1\n")
ser.flush()
time.sleep(0.5)
for _ in range(20):
    try:
        line = ser.read_until(b'\n').decode(errors='replace')
        if line.strip():
            print(f"  RX: [{line.strip()}]", flush=True)
    except: break

print("=== SEND GS ===", flush=True)
ser.write(b"GS\n")
ser.flush()
time.sleep(0.5)
for _ in range(20):
    try:
        line = ser.read_until(b'\n').decode(errors='replace')
        if line.strip():
            print(f"  RX: [{line.strip()}]", flush=True)
    except: break

print("=== DONE ===", flush=True)
ser.close()
