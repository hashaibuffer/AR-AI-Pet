from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
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
    PERSONA_ROOT,
)


def response(request_id: str | None, message_type: str, status: str, payload: Any = None) -> dict[str, Any]:
    return {"requestId": request_id, "type": message_type, "status": status, "payload": payload or {}}


class ExperienceHub:
    def __init__(self) -> None:
        self.subscribers: set[WebSocket] = set()

    async def subscribe(self, socket: WebSocket) -> None:
        self.subscribers.add(socket)

    def unsubscribe(self, socket: WebSocket) -> None:
        self.subscribers.discard(socket)

    async def publish(self, event: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for socket in self.subscribers:
            try:
                await socket.send_json({"type": "experience.event", "status": "ok", "payload": event})
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
runtime = AgentRuntime(
    mcp_url=MCP_URL,
    data_service=data_service,
    memory_service=memory_service,
    provider=provider,
    max_tool_rounds=AGENT_MAX_TOOL_ROUNDS,
)
orchestrator = ExperienceOrchestrator(PERSONA_ROOT)
hub = ExperienceHub()
scheduler = ProactiveScheduler(data_service, orchestrator)
app = FastAPI(title="AR-AIPet Local Agent", version="0.2")


async def persist_and_publish(event: dict[str, Any]) -> None:
    await data_service.request("experience.event.append", {"event": event})
    await hub.publish(event)


async def proactive_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            for event in await scheduler.tick():
                await persist_and_publish(event)
        except Exception:
            # Proactive behavior must never stop the Agent request loop.
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=EXPERIENCE_TICK_SECONDS)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop = asyncio.Event()
    task = asyncio.create_task(proactive_loop(stop))
    try:
        yield
    finally:
        stop.set()
        await task


app.router.lifespan_context = lifespan


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
            if message_type == "experience.action.result":
                result = validate_action_result(payload.get("result") if isinstance(payload.get("result"), dict) else payload)
                stored = await data_service.request("action.result.append", {"result": result})
                await socket.send_json(response(request_id, "experience.action.result.ack", "ok", stored))
                continue
            if message_type != "agent.chat":
                await socket.send_json(response(request_id, "agent.error", "error", {"code": "unsupported_message"}))
                continue
            await socket.send_json(response(request_id, "agent.accepted", "ok", {}))
            try:
                text = str(payload.get("text", ""))
                result = await runtime.chat(text, payload.get("conversationId"))
                turn, event = orchestrator.from_turn(result, text)
                await persist_and_publish(event)
                result["agentTurn"] = turn
                result["experienceEvent"] = event
                result["experienceEventId"] = event["eventId"]
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
