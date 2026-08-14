from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from .scene_mapper import SceneStepMapper


LOG = logging.getLogger("robot-bridge")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@dataclass
class RunningAction:
    action_id: str
    event_id: str | None
    task: asyncio.Task[None]


class MockRobotAdapter:
    """Semantic robot adapter used until StackChan/Base adapters are wired.

    It deliberately accepts intents, not servo/PWM/motor details. The same
    bridge contract can later delegate these methods to StackChanAdapter and
    BaseAdapter without changing the Agent protocol.
    """

    supported = {
        "blink",
        "nod",
        "wave",
        "dance",
        "scene.play",
        "farm_tend",
        "stop",
    }

    def __init__(self, delay_ms: int = 50) -> None:
        self.delay_ms = max(0, delay_ms)
        self.scene_mapper = SceneStepMapper()

    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if intent not in self.supported:
            return {"status": "failed", "error": f"unsupported_intent:{intent}", "measuredResult": {}}
        delay = self.delay_ms / 1000
        if intent == "dance":
            delay = max(delay, 0.5)
        if intent == "scene.play":
            commands = self.scene_mapper.map_scene(parameters)
            requested = int(parameters.get("durationMs", 0) or 0)
            delay = max(delay, min(1.0, max(0, requested) / 1000))
        await asyncio.sleep(delay)
        return {
            "status": "completed",
            "error": None,
            "measuredResult": {
                "adapter": "mock",
                "intent": intent,
                "sceneId": parameters.get("sceneId"),
                "parameters": parameters,
                "mappedCommands": [command.as_dict() for command in commands],
                "mappedCommandCount": len(commands),
            },
        }


class RobotBridge:
    def __init__(self, url: str, device_id: str, adapter: MockRobotAdapter) -> None:
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
            await self.report(action_id, intent, "cancelled", started, None, parameters, {"adapter": "mock"}, source_event_id, "cancelled")
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
            await asyncio.sleep(retry_seconds)


async def main() -> None:
    bridge = RobotBridge(
        os.getenv("AGENT_GATEWAY_WS_URL", "ws://127.0.0.1:8082/ws"),
        os.getenv("ROBOT_DEVICE_ID", "mock-robot"),
        MockRobotAdapter(int(os.getenv("MOCK_ACTION_DELAY_MS", "50"))),
    )
    await bridge.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
