from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
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

    async def next_command(self) -> dict[str, Any]:
        assert self.socket is not None
        while True:
            message = json.loads(await self.socket.recv())
            if message.get("type", "").startswith("robot.command"):
                payload = message.get("payload") or {}
                if payload.get("deviceId") in {None, self.device_id}:
                    return payload

    async def _send_result(self, result: dict[str, Any]) -> dict[str, Any]:
        assert self.socket is not None
        request_id = f"action-{uuid.uuid4().hex}"
        await self.socket.send(json.dumps({"requestId": request_id, "type": "experience.action.result", "payload": {"result": result}}))
        while True:
            message = json.loads(await self.socket.recv())
            if message.get("requestId") == request_id:
                assert message.get("status") == "ok", message
                return message.get("payload") or {}

    async def acknowledge(self, event: dict[str, Any], action_type: str, *, final_status: str = "completed") -> list[dict[str, Any]]:
        action = self._event_action(event)
        action_id = action.get("actionId") or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        results = []
        for status in ("accepted", "started", final_status):
            result = {
                "version": "0.1", "actionId": action_id, "deviceId": self.device_id,
                "actionType": action_type, "status": status,
                "startedAt": now if status != "accepted" else None,
                "completedAt": now if status in {"completed", "failed", "cancelled", "timeout"} else None,
                "requestedParameters": action.get("parameters", {}),
                "measuredResult": {"simulated": True},
                "error": None if status not in {"failed", "timeout", "cancelled"} else status,
                "sourceEventId": event["eventId"],
            }
            results.append(await self._send_result(result))
        return results

    async def acknowledge_command(self, command: dict[str, Any], *, final_status: str = "cancelled") -> list[dict[str, Any]]:
        action = {"actionId": command.get("actionId"), "parameters": {}}
        event = {"eventId": command.get("sourceEventId"), "robot": {"actions": [action]}}
        return await self.acknowledge(event, "stop", final_status=final_status)

    def _event_action(self, event: dict[str, Any]) -> dict[str, Any]:
        if self.device_id.startswith("mock-unity") or self.device_id.startswith("unity"):
            return {"actionId": (event.get("xr") or {}).get("displayActionId"), "parameters": {}}
        return (event.get("robot") or {}).get("actions", [{}])[0]


class MockUnity(MockExperienceClient):
    pass


class MockRobot(MockExperienceClient):
    pass
