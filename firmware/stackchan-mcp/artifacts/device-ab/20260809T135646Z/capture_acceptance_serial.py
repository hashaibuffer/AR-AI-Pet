#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
from pathlib import Path
import time

import serial


parser = argparse.ArgumentParser()
parser.add_argument("--port", default="COM7")
parser.add_argument("--seconds", type=int, default=300)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

args.output.parent.mkdir(parents=True, exist_ok=True)
serial_port = serial.Serial()
serial_port.port = args.port
serial_port.baudrate = 115200
serial_port.timeout = 0.5
serial_port.dtr = False
serial_port.rts = False
serial_port.open()

deadline = time.monotonic() + args.seconds
with args.output.open("w", encoding="utf-8", newline="\n") as output:
    output.write(f"# started_at={datetime.now(timezone.utc).isoformat()}\n")
    output.write(f"# port={args.port}\n")
    output.write("# reset_requested=false\n")
    while time.monotonic() < deadline:
        raw = serial_port.readline()
        if raw:
            timestamp = int(time.time() * 1000)
            output.write(f"[{timestamp}] {raw.decode('utf-8', errors='replace').rstrip()}\n")
            output.flush()

serial_port.close()
