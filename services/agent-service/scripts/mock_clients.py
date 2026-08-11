from __future__ import annotations

import json
import uuid
from typing import Any

import websockets


class MockExperienceClient:
    device_id = "mock-device"

    def __init__(self, url: str, device_id: str) -> None:
        self.url = url
        self.device_id = device_id
        self.socket = None

    async def connect(self) -> None:
        self.socket = await websockets.connect(self.url)
        request_id = f"subscribe-{uuid.uuid4().hex}"
        await self.socket.send(json.dumps({"requestId": request_id, "type": "experience.subscribe", "payload": {"deviceId": self.device_id}}))
        while True:
            message = json.loads(await self.socket.recv())
            if message.get("requestId") == request_id:
                assert message.get("status") == "ok", message
                return

    async def next_event(self) -> dict[str, Any]:
        assert self.socket is not None
        while True:
            message = json.loads(await self.socket.recv())
            if message.get("type") == "experience.event":
                return message["payload"]

    async def acknowledge(self, event: dict[str, Any], action_type: str) -> dict[str, Any]:
        assert self.socket is not None
        now = event["expiresAt"]
        result = {
            "actionId": str(uuid.uuid4()),
            "deviceId": self.device_id,
            "actionType": action_type,
            "status": "completed",
            "startedAt": now,
            "completedAt": now,
            "requestedParameters": {},
            "measuredResult": {"simulated": True},
            "error": None,
            "sourceEventId": event["eventId"],
        }
        request_id = f"action-{uuid.uuid4().hex}"
        await self.socket.send(json.dumps({"requestId": request_id, "type": "experience.action.result", "payload": {"result": result}}))
        while True:
            message = json.loads(await self.socket.recv())
            if message.get("requestId") == request_id:
                assert message.get("status") == "ok", message
                return message.get("payload") or {}


class MockUnity(MockExperienceClient):
    pass


class MockRobot(MockExperienceClient):
    pass
