from __future__ import annotations

import asyncio
import json
import os
import uuid

from websockets.asyncio.client import connect


async def main() -> None:
    agent_url = os.getenv("AGENT_GATEWAY_WS_URL", "ws://127.0.0.1:8082/ws")
    data_url = os.getenv("DATA_SERVICE_WS_URL", "ws://data-service:8080/ws")
    event = None
    async with connect(agent_url, open_timeout=10) as socket:
        request_id = f"bridge-smoke-{uuid.uuid4().hex}"
        await socket.send(json.dumps({"requestId": request_id, "type": "experience.subscribe", "payload": {"deviceId": "mock-robot"}}))
        await socket.send(json.dumps({"requestId": f"chat-{uuid.uuid4().hex}", "type": "agent.chat", "payload": {"text": "请点头回应我"}}))
        deadline = asyncio.get_running_loop().time() + 15
        while asyncio.get_running_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(socket.recv(), timeout=1)
            except asyncio.TimeoutError:
                continue
            message = json.loads(raw)
            if message.get("type") == "experience.event":
                event = message.get("payload")
                break
    if not isinstance(event, dict):
        raise SystemExit("robot bridge smoke did not receive experience.event")

    action_ids = {
        str(action.get("actionId"))
        for action in (event.get("robot") or {}).get("actions", [])
        if isinstance(action, dict) and action.get("actionId")
    }
    if not action_ids:
        raise SystemExit("experience.event did not contain a robot action")

    async with connect(data_url, open_timeout=10) as socket:
        deadline = asyncio.get_running_loop().time() + 10
        while asyncio.get_running_loop().time() < deadline:
            await socket.send(json.dumps({"requestId": f"query-{uuid.uuid4().hex}", "type": "action.query_recent", "payload": {"limit": 20, "deviceId": "mock-robot"}}))
            try:
                raw = await asyncio.wait_for(socket.recv(), timeout=2)
            except asyncio.TimeoutError:
                continue
            payload = (json.loads(raw).get("payload") or {}).get("actions", [])
            if any(str(item.get("actionId")) in action_ids and item.get("status") == "completed" for item in payload):
                print("ROBOT_BRIDGE_SMOKE_OK")
                return
            await asyncio.sleep(0.25)
    raise SystemExit("robot bridge smoke did not observe completed action in data service")


if __name__ == "__main__":
    asyncio.run(main())
