"""Unified smoke test for the AR-AIPet agent-service.

Connects to /ws/device (as the device) and /ws/app (as the app), sends a
device.hello, subscribes to experience events, sends an agent.chat, and
verifies that the agent dispatches a robot action and returns a result.

Unlike a bare timeout, this script tracks which protocol phases completed
and prints a clear diagnostic when the smoke fails, so the operator knows
whether the issue is 'agent not responding', 'no device session', or
'action not dispatched'.

Usage: python scripts/unified_smoke.py
Env:  UNIFIED_WS_BASE=ws://localhost:8090 (default)
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid

import websockets


BASE = os.getenv("UNIFIED_WS_BASE", "ws://localhost:8090")
TIMEOUT_SECONDS = float(os.getenv("UNIFIED_SMOKE_TIMEOUT", "10"))


async def main() -> None:
    phases: dict[str, bool] = {
        "device.hello": False,
        "experience.subscribe": False,
        "agent.accepted": False,
        "robot.action.request": False,
        "experience.action.result": False,
        "agent.result": False,
    }

    try:
        async with websockets.connect(BASE + "/ws/device") as device, \
                   websockets.connect(BASE + "/ws/app") as app:
            # Phase 1: device hello
            await device.send(json.dumps({
                "requestId": "hello-" + uuid.uuid4().hex,
                "type": "device.hello",
                "payload": {
                    "deviceId": "stackchan-robot",
                    "capabilities": ["nod", "dance", "stop"],
                },
            }))
            hello = json.loads(await asyncio.wait_for(device.recv(), timeout=5))
            assert hello["type"] == "device.hello.result", hello
            phases["device.hello"] = True

            # Phase 2: subscribe
            subscribe_id = "subscribe-" + uuid.uuid4().hex
            await app.send(json.dumps({
                "requestId": subscribe_id,
                "type": "experience.subscribe",
                "payload": {},
            }))
            subscribed = json.loads(await asyncio.wait_for(app.recv(), timeout=5))
            assert subscribed["type"] == "experience.subscribe.result" and subscribed["status"] == "ok", subscribed
            phases["experience.subscribe"] = True

            # Phase 3: send agent chat
            request_id = "chat-" + uuid.uuid4().hex
            await app.send(json.dumps({
                "requestId": request_id,
                "type": "agent.chat",
                "payload": {"text": "跳舞"},
            }))

            # Phases 4-6: wait for action request, action result, agent result
            deadline = asyncio.get_running_loop().time() + TIMEOUT_SECONDS
            while not (phases["agent.result"] and phases["experience.action.result"]):
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    break
                app_task = asyncio.create_task(app.recv())
                device_task = asyncio.create_task(device.recv())
                done, pending = await asyncio.wait(
                    {app_task, device_task},
                    timeout=remaining,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if not done:
                    break
                for task in done:
                    message = json.loads(task.result())
                    mtype = message.get("type", "")
                    if mtype == "agent.accepted":
                        phases["agent.accepted"] = True
                    elif mtype == "robot.action.request":
                        phases["robot.action.request"] = True
                        payload = message.get("payload", {})
                        await device.send(json.dumps({
                            "requestId": message.get("requestId"),
                            "type": "robot.action.result",
                            "payload": {
                                "result": {
                                    "actionId": payload.get("actionId"),
                                    "status": "dispatched",
                                    "measuredResult": {
                                        "transportAccepted": True,
                                        "physicalConfirmed": False,
                                    },
                                },
                            },
                        }))
                    elif mtype == "experience.action.result":
                        phases["experience.action.result"] = True
                    elif mtype == "agent.result":
                        phases["agent.result"] = True
                for task in pending:
                    task.cancel()

    except Exception as exc:
        print(f"UNIFIED_SMOKE_ERROR: {exc}")
        _print_diagnostic(phases)
        raise

    if not phases["agent.result"]:
        print("UNIFIED_SMOKE_FAIL: agent did not return a result")
        _print_diagnostic(phases)
        raise SystemExit(1)

    if not phases["robot.action.request"]:
        print("UNIFIED_SMOKE_FAIL: agent did not dispatch a robot action")
        _print_diagnostic(phases)
        raise SystemExit(1)

    print("UNIFIED_SMOKE_OK", json.dumps(phases))


def _print_diagnostic(phases: dict[str, bool]) -> None:
    print("Phase tracking:")
    for phase, ok in phases.items():
        mark = "OK" if ok else "MISSING"
        print(f"  {phase}: {mark}")

    if not phases["device.hello"]:
        print("DIAGNOSTIC: The /ws/device endpoint did not respond to device.hello.")
        print("  -> Is the unified agent-service running on port 8090?")
        print("  -> Check: docker compose --profile unified up -d")
    elif not phases["agent.accepted"]:
        print("DIAGNOSTIC: The agent did not accept the chat message.")
        print("  -> Is AGENT_PROVIDER set to 'mock' or a valid LLM provider?")
        print("  -> Check service logs for agent errors.")
    elif not phases["robot.action.request"]:
        print("DIAGNOSTIC: The agent responded but did not dispatch a robot action.")
        print("  -> The agent may not have the right tools or persona configured.")
        print("  -> If a REAL StackChan is expected to be the device,")
        print("     the smoke test itself is acting as the simulated device.")
        print("     A real device session is separate — check /health/device.")
    elif not phases["experience.action.result"]:
        print("DIAGNOSTIC: The action result was not recorded.")
        print("  -> Check data-service connectivity and experience hub state.")


if __name__ == "__main__":
    asyncio.run(main())
