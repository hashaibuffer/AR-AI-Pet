from __future__ import annotations

import asyncio
import json
import os
import uuid

import websockets


BASE = os.getenv("UNIFIED_WS_BASE", "ws://localhost:8090")


async def main() -> None:
    async with websockets.connect(BASE + "/ws/device") as device, websockets.connect(BASE + "/ws/app") as app:
        await device.send(json.dumps({"requestId": "hello-" + uuid.uuid4().hex, "type": "device.hello", "payload": {"deviceId": "stackchan-robot", "capabilities": ["nod", "dance", "stop"]}}))
        hello = json.loads(await device.recv())
        assert hello["type"] == "device.hello.result", hello

        subscribe_id = "subscribe-" + uuid.uuid4().hex
        await app.send(json.dumps({"requestId": subscribe_id, "type": "experience.subscribe", "payload": {}}))
        subscribed = json.loads(await app.recv())
        assert subscribed["type"] == "experience.subscribe.result" and subscribed["status"] == "ok", subscribed

        request_id = "chat-" + uuid.uuid4().hex
        await app.send(json.dumps({"requestId": request_id, "type": "agent.chat", "payload": {"text": "跳舞"}}))
        action_seen = False
        result_seen = False
        completed = False
        deadline = asyncio.get_running_loop().time() + 5
        while not (completed and result_seen):
            remaining = deadline - asyncio.get_running_loop().time()
            assert remaining > 0, "timed out waiting for agent and action results"
            app_task = asyncio.create_task(app.recv())
            device_task = asyncio.create_task(device.recv())
            done, pending = await asyncio.wait({app_task, device_task}, timeout=remaining, return_when=asyncio.FIRST_COMPLETED)
            assert done, "timed out waiting for unified event"
            for task in done:
                message = json.loads(task.result())
                if message.get("type") == "robot.action.request":
                    action_seen = True
                    payload = message.get("payload", {})
                    await device.send(json.dumps({"requestId": message.get("requestId"), "type": "robot.action.result", "payload": {"result": {"actionId": payload.get("actionId"), "status": "dispatched", "measuredResult": {"transportAccepted": True, "physicalConfirmed": False}}}}))
                elif message.get("type") == "experience.action.result":
                    result_seen = True
                elif message.get("type") == "agent.result":
                    completed = True
            for task in pending:
                task.cancel()
        assert action_seen, "Agent did not dispatch a device action"
        print("UNIFIED_SMOKE_OK", "action_seen", action_seen, "result_seen", result_seen)


if __name__ == "__main__":
    asyncio.run(main())
