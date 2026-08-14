"""Check StackChan connection status - run on Windows.
Usage: python check_all.py
"""
import json, time, sys, threading

BASE = "http://localhost:8090"

def check_health():
    import urllib.request
    try:
        r = urllib.request.urlopen(f"{BASE}/health", timeout=5)
        print(f"[1] Health: {r.read().decode()}")
        return True
    except Exception as e:
        print(f"[1] Health FAILED: {e}")
        return False

def check_mcp_tools():
    import urllib.request
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}).encode()
    req = urllib.request.Request(f"{BASE}/mcp", data=body, headers={
        "Content-Type":"application/json",
        "Accept":"application/json, text/event-stream"
    })
    try:
        r = urllib.request.urlopen(req, timeout=10)
        raw = r.read().decode()
        # Parse SSE response
        for line in raw.split('\n'):
            if line.startswith('data:'):
                data = json.loads(line[5:].strip())
                if 'result' in data and 'tools' in data['result']:
                    tools = [t['name'] for t in data['result']['tools']]
                    robot_tools = [t for t in tools if 'robot' in t or 'base' in t]
                    print(f"[2] MCP tools ({len(tools)} total):")
                    for t in tools:
                        print(f"    {t}")
                    return robot_tools
        print(f"[2] MCP response (raw): {raw[:300]}")
    except Exception as e:
        print(f"[2] MCP tools FAILED: {e}")
    return []

def send_robot_action(intent, parameters):
    import urllib.request
    body = json.dumps({
        "jsonrpc":"2.0","id":99,"method":"tools/call",
        "params":{"name":"robot.react","arguments":{"intent":intent,"parameters":parameters}}
    }).encode()
    req = urllib.request.Request(f"{BASE}/mcp", data=body, headers={
        "Content-Type":"application/json",
        "Accept":"application/json, text/event-stream"
    })
    try:
        r = urllib.request.urlopen(req, timeout=15)
        raw = r.read().decode()
        print(f"[4] Action '{intent}' response: {raw[:500]}")
        return raw
    except Exception as e:
        print(f"[4] Action '{intent}' FAILED: {e}")
        return None

def check_com7(duration=15):
    try:
        import serial
    except ImportError:
        print("[3] pyserial not installed, trying pip install...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pyserial"], capture_output=True)
        import serial

    print(f"[3] Reading COM7 for {duration}s (reset StackChan now!)...")
    try:
        port = serial.Serial("COM7", 115200, timeout=1)
        end = time.time() + duration
        buf = ""
        while time.time() < end:
            data = port.read(4096).decode('utf-8', errors='replace')
            if data:
                buf += data
                # Print in real-time
                sys.stdout.write(data)
                sys.stdout.flush()
        port.close()
    except Exception as e:
        print(f"[3] COM7 error: {e}")
        return ""

    print("\n\n--- COM7 Analysis ---")
    if "got ip" in buf.lower() or "ip:" in buf.lower():
        import re
        m = re.search(r'(?:got ip|ip:)\s*[:]*\s*([0-9.]+)', buf, re.I)
        if m: print(f"  Wi-Fi: CONNECTED ({m.group(1)})")
        else: print("  Wi-Fi: seems connected")
    else:
        print("  Wi-Fi: NOT FOUND in output")

    if "action gateway" in buf.lower():
        if "connected" in buf.lower():
            print("  Gateway: CONNECTED!")
        elif "timed out" in buf.lower():
            print("  Gateway: TIMEOUT")
        else:
            print("  Gateway: mentioned")
        import re
        m = re.search(r'action gateway.*?(ws[s]?://[^\s]+)', buf, re.I)
        if m: print(f"  Gateway URL: {m.group(1)}")
    else:
        print("  Gateway: not mentioned (AI.AGENT app may not be open)")

    import re
    tools = re.findall(r'Add tool:\s*(\S+)', buf)
    if tools:
        print(f"  MCP tools found: {len(tools)}")
        for t in tools:
            print(f"    {t}")

    print(f"\n  Expected gateway URL: ws://192.168.50.133:8090/ws/device")
    return buf

if __name__ == "__main__":
    print("=" * 60)
    print("StackChan Action Gateway - Full Check")
    print("=" * 60)

    # 1. Health
    ok = check_health()
    if not ok:
        print("Agent service not running. Start Docker first.")
        sys.exit(1)

    # 2. MCP tools
    check_mcp_tools()

    # 3. COM7 serial (run in background while we also do MCP)
    print()
    com_result = check_com7(15)

    # 4. Try robot action
    print()
    send_robot_action("wave", {"motion": "happy"})

    print("\n" + "=" * 60)
    print("Done. If COM7 shows no 'action gateway connected',")
    print("the firmware URL likely needs updating to:")
    print("  ws://192.168.50.133:8090/ws/device")
    print("=" * 60)
