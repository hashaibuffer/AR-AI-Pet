"""Check StackChan connection status — run on Windows.

This script:
  1. Checks the agent-service health endpoint
  2. Lists MCP tools (if the MCP hub is running)
  3. Reads COM7 serial output and analyses Wi-Fi, gateway URL and AI.AGENT
  4. Sends a test robot action (if the service is up)

Usage: python check_all.py

The expected firmware gateway URL is computed dynamically from this PC's
LAN IP so you can compare it against what the device reports.
"""
import json
import os
import re
import socket
import sys
import time
import urllib.request

BASE = os.getenv("AR_AIPET_BASE", "http://localhost:8090")
UNIFIED_PORT = os.getenv("UNIFIED_PORT", "8090")


def detect_lan_ip():
    """Return this PC's LAN IPv4, or None."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def expected_gateway_url():
    ip = detect_lan_ip()
    if not ip:
        return None
    return f"ws://{ip}:{UNIFIED_PORT}/ws/device"


def check_health():
    try:
        r = urllib.request.urlopen(f"{BASE}/health", timeout=5)
        print(f"[1] Health: {r.read().decode()}")
        return True
    except Exception as e:
        print(f"[1] Health FAILED: {e}")
        return False


def check_device_sessions():
    """Query /health/device to see if a real StackChan is connected."""
    try:
        r = urllib.request.urlopen(f"{BASE}/health/device", timeout=5)
        data = json.loads(r.read().decode())
        count = data.get("sessionCount", 0)
        if count > 0:
            print(f"[2] Device sessions: {count} active")
            for s in data.get("deviceSessions", []):
                print(f"    deviceId={s.get('deviceId')} protocol={s.get('protocol')}")
            return True
        else:
            print("[2] Device sessions: NONE — no real StackChan connected")
            print("    The firmware has not established a /ws/device session.")
            print("    Check: (a) Wi-Fi connected? (b) AI.AGENT app open?")
            return False
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("[2] /health/device not available (unified service not running)")
        else:
            print(f"[2] Device session check FAILED: {e}")
        return False
    except Exception as e:
        print(f"[2] Device session check FAILED: {e}")
        return False


def check_mcp_tools():
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
    req = urllib.request.Request(f"{BASE}/mcp", data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    })
    try:
        r = urllib.request.urlopen(req, timeout=10)
        raw = r.read().decode()
        for line in raw.split('\n'):
            if line.startswith('data:'):
                data = json.loads(line[5:].strip())
                if 'result' in data and 'tools' in data['result']:
                    tools = [t['name'] for t in data['result']['tools']]
                    print(f"[3] MCP tools ({len(tools)} total):")
                    for t in tools:
                        print(f"    {t}")
                    return tools
        print(f"[3] MCP response (raw): {raw[:300]}")
    except Exception as e:
        print(f"[3] MCP tools FAILED: {e}")
    return []


def check_com7(duration=15):
    try:
        import serial
    except ImportError:
        print("[4] pyserial not installed, trying pip install...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pyserial"], capture_output=True)
        import serial

    expected = expected_gateway_url()
    print(f"[4] Reading COM7 for {duration}s (reset StackChan now!)...")
    print(f"    Expected firmware gateway URL: {expected or '<LAN IP not detected>'}")
    try:
        port = serial.Serial("COM7", 115200, timeout=1)
        end = time.time() + duration
        buf = ""
        while time.time() < end:
            data = port.read(4096).decode('utf-8', errors='replace')
            if data:
                buf += data
                sys.stdout.write(data)
                sys.stdout.flush()
        port.close()
    except Exception as e:
        print(f"[4] COM7 error: {e}")
        return ""

    print("\n\n--- COM7 Analysis ---")
    # Wi-Fi
    m = re.search(r'(?:got ip|ip:)\s*[:]*\s*([0-9.]+)', buf, re.I)
    if m:
        print(f"  Wi-Fi: CONNECTED ({m.group(1)})")
    else:
        print("  Wi-Fi: NOT FOUND in output")
        print("  -> Check AP config, 2.4 GHz band, reset procedure")

    # Firmware gateway URL
    device_url = None
    m = re.search(r'connecting action gateway:\s*(\S+)', buf, re.I)
    if m:
        device_url = m.group(1).strip()
        print(f"  Firmware gateway URL: {device_url}")
    elif 'action gateway disabled' in buf.lower():
        print("  Firmware gateway URL: DISABLED (empty Kconfig)")
    else:
        print("  Gateway URL: not found — AI.AGENT app may not be open")
        print("  (Mooncake only starts the action client after requestXiaozhiStart())")

    # Connection status
    if 'action gateway connected' in buf.lower():
        print("  Gateway session: CONNECTED")
    elif 'timed out' in buf.lower() and 'action gateway' in buf.lower():
        print("  Gateway session: TIMEOUT (wrong URL or server not listening)")
    elif 'action gateway' in buf.lower():
        print("  Gateway session: mentioned but unclear")
    else:
        print("  Gateway session: no mention (open AI.AGENT app)")

    # AI.AGENT lifecycle
    if re.search(r'AI\.AGENT|onOpen|requestXiaozhiStart', buf, re.I):
        print("  AI.AGENT lifecycle: mentioned (good)")
    else:
        print("  AI.AGENT lifecycle: NOT mentioned — open the app on device screen")

    # Config comparison
    print()
    if device_url and expected:
        if device_url.rstrip('/') == expected.rstrip('/'):
            print("  CONFIG OK: firmware URL matches expected URL")
        else:
            print("  CONFIG MISMATCH:")
            print(f"    Firmware says:  {device_url}")
            print(f"    PC expects:     {expected}")
            print("    Fix: rebuild firmware or use gateway_config_set.")
            print("    See docs/13-动作网关会话恢复步骤.md")
    elif not device_url:
        print("  Cannot compare: firmware did not report a URL.")
        print("  Steps: (1) confirm Wi-Fi, (2) open AI.AGENT, (3) re-run.")
    else:
        print(f"  Expected URL: {expected or '<LAN IP not detected>'}")

    # MCP tools in serial
    tools = re.findall(r'Add tool:\s*(\S+)', buf)
    if tools:
        print(f"\n  MCP tools in serial ({len(tools)}):")
        for t in tools:
            print(f"    {t}")

    return buf


def send_robot_action(intent, parameters):
    body = json.dumps({
        "jsonrpc": "2.0", "id": 99, "method": "tools/call",
        "params": {"name": "robot.react", "arguments": {"intent": intent, "parameters": parameters}}
    }).encode()
    req = urllib.request.Request(f"{BASE}/mcp", data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    })
    try:
        r = urllib.request.urlopen(req, timeout=15)
        raw = r.read().decode()
        print(f"[5] Action '{intent}' response: {raw[:500]}")
        return raw
    except Exception as e:
        print(f"[5] Action '{intent}' FAILED: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("StackChan Action Gateway - Full Diagnostic")
    print("=" * 60)
    print(f"Service base: {BASE}")
    exp = expected_gateway_url()
    print(f"Expected firmware gateway URL: {exp or '<LAN IP not detected>'}")
    print(f"Known stale firmware config: ws://192.168.50.133:8765 (old Scheme B)")
    print()

    ok = check_health()
    if not ok:
        print("Agent service not running. Start Docker first:")
        print("  docker compose --profile unified up -d")
        print()

    check_device_sessions()
    check_mcp_tools()
    print()
    check_com7(15)
    print()
    if ok:
        send_robot_action("wave", {"motion": "happy"})

    print("\n" + "=" * 60)
    print("Diagnostic complete. If gateway URL mismatches, see:")
    print("  docs/13-动作网关会话恢复步骤.md")
    print("=" * 60)
