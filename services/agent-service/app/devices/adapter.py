from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Protocol

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed


class AdapterError(RuntimeError):
    pass


class RobotAdapter(Protocol):
    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]: ...
    async def stop(self, reason: str = "stop") -> dict[str, Any]: ...
    async def close(self) -> None: ...


def _int(value: Any, low: int, high: int, default: int) -> int:
    value = default if value is None else int(value)
    if not low <= value <= high:
        raise AdapterError(f"unsafe_value:{value}")
    return value


def _float(value: Any, low: float, high: float, default: float) -> float:
    value = default if value is None else float(value)
    if not low <= value <= high:
        raise AdapterError(f"unsafe_value:{value}")
    return value


class MockRobotAdapter:
    supported = {"blink", "nod", "shake_head", "look_at_user", "think", "wave", "celebrate", "dance", "farm_tend", "base_move", "base_turn", "base_drive", "base_stop", "stop"}

    def __init__(self, delay_ms: int = 50) -> None:
        self.delay = max(0, delay_ms) / 1000

    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if intent not in self.supported:
            return {"status": "failed", "error": f"unsupported_intent:{intent}", "measuredResult": {}}
        await asyncio.sleep(max(self.delay, 0.5 if intent in {"dance", "celebrate"} else 0))
        return {"status": "completed", "error": None, "measuredResult": {"adapter": "mock", "intent": intent, "parameters": parameters, "transportAccepted": True, "physicalConfirmed": True}}

    async def stop(self, reason: str = "stop") -> dict[str, Any]:
        return {"status": "completed", "error": None, "measuredResult": {"adapter": "mock", "physicalConfirmed": True}}

    async def close(self) -> None:
        return None


class StackChanWebSocketAdapter:
    """Translate semantic actions to MCP JSON-RPC StackChan calls."""

    supported = MockRobotAdapter.supported

    def __init__(self, url: str, *, token: str = "", connect_timeout: float = 10, max_speed: int = 180, max_duration_seconds: float = 1.5) -> None:
        self.url, self.token = url, token
        self.connect_timeout = connect_timeout
        self.max_speed = max(1, min(max_speed, 180))
        self.max_duration = max(0.05, min(max_duration_seconds, 1.5))
        self.socket: Any = None
        self.lock = asyncio.Lock()
        self.rpc_id = 0

    async def _socket(self) -> Any:
        if self.socket is None:
            kwargs: dict[str, Any] = {"open_timeout": self.connect_timeout, "ping_interval": 20, "ping_timeout": 10}
            if self.token:
                kwargs["additional_headers"] = {"Authorization": f"Bearer {self.token}"}
            try:
                self.socket = await connect(self.url, **kwargs)
            except Exception as exc:
                raise AdapterError(f"stackchan_connect_failed:{exc}") from exc
        return self.socket

    async def _call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with self.lock:
            socket = await self._socket()
            self.rpc_id += 1
            try:
                await socket.send(json.dumps({"jsonrpc": "2.0", "id": self.rpc_id, "method": "tools/call", "params": {"name": f"self.robot.{name}", "arguments": arguments}}))
            except (ConnectionClosed, OSError) as exc:
                await self.close()
                raise AdapterError(f"stackchan_send_failed:{exc}") from exc
            return {"transportAccepted": True, "physicalConfirmed": False, "tool": name}

    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            if intent not in self.supported:
                raise AdapterError(f"unsupported_intent:{intent}")
            if intent in {"blink", "wave", "celebrate", "dance", "farm_tend", "think"}:
                calls = [await self._call("play_motion", {"name": str(parameters.get("motion", "happy"))})]
            elif intent == "nod":
                speed = _int(parameters.get("speed"), 100, 1000, 300)
                calls = [await self._call("set_head_angles", {"yaw": 0, "pitch": 15, "speed": speed}), await self._call("set_head_angles", {"yaw": 0, "pitch": 0, "speed": speed})]
            elif intent == "shake_head":
                speed = _int(parameters.get("speed"), 100, 1000, 300)
                calls = [await self._call("set_head_angles", {"yaw": -20, "pitch": 0, "speed": speed}), await self._call("set_head_angles", {"yaw": 20, "pitch": 0, "speed": speed}), await self._call("set_head_angles", {"yaw": 0, "pitch": 0, "speed": speed})]
            elif intent == "look_at_user":
                calls = [await self._call("set_head_angles", {"yaw": _int(parameters.get("yaw"), -90, 90, 0), "pitch": _int(parameters.get("pitch"), -45, 45, 0), "speed": _int(parameters.get("speed"), 100, 1000, 300)})]
            elif intent in {"base_move", "base_turn"}:
                duration = _float(parameters.get("durationSeconds"), 0.05, self.max_duration, 0.5)
                speed = _int(parameters.get("speed"), 1, self.max_speed, min(100, self.max_speed))
                calls = [await self._call("base_move", {"direction": str(parameters.get("direction", "forward")), "speed": speed})]
                await asyncio.sleep(duration)
                calls.append(await self._call("base_stop", {}))
            elif intent == "base_drive":
                duration = _float(parameters.get("durationSeconds"), 0.05, self.max_duration, 0.5)
                calls = [await self._call("base_drive", {"left": _int(parameters.get("left"), -self.max_speed, self.max_speed, 0), "right": _int(parameters.get("right"), -self.max_speed, self.max_speed, 0)})]
                await asyncio.sleep(duration)
                calls.append(await self._call("base_stop", {}))
            else:
                calls = [await self._call("stop_motion", {}), await self._call("base_stop", {})]
            return {"status": "dispatched", "error": None, "measuredResult": {"adapter": "stackchan-websocket", "transportAccepted": True, "physicalConfirmed": False, "commands": calls}}
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            return {"status": "failed", "error": str(exc), "measuredResult": {"adapter": "stackchan-websocket", "transportAccepted": False, "physicalConfirmed": False}}

    async def stop(self, reason: str = "stop") -> dict[str, Any]:
        if self.socket is not None:
            try:
                await self._call("stop_motion", {})
                await self._call("base_stop", {})
                return {"status": "dispatched", "error": None, "measuredResult": {"adapter": "stackchan-websocket", "physicalConfirmed": False}}
            except Exception:
                await self.close()
                return {"status": "failed", "error": "stackchan_stop_failed", "measuredResult": {"adapter": "stackchan-websocket", "physicalConfirmed": False}}
        return {"status": "failed", "error": "stackchan_not_connected", "measuredResult": {"adapter": "stackchan-websocket", "physicalConfirmed": False}}

    async def close(self) -> None:
        socket, self.socket = self.socket, None
        if socket is not None:
            await socket.close()


class ActionDispatcher:
    def __init__(self, adapter: RobotAdapter, device_id: str) -> None:
        self.adapter, self.device_id = adapter, device_id

    async def dispatch(self, action: dict[str, Any], source_event_id: str | None = None) -> dict[str, Any]:
        started = datetime.now(timezone.utc).isoformat()
        intent = str(action.get("intent", ""))
        parameters = action.get("parameters") if isinstance(action.get("parameters"), dict) else {}
        outcome = await self.adapter.execute(intent, parameters)
        return {"version": "1.0", "actionId": str(action.get("actionId", uuid.uuid4())), "deviceId": self.device_id, "actionType": intent, "status": outcome.get("status", "failed"), "startedAt": started, "completedAt": datetime.now(timezone.utc).isoformat(), "requestedParameters": parameters, "measuredResult": outcome.get("measuredResult", {}), "error": outcome.get("error"), "sourceEventId": source_event_id}

    async def stop(self, reason: str = "stop") -> dict[str, Any]:
        return await self.adapter.stop(reason)

    async def close(self) -> None:
        await self.adapter.close()
