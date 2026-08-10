import sys
import time
import serial

port = sys.argv[1] if len(sys.argv) > 1 else "COM7"
seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 12
with serial.Serial(port, 115200, timeout=0.25) as ser:
    end = time.time() + seconds
    while time.time() < end:
        line = ser.readline()
        if line:
            sys.stdout.buffer.write(line)
            sys.stdout.flush()
