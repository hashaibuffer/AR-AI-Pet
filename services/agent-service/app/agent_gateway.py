from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .agent_runtime import AgentRuntime, AgentRuntimeError
from .data_service_client import DataServiceClient
from .experience import ExperienceOrchestrator, ProactiveScheduler
from .experience_protocol import validate_action_result
from .memory_client import MemoryServiceClient
from .llm_provider import create_provider
from .settings import (
    AGENT_HOST,
    AGENT_LLM_API_KEY,
    AGENT_LLM_BASE_URL,
    AGENT_LLM_MODEL,
    AGENT_LLM_TIMEOUT_SECONDS,
    AGENT_MAX_TOOL_ROUNDS,
    AGENT_PORT,
    AGENT_PROVIDER,
    AGENT_TIMEZONE,
    DATA_SERVICE_TIMEOUT_SECONDS,
    DATA_SERVICE_WS_URL,
    EXPERIENCE_TICK_SECONDS,
    MEMORY_SEARCH_TIMEOUT_SECONDS,
    MEMORY_WS_URL,
    MCP_URL,
    AGENT_TOOL_MODE,
    PERSONA_ROOT,
    ROBOT_ADAPTER,
    ROBOT_DEVICE_ID,
    ROBOT_DISPATCH_MODE,
    STACKCHAN_MAX_DURATION_SECONDS,
    STACKCHAN_MAX_SPEED,
    STACKCHAN_TOKEN,
    STACKCHAN_WS_URL,
    DEVICE_ACTION_TIMEOUT_SECONDS,
)
from .tool_registry import InternalToolRegistry
from .devices.adapter import ActionDispatcher, MockRobotAdapter, StackChanWebSocketAdapter
from .devices.session import DeviceSessionManager, DeviceSessionRobotAdapter


def response(request_id: str | None, message_type: str, status: str, payload: Any = None) -> dict[str, Any]:
    return {"requestId": request_id, "type": message_type, "status": status, "payload": payload or {}}


class ExperienceHub:
    """Admission, publication and completion tracking for one active experience."""

    def __init__(self) -> None:
        self.subscribers: set[WebSocket] = set()
        self.active_event: dict[str, Any] | None = None
        self._required_action_ids: set[str] = set()
        self._completed_action_ids: set[str] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self, socket: WebSocket) -> None:
        self.subscribers.add(socket)

    def unsubscribe(self, socket: WebSocket) -> None:
        self.subscribers.discard(socket)

    @staticmethod
    def _expired(event: dict[str, Any] | None) -> bool:
        if not event or not event.get("expiresAt"):
            return True
        try:
            expiry = datetime.fromisoformat(str(event["expiresAt"]).replace("Z", "+00:00"))
            return expiry <= datetime.now(timezone.utc)
        except ValueError:
            return True

    @staticmethod
    def _action_ids(event: dict[str, Any]) -> set[str]:
        ids: set[str] = set()
        display_id = (event.get("xr") or {}).get("displayActionId")
        if (event.get("xr") or {}).get("visible") and display_id:
            ids.add(str(display_id))
        for action in (event.get("robot") or {}).get("actions", []):
            if action.get("actionId"):
                ids.add(str(action["actionId"]))
        return ids

    async def admit(self, event: dict[str, Any]) -> dict[str, Any]:
        """Reserve an event before any database write or device action is created."""
        async with self._lock:
            active = self.active_event
            if active and not self._expired(active) and int(event.get("priority", 0)) < int(active.get("priority", 0)):
                return {"accepted": False, "reason": "lower_priority", "activeEventId": active.get("eventId")}
            cancellation = None
            if active and not self._expired(active):
                cancellation = {"eventId": active.get("eventId"), "reason": "preempted", "byEventId": event.get("eventId")}
            self.active_event = event
            self._required_action_ids = self._action_ids(event)
            self._completed_action_ids = set()
            return {"accepted": True, "cancellation": cancellation}

    async def rollback(self, event_id: str, previous: dict[str, Any] | None = None) -> None:
        async with self._lock:
            if self.active_event and self.active_event.get("eventId") == event_id:
                self.active_event = previous
                self._required_action_ids = self._action_ids(previous) if previous else set()
                self._completed_action_ids = set()

    async def publish_admitted(self, event: dict[str, Any], cancellation: dict[str, Any] | None = None) -> None:
        if cancellation:
            await self._broadcast({"type": "experience.cancelled", "status": "ok", "payload": cancellation})
        await self._broadcast({"type": "experience.event", "status": "ok", "payload": event})
        if not self._required_action_ids:
            async with self._lock:
                if self.active_event and self.active_event.get("eventId") == event.get("eventId"):
                    self.active_event = None

    async def record_result(self, result: dict[str, Any]) -> None:
        if result.get("status") not in {"dispatched", "completed", "failed", "timeout", "cancelled"}:
            return
        action_id = str(result.get("actionId", ""))
        async with self._lock:
            if action_id not in self._required_action_ids:
                return
            self._completed_action_ids.add(action_id)
            if self._completed_action_ids >= self._required_action_ids:
                self.active_event = None
                self._required_action_ids = set()
                self._completed_action_ids = set()

    async def broadcast_stop(self, payload: dict[str, Any]) -> dict[str, Any]:
        active = self.active_event
        action_id = payload.get("actionId")
        if not action_id and active:
            action_id = next((item for item in (active.get("robot") or {}).get("actions", []) if item.get("actionId")), None)
            if isinstance(action_id, dict):
                action_id = action_id.get("actionId")
        command = {
            "commandId": str(uuid.uuid4()),
            "actionId": str(action_id) if action_id else None,
            "sourceEventId": payload.get("sourceEventId") or (active or {}).get("eventId"),
            "deviceId": payload.get("deviceId", "mock-robot"),
        }
        await self._broadcast({"type": "robot.command.stop", "status": "ok", "payload": command})
        return {"status": "sent", **command}

    async def _broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for socket in list(self.subscribers):
            try:
                await socket.send_json(message)
            except Exception:
                dead.append(socket)
        for socket in dead:
            self.unsubscribe(socket)


data_service = DataServiceClient(DATA_SERVICE_WS_URL, DATA_SERVICE_TIMEOUT_SECONDS)
memory_service = MemoryServiceClient(MEMORY_WS_URL, MEMORY_SEARCH_TIMEOUT_SECONDS)
provider = create_provider(
    AGENT_PROVIDER,
    base_url=AGENT_LLM_BASE_URL,
    api_key=AGENT_LLM_API_KEY,
    model=AGENT_LLM_MODEL,
    timezone_name=AGENT_TIMEZONE,
    timeout_seconds=AGENT_LLM_TIMEOUT_SECONDS,
)
device_sessions = DeviceSessionManager(action_timeout_seconds=DEVICE_ACTION_TIMEOUT_SECONDS)
if ROBOT_DISPATCH_MODE == "internal":
    if ROBOT_ADAPTER == "device":
        _adapter = DeviceSessionRobotAdapter(device_sessions, ROBOT_DEVICE_ID)
    elif ROBOT_ADAPTER == "stackchan":
        _adapter = StackChanWebSocketAdapter(STACKCHAN_WS_URL, token=STACKCHAN_TOKEN, max_speed=STACKCHAN_MAX_SPEED, max_duration_seconds=STACKCHAN_MAX_DURATION_SECONDS)
    else:
        _adapter = MockRobotAdapter()
    action_dispatcher: ActionDispatcher | None = ActionDispatcher(_adapter, ROBOT_DEVICE_ID)
else:
    action_dispatcher = None

tool_registry = None
if AGENT_TOOL_MODE == "internal":
    tool_registry = InternalToolRegistry(
        data_service,
        robot_stop_handler=action_dispatcher.stop if action_dispatcher is not None else None,
    )
runtime = AgentRuntime(mcp_url=MCP_URL, data_service=data_service, memory_service=memory_service, provider=provider, max_tool_rounds=AGENT_MAX_TOOL_ROUNDS, tool_registry=tool_registry)
orchestrator = ExperienceOrchestrator(PERSONA_ROOT)
hub = ExperienceHub()
scheduler = ProactiveScheduler(data_service, orchestrator)
app = FastAPI(title="AR-AIPet Local Agent", version="0.2")


async def persist_and_publish(event: dict[str, Any]) -> bool:
    admission = await hub.admit(event)
    if not admission["accepted"]:
        return False
    try:
        await data_service.request("experience.event.append", {"event": event})
        for action in (event.get("robot") or {}).get("actions", []):
            action_id = action.get("actionId")
            if action_id:
                await data_service.request("robot.action.request", {
                    "actionId": action_id,
                    "actionType": action.get("intent", "nod"),
                    "parameters": action.get("parameters", {}),
                    "sourceEventId": event.get("eventId"),
                })
        await hub.publish_admitted(event, admission.get("cancellation"))
        if action_dispatcher is not None:
            for action in (event.get("robot") or {}).get("actions", []):
                result = await action_dispatcher.dispatch(action, event.get("eventId"))
                await data_service.request("action.result.append", {"result": result})
                await hub.record_result(result)
                await hub._broadcast({"type": "experience.action.result", "status": "ok", "payload": {"result": result}})
        if admission.get("cancellation"):
            await data_service.request("experience.event.cancel", {"cancellation": admission["cancellation"]})
        return True
    except Exception:
        await hub.rollback(str(event.get("eventId")))
        raise


async def proactive_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            events = await scheduler.tick()
            for event in sorted(events, key=lambda item: int(item.get("priority", 0)), reverse=True):
                await persist_and_publish(event)
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=EXPERIENCE_TICK_SECONDS)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        selected = await data_service.request("persona.get")
        runtime.set_persona(orchestrator.select_persona(selected.get("personaId")))
    except Exception:
        runtime.set_persona(orchestrator.ensure_persona())
    stop = asyncio.Event()
    task = asyncio.create_task(proactive_loop(stop))
    try:
        yield
    finally:
        stop.set()
        await task
        if action_dispatcher is not None:
            await action_dispatcher.close()


app.router.lifespan_context = lifespan


async def device_websocket_endpoint(socket: WebSocket) -> None:
    await device_sessions.handle(socket)


@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket) -> None:
    await socket.accept()
    subscribed = False
    try:
        while True:
            message = json.loads(await socket.receive_text())
            request_id = message.get("requestId") or f"agent-{uuid.uuid4().hex}"
            message_type = message.get("type")
            payload = message.get("payload") or {}
            if message_type == "ping":
                await socket.send_json(response(request_id, "pong", "ok", {}))
                continue
            if message_type == "experience.subscribe":
                await hub.subscribe(socket)
                subscribed = True
                await socket.send_json(response(request_id, "experience.subscribe.result", "ok", {"subscribed": True}))
                continue
            if message_type == "robot.command.stop":
                result = await hub.broadcast_stop(payload)
                stop_status = "ok"
                if action_dispatcher is not None:
                    dispatch_result = await action_dispatcher.stop("remote_stop")
                    result["dispatch"] = dispatch_result
                    if isinstance(dispatch_result, dict) and dispatch_result.get("status") == "failed":
                        stop_status = "error"
                await socket.send_json(response(request_id, "robot.command.stop.result", stop_status, result))
                continue
            if message_type == "persona.list":
                await socket.send_json(response(request_id, "persona.list.result", "ok", orchestrator.personas.list()))
                continue
            if message_type == "persona.get":
                selected = await data_service.request("persona.get")
                selected["persona"] = orchestrator.personas.load(selected.get("personaId"))
                await socket.send_json(response(request_id, "persona.get.result", "ok", selected))
                continue
            if message_type == "persona.select":
                selected = await data_service.request("persona.select", payload)
                persona = orchestrator.select_persona(selected["personaId"])
                runtime.set_persona(persona)
                await socket.send_json(response(request_id, "persona.select.result", "ok", {**selected, "persona": persona}))
                continue
            if message_type == "experience.action.result":
                result = validate_action_result(payload.get("result") if isinstance(payload.get("result"), dict) else payload)
                stored = await data_service.request("action.result.append", {"result": result})
                await hub.record_result(result)
                await socket.send_json(response(request_id, "experience.action.result.ack", "ok", stored))
                continue
            if message_type != "agent.chat":
                await socket.send_json(response(request_id, "agent.error", "error", {"code": "unsupported_message"}))
                continue
            await socket.send_json(response(request_id, "agent.accepted", "ok", {}))
            try:
                text = str(payload.get("text", ""))
                result = await runtime.chat(text, payload.get("conversationId"))
                selected = await data_service.request("persona.get")
                runtime.set_persona(orchestrator.select_persona(selected.get("personaId")))
                turn, event = orchestrator.from_turn(result, text)
                accepted = await persist_and_publish(event)
                result["agentTurn"] = turn
                result["experienceEvent"] = event
                result["experienceEventId"] = event["eventId"]
                result["experienceAccepted"] = accepted
                await socket.send_json(response(request_id, "agent.result", "ok", result))
            except AgentRuntimeError as exc:
                await socket.send_json(response(request_id, "agent.error", "error", {"code": "agent_failed", "message": str(exc)}))
            except Exception as exc:
                await socket.send_json(response(request_id, "agent.error", "error", {"code": "agent_failed", "message": str(exc)}))
    except WebSocketDisconnect:
        return
    finally:
        if subscribed:
            hub.unsubscribe(socket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=AGENT_HOST, port=AGENT_PORT)
