from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed


LOG = logging.getLogger("robot-bridge")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


class AdapterError(RuntimeError):
    """The semantic action could not be dispatched to the device gateway."""


class RobotAdapter(Protocol):
    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]:
        ...

    async def stop(self, reason: str = "stop") -> None:
        ...

    async def close(self) -> None:
        ...


def _bounded_int(value: Any, *, name: str, low: int, high: int, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise AdapterError(f"invalid_{name}") from exc
    if number < low or number > high:
        raise AdapterError(f"unsafe_{name}:{number}")
    return number


def _bounded_float(value: Any, *, name: str, low: float, high: float, default: float) -> float:
    try:
        number = default if value is None else float(value)
    except (TypeError, ValueError) as exc:
        raise AdapterError(f"invalid_{name}") from exc
    if number < low or number > high:
        raise AdapterError(f"unsafe_{name}:{number}")
    return number


class MockRobotAdapter:
    """Semantic adapter used by local development and CI.

    It deliberately accepts intents, not servo/PWM/motor details. The same
    bridge contract is used by ``StackChanWebSocketAdapter`` in real mode.
    """

    supported = {
        "blink",
        "nod",
        "shake_head",
        "look_at_user",
        "think",
        "wave",
        "celebrate",
        "dance",
        "farm_tend",
        "base_move",
        "base_turn",
        "base_drive",
        "base_stop",
        "stop",
    }

    def __init__(self, delay_ms: int = 50) -> None:
        self.delay_ms = max(0, delay_ms)

    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if intent not in self.supported:
            return {"status": "failed", "error": f"unsupported_intent:{intent}", "measuredResult": {}}
        delay = self.delay_ms / 1000
        if intent in {"dance", "celebrate"}:
            delay = max(delay, 0.5)
        await asyncio.sleep(delay)
        return {
            "status": "completed",
            "error": None,
            "measuredResult": {
                "adapter": "mock",
                "intent": intent,
                "parameters": parameters,
                "transportAccepted": True,
                "physicalConfirmed": True,
            },
        }

    async def stop(self, reason: str = "stop") -> None:
        LOG.info("mock stop: %s", reason)

    async def close(self) -> None:
        return None


class StackChanWebSocketAdapter:
    """Translate semantic intents into StackChan MCP JSON-RPC calls.

    The official StackChan WebSocket accepts MCP calls but normally does not
    return a physical completion result. Consequently successful writes are
    reported as ``dispatched`` with ``physicalConfirmed=false``. A response
    timeout can be enabled for gateways that do return an MCP response, but an
    MCP response is still only transport/gateway acknowledgement.
    """

    supported = {
        "blink",
        "nod",
        "shake_head",
        "look_at_user",
        "think",
        "wave",
        "celebrate",
        "dance",
        "farm_tend",
        "base_move",
        "base_turn",
        "base_drive",
        "base_stop",
        "stop",
    }
    _directions = {"forward", "backward", "left", "right"}

    def __init__(
        self,
        url: str,
        *,
        token: str = "",
        connect_timeout: float = 10.0,
        response_timeout: float = 0.0,
        max_speed: int = 180,
        max_duration_seconds: float = 1.5,
    ) -> None:
        self.url = url
        self.token = token
        self.connect_timeout = max(1.0, connect_timeout)
        self.response_timeout = max(0.0, response_timeout)
        self.max_speed = max(1, min(180, max_speed))
        self.max_duration_seconds = max(0.05, min(1.5, max_duration_seconds))
        self.socket: ClientConnection | None = None
        self._lock = asyncio.Lock()
        self._rpc_id = 0

    async def _ensure_socket(self) -> ClientConnection:
        if self.socket is not None:
            return self.socket
        kwargs: dict[str, Any] = {
            "open_timeout": self.connect_timeout,
            "ping_interval": 20,
            "ping_timeout": 10,
        }
        if self.token:
            kwargs["additional_headers"] = {"Authorization": f"Bearer {self.token}"}
        try:
            self.socket = await connect(self.url, **kwargs)
        except Exception as exc:
            raise AdapterError(f"stackchan_connect_failed:{exc}") from exc
        LOG.info("connected to StackChan gateway %s", self.url)
        return self.socket

    async def _call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            socket = await self._ensure_socket()
            self._rpc_id += 1
            message = {
                "jsonrpc": "2.0",
                "id": self._rpc_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }
            try:
                await socket.send(json.dumps(message, ensure_ascii=False))
            except (ConnectionClosed, OSError) as exc:
                await self.close()
                raise AdapterError(f"stackchan_send_failed:{exc}") from exc

            result: dict[str, Any] = {
                "transportAccepted": True,
                "physicalConfirmed": False,
                "responseReceived": False,
                "tool": tool_name,
            }
            if self.response_timeout <= 0:
                return result
            try:
                raw = await asyncio.wait_for(socket.recv(), timeout=self.response_timeout)
            except asyncio.TimeoutError:
                return result
            except (ConnectionClosed, OSError) as exc:
                await self.close()
                raise AdapterError(f"stackchan_receive_failed:{exc}") from exc
            try:
                response = json.loads(raw)
            except json.JSONDecodeError:
                result["responseReceived"] = True
                result["gatewayResponse"] = {"raw": str(raw)[:500]}
                return result
            if isinstance(response, dict) and response.get("error"):
                raise AdapterError(f"stackchan_gateway_error:{response['error']}")
            result["responseReceived"] = True
            result["gatewayResponse"] = response
            return result

    @staticmethod
    def _tool(name: str, arguments: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return (f"self.robot.{name}", arguments)

    def _commands(self, intent: str, parameters: dict[str, Any]) -> tuple[list[tuple[str, dict[str, Any]]], float]:
        if intent not in self.supported:
            raise AdapterError(f"unsupported_intent:{intent}")
        if intent in {"blink", "wave", "celebrate", "dance", "farm_tend", "think"}:
            motion = str(parameters.get("motion") or {
                "blink": "robot",
                "wave": "look_around",
                "celebrate": "happy",
                "dance": "happy",
                "farm_tend": "robot",
                "think": "robot",
            }[intent])
            return [self._tool("play_motion", {"name": motion})], 0.0
        if intent == "nod":
            speed = _bounded_int(parameters.get("speed"), name="speed", low=100, high=1000, default=300)
            pause = _bounded_float(parameters.get("pauseSeconds"), name="pauseSeconds", low=0.0, high=0.25, default=0.08)
            return [
                self._tool("set_head_angles", {"yaw": 0, "pitch": 15, "speed": speed}),
                self._tool("set_head_angles", {"yaw": 0, "pitch": 0, "speed": speed}),
            ], pause
        if intent == "shake_head":
            speed = _bounded_int(parameters.get("speed"), name="speed", low=100, high=1000, default=300)
            pause = _bounded_float(parameters.get("pauseSeconds"), name="pauseSeconds", low=0.0, high=0.25, default=0.08)
            return [
                self._tool("set_head_angles", {"yaw": -20, "pitch": 0, "speed": speed}),
                self._tool("set_head_angles", {"yaw": 20, "pitch": 0, "speed": speed}),
                self._tool("set_head_angles", {"yaw": 0, "pitch": 0, "speed": speed}),
            ], pause
        if intent == "look_at_user":
            speed = _bounded_int(parameters.get("speed"), name="speed", low=100, high=1000, default=300)
            yaw = _bounded_int(parameters.get("yaw"), name="yaw", low=-90, high=90, default=0)
            pitch = _bounded_int(parameters.get("pitch"), name="pitch", low=-45, high=45, default=0)
            return [self._tool("set_head_angles", {"yaw": yaw, "pitch": pitch, "speed": speed})], 0.0
        if intent in {"base_move", "base_turn"}:
            direction = str(parameters.get("direction") or ("left" if intent == "base_turn" else "forward"))
            if direction not in self._directions:
                raise AdapterError(f"invalid_direction:{direction}")
            base_speed = _bounded_int(parameters.get("speed"), name="base_speed", low=1, high=self.max_speed, default=min(100, self.max_speed))
            duration = _bounded_float(
                parameters.get("durationSeconds"),
                name="durationSeconds",
                low=0.05,
                high=self.max_duration_seconds,
                default=min(0.5, self.max_duration_seconds),
            )
            return [self._tool("base_move", {"direction": direction, "speed": base_speed})], duration
        if intent == "base_drive":
            left = _bounded_int(parameters.get("left"), name="left", low=-self.max_speed, high=self.max_speed, default=0)
            right = _bounded_int(parameters.get("right"), name="right", low=-self.max_speed, high=self.max_speed, default=0)
            duration = _bounded_float(
                parameters.get("durationSeconds"),
                name="durationSeconds",
                low=0.05,
                high=self.max_duration_seconds,
                default=min(0.5, self.max_duration_seconds),
            )
            return [self._tool("base_drive", {"left": left, "right": right})], duration
        if intent in {"base_stop", "stop"}:
            if intent == "base_stop":
                return [self._tool("base_stop", {})], 0.0
            return [self._tool("stop_motion", {}), self._tool("base_stop", {})], 0.0
        raise AdapterError(f"unsupported_intent:{intent}")

    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            commands, pause_or_duration = self._commands(intent, parameters)
            calls: list[dict[str, Any]] = []
            for index, (tool, arguments) in enumerate(commands):
                calls.append(await self._call(tool, arguments))
                if pause_or_duration and index < len(commands) - 1:
                    await asyncio.sleep(pause_or_duration)
            if intent in {"base_move", "base_turn", "base_drive"}:
                await asyncio.sleep(pause_or_duration)
                calls.append(await self._call("self.robot.base_stop", {}))
            return {
                "status": "dispatched",
                "error": None,
                "measuredResult": {
                    "adapter": "stackchan-websocket",
                    "transportAccepted": all(item.get("transportAccepted") for item in calls),
                    "physicalConfirmed": False,
                    "confirmationReason": "stackchan_gateway_has_no_physical_feedback",
                    "commands": calls,
                },
            }
        except asyncio.CancelledError:
            raise
        except AdapterError as exc:
            return {
                "status": "failed",
                "error": str(exc),
                "measuredResult": {
                    "adapter": "stackchan-websocket",
                    "transportAccepted": False,
                    "physicalConfirmed": False,
                },
            }

    async def stop(self, reason: str = "stop") -> None:
        LOG.info("StackChan stop: %s", reason)
        if self.socket is None:
            LOG.info("StackChan stop skipped: gateway socket is not connected")
            return
        try:
            await self._call("self.robot.stop_motion", {})
            await self._call("self.robot.base_stop", {})
        except AdapterError as exc:
            LOG.warning("StackChan stop could not be dispatched: %s", exc)

    async def close(self) -> None:
        socket = self.socket
        self.socket = None
        if socket is not None:
            try:
                await socket.close()
            except Exception:
                LOG.debug("StackChan socket close failed", exc_info=True)


@dataclass
class RunningAction:
    action_id: str
    event_id: str | None
    task: asyncio.Task[None]


class RobotBridge:
    def __init__(self, url: str, device_id: str, adapter: RobotAdapter) -> None:
        self.url = url
        self.device_id = device_id
        self.adapter = adapter
        self.running: dict[str, RunningAction] = {}
        self.socket: ClientConnection | None = None

    async def send(self, message_type: str, payload: dict[str, Any] | None = None) -> None:
        if self.socket is None:
            return
        await self.socket.send(json.dumps({
            "requestId": request_id("bridge"),
            "type": message_type,
            "payload": payload or {},
        }, ensure_ascii=False))

    async def subscribe(self) -> None:
        await self.send("experience.subscribe", {"deviceId": self.device_id})
        LOG.info("subscribed to Agent Gateway as %s", self.device_id)

    async def run_action(self, action: dict[str, Any], source_event_id: str | None) -> None:
        action_id = str(action.get("actionId", ""))
        intent = str(action.get("intent", ""))
        parameters = action.get("parameters") if isinstance(action.get("parameters"), dict) else {}
        started = now_iso()
        try:
            outcome = await self.adapter.execute(intent, parameters)
        except asyncio.CancelledError:
            await self.report(action_id, intent, "cancelled", started, None, parameters, {"cancelled": True}, source_event_id, "cancelled")
            raise
        except Exception as exc:  # pragma: no cover - defensive adapter boundary
            LOG.exception("adapter failed action=%s", action_id)
            await self.report(action_id, intent, "failed", started, now_iso(), parameters, {}, source_event_id, str(exc))
            return
        await self.report(
            action_id,
            intent,
            outcome["status"],
            started,
            now_iso(),
            parameters,
            outcome.get("measuredResult", {}),
            source_event_id,
            outcome.get("error"),
        )

    async def report(
        self,
        action_id: str,
        intent: str,
        status: str,
        started: str | None,
        completed: str | None,
        requested: dict[str, Any],
        measured: dict[str, Any],
        source_event_id: str | None,
        error: str | None,
    ) -> None:
        result = {
            "version": "1.0",
            "actionId": action_id,
            "deviceId": self.device_id,
            "actionType": intent,
            "status": status,
            "startedAt": started,
            "completedAt": completed,
            "requestedParameters": requested,
            "measuredResult": measured,
            "error": error,
            "sourceEventId": source_event_id,
        }
        await self.send("experience.action.result", {"result": result})
        LOG.info("action result action=%s intent=%s status=%s", action_id, intent, status)

    async def stop_all(self, reason: str = "stop") -> None:
        actions = list(self.running.values())
        for current in actions:
            if not current.task.done():
                current.task.cancel()
        if actions:
            await asyncio.gather(*(current.task for current in actions), return_exceptions=True)
        self.running.clear()
        await self.adapter.stop(reason)
        LOG.info("stopped %d action(s): %s", len(actions), reason)

    async def handle_event(self, event: dict[str, Any]) -> None:
        robot = event.get("robot") if isinstance(event.get("robot"), dict) else {}
        actions = robot.get("actions") if isinstance(robot.get("actions"), list) else []
        event_id = event.get("eventId")
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_id = str(action.get("actionId", ""))
            if not action_id or action_id in self.running:
                continue
            task = asyncio.create_task(self.run_action(action, event_id))
            self.running[action_id] = RunningAction(action_id, event_id, task)
            task.add_done_callback(lambda _, current_action_id=action_id: self.running.pop(current_action_id, None))

    async def handle_message(self, message: dict[str, Any]) -> None:
        message_type = message.get("type")
        payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
        if message_type == "experience.event":
            await self.handle_event(payload)
        elif message_type == "experience.cancelled":
            await self.stop_all("event_cancelled")
        elif message_type == "robot.command.stop":
            await self.stop_all("remote_stop")

    async def connected_loop(self) -> None:
        async with connect(self.url, open_timeout=10, ping_interval=20, ping_timeout=10) as socket:
            self.socket = socket
            await self.subscribe()
            async for raw in socket:
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    LOG.warning("ignored non-JSON Agent message")
                    continue
                if isinstance(message, dict):
                    await self.handle_message(message)

    async def run_forever(self) -> None:
        retry_seconds = max(1, int(os.getenv("BRIDGE_RETRY_SECONDS", "2")))
        while True:
            try:
                await self.connected_loop()
            except (ConnectionClosed, OSError, asyncio.TimeoutError) as exc:
                LOG.warning("Agent connection lost: %s", exc)
            except Exception:
                LOG.exception("bridge loop failed")
            finally:
                self.socket = None
                await self.stop_all("gateway_disconnected")
                await self.adapter.close()
            await asyncio.sleep(retry_seconds)


def create_adapter() -> RobotAdapter:
    mode = os.getenv("ROBOT_ADAPTER", "mock").strip().lower()
    if mode == "stackchan":
        return StackChanWebSocketAdapter(
            os.getenv("STACKCHAN_WS_URL", "ws://127.0.0.1:8080/ws"),
            token=os.getenv("STACKCHAN_TOKEN", ""),
            connect_timeout=float(os.getenv("STACKCHAN_CONNECT_TIMEOUT_SECONDS", "10")),
            response_timeout=float(os.getenv("STACKCHAN_RESPONSE_TIMEOUT_SECONDS", "0")),
            max_speed=int(os.getenv("STACKCHAN_MAX_SPEED", "180")),
            max_duration_seconds=float(os.getenv("STACKCHAN_MAX_DURATION_SECONDS", "1.5")),
        )
    if mode != "mock":
        raise ValueError(f"unsupported ROBOT_ADAPTER: {mode}")
    return MockRobotAdapter(int(os.getenv("MOCK_ACTION_DELAY_MS", "50")))


async def main() -> None:
    bridge = RobotBridge(
        os.getenv("AGENT_GATEWAY_WS_URL", "ws://127.0.0.1:8082/ws"),
        os.getenv("ROBOT_DEVICE_ID", "mock-robot"),
        create_adapter(),
    )
    await bridge.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
