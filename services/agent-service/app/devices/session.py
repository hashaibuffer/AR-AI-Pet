from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


@dataclass
class DeviceSession:
    device_id: str
    socket: WebSocket
    capabilities: list[str] = field(default_factory=list)
    pending: dict[str, asyncio.Future[dict[str, Any]]] = field(default_factory=dict)
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    protocol: str = "device-v1"
    session_id: str | None = None


class DeviceSessionManager:
    """Tracks device-initiated sessions without storing device state in MCP."""

    def __init__(self, action_timeout_seconds: float = 0.8) -> None:
        self.sessions: dict[str, DeviceSession] = {}
        self.lock = asyncio.Lock()
        self.action_timeout_seconds = max(0.1, min(float(action_timeout_seconds), 5.0))

    async def register(self, socket: WebSocket, hello: dict[str, Any]) -> DeviceSession:
        device_id = str(hello.get("deviceId") or "stackchan-robot")
        session = DeviceSession(device_id, socket, [str(item) for item in hello.get("capabilities", [])], protocol=str(hello.get("protocol", "device-v1")))
        async with self.lock:
            old = self.sessions.get(device_id)
            if old is not None:
                for pending in old.pending.values():
                    if not pending.done():
                        pending.set_result({"status": "failed", "error": "device_replaced"})
            self.sessions[device_id] = session
        return session

    async def unregister(self, session: DeviceSession) -> None:
        async with self.lock:
            if self.sessions.get(session.device_id) is session:
                self.sessions.pop(session.device_id, None)
        for pending in session.pending.values():
            if not pending.done():
                pending.set_result({"status": "failed", "error": "device_disconnected"})

    async def dispatch(self, device_id: str, action: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        session = self.sessions.get(device_id)
        if session is None:
            return {"status": "failed", "error": "device_not_connected", "measuredResult": {"transportAccepted": False, "physicalConfirmed": False}}
        action_id = str(action.get("actionId") or uuid.uuid4())
        if session.protocol == "scheme-b":
            rpc = self._scheme_b_call(action_id, action)
            message = {"type": "mcp", "session_id": session.session_id, "payload": rpc}
        else:
            message = {"version": "1.0", "requestId": str(uuid.uuid4()), "type": "robot.action.request", "timestamp": datetime.now(timezone.utc).isoformat(), "payload": {**action, "actionId": action_id}}
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        session.pending[action_id] = future
        timeout = self.action_timeout_seconds if timeout is None else max(0.1, min(float(timeout), 5.0))
        try:
            async with session.send_lock:
                await session.socket.send_text(json.dumps(message, ensure_ascii=False))
            try:
                result = await asyncio.wait_for(future, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                return {"status": "dispatched", "error": None, "measuredResult": {"transportAccepted": True, "physicalConfirmed": False, "confirmationReason": "device_ack_timeout"}}
        except Exception as exc:
            return {"status": "failed", "error": str(exc), "measuredResult": {"transportAccepted": False, "physicalConfirmed": False}}
        finally:
            session.pending.pop(action_id, None)

    @staticmethod
    def _scheme_b_call(action_id: str, action: dict[str, Any]) -> dict[str, Any]:
        intent = str(action.get("intent", ""))
        parameters = action.get("parameters") if isinstance(action.get("parameters"), dict) else {}
        if intent == "nod":
            name, arguments = "self.robot.set_head_angles", {"yaw": 0, "pitch": 15, "speed": int(parameters.get("speed", 300))}
        elif intent in {"dance", "celebrate", "wave", "farm_tend"}:
            name, arguments = "self.robot.play_motion", {"name": str(parameters.get("motion", "happy"))}
        elif intent in {"base_move", "base_turn"}:
            name, arguments = "self.robot.base_move", {"direction": str(parameters.get("direction", "forward")), "speed": min(180, int(parameters.get("speed", 100)))}
        elif intent == "base_drive":
            name, arguments = "self.robot.base_drive", {"left": max(-180, min(180, int(parameters.get("left", 0)))), "right": max(-180, min(180, int(parameters.get("right", 0))))}
        elif intent in {"stop", "base_stop"}:
            name, arguments = "self.robot.base_stop", {}
        else:
            name, arguments = "self.robot.set_head_angles", {"yaw": int(parameters.get("yaw", 0)), "pitch": int(parameters.get("pitch", 0)), "speed": 300}
        return {"jsonrpc": "2.0", "id": action_id, "method": "tools/call", "params": {"name": name, "arguments": arguments}}

    async def stop(self, device_id: str, reason: str = "stop") -> dict[str, Any]:
        return await self.dispatch(device_id, {"actionId": str(uuid.uuid4()), "intent": "stop", "parameters": {"reason": reason}})

    async def handle(self, socket: WebSocket) -> None:
        await socket.accept()
        session: DeviceSession | None = None
        try:
            while True:
                message = json.loads(await socket.receive_text())
                message_type = message.get("type")
                payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
                if message_type in {"device.hello", "device.register"}:
                    session = await self.register(socket, payload)
                    await socket.send_json({"requestId": message.get("requestId"), "type": "device.hello.result", "status": "ok", "payload": {"deviceId": session.device_id, "connected": True}})
                elif message_type == "hello":
                    headers = socket.headers
                    # Use ROBOT_DEVICE_ID so dispatch can find this session.
                    # The firmware sends its MAC as Device-Id header, but
                    # DeviceSessionRobotAdapter looks up by ROBOT_DEVICE_ID.
                    from ..settings import ROBOT_DEVICE_ID
                    hello = {"deviceId": ROBOT_DEVICE_ID, "capabilities": ["mcp"], "protocol": "scheme-b"}
                    session = await self.register(socket, hello)
                    session.session_id = uuid.uuid4().hex
                    await socket.send_json({"type": "hello", "version": 1, "session_id": session.session_id})
                elif message_type in {"ping", "device.heartbeat"}:
                    await socket.send_json({"requestId": message.get("requestId"), "type": "pong", "status": "ok", "payload": {"deviceId": session.device_id if session else None}})
                elif message_type in {"robot.action.result", "device.action.result"} and session is not None:
                    result = payload.get("result") if isinstance(payload.get("result"), dict) else payload
                    action_id = str(result.get("actionId", ""))
                    future = session.pending.get(action_id)
                    if future is not None and not future.done():
                        future.set_result(result)
                elif message_type == "mcp" and session is not None:
                    result = payload if isinstance(payload, dict) else {}
                    action_id = str(result.get("id", ""))
                    future = session.pending.get(action_id)
                    if future is not None and not future.done():
                        future.set_result({"status": "dispatched", "error": None, "measuredResult": {"transportAccepted": True, "physicalConfirmed": False, "gatewayResponse": result}})
        except WebSocketDisconnect:
            return
        finally:
            if session is not None:
                await self.unregister(session)


class DeviceSessionRobotAdapter:
    def __init__(self, sessions: DeviceSessionManager, device_id: str) -> None:
        self.sessions, self.device_id = sessions, device_id

    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]:
        return await self.sessions.dispatch(self.device_id, {"intent": intent, "parameters": parameters})

    async def stop(self, reason: str = "stop") -> dict[str, Any]:
        return await self.sessions.stop(self.device_id, reason)

    async def close(self) -> None:
        return None
