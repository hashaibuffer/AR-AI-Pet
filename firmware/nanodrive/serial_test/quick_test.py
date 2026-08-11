import serial, time, sys, traceback

port = sys.argv[1] if len(sys.argv) > 1 else "COM8"
print(f"Opening {port}...", flush=True)
try:
    ser = serial.Serial(port, 115200, timeout=3)
    print(f"Opened {port}", flush=True)
    time.sleep(3)

    # Drain boot
    lines = []
    for i in range(20):
        try:
            line = ser.read_until(b'\n').decode(errors='replace').strip()
            if line:
                lines.append(line)
            if 'READY' in line:
                break
        except:
            break
    print("=== BOOT ===", flush=True)
    for l in lines:
        print(l, flush=True)

    ser.close()
    print("=== DONE ===", flush=True)
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
