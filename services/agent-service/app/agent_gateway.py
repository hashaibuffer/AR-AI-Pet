from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .agent_runtime import AgentRuntime, AgentRuntimeError
from .data_service_client import DataServiceClient
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
    MCP_URL,
)


def response(request_id: str | None, message_type: str, status: str, payload: Any = None) -> dict[str, Any]:
    return {"requestId": request_id, "type": message_type, "status": status, "payload": payload or {}}


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


data_service = DataServiceClient(DATA_SERVICE_WS_URL, DATA_SERVICE_TIMEOUT_SECONDS)
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
    provider=provider,
    max_tool_rounds=AGENT_MAX_TOOL_ROUNDS,
)
app = FastAPI(title="AR-AIPet Local Agent", version="0.1", lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket) -> None:
    await socket.accept()
    try:
        while True:
            message = json.loads(await socket.receive_text())
            request_id = message.get("requestId") or f"agent-{uuid.uuid4().hex}"
            message_type = message.get("type")
            payload = message.get("payload") or {}
            if message_type == "ping":
                await socket.send_json(response(request_id, "pong", "ok", {}))
                continue
            if message_type != "agent.chat":
                await socket.send_json(response(request_id, "agent.error", "error", {"code": "unsupported_message"}))
                continue
            await socket.send_json(response(request_id, "agent.accepted", "ok", {}))
            try:
                result = await runtime.chat(payload.get("text", ""), payload.get("conversationId"))
                await socket.send_json(response(request_id, "agent.result", "ok", result))
            except AgentRuntimeError as exc:
                await socket.send_json(response(request_id, "agent.error", "error", {"code": "agent_failed", "message": str(exc)}))
            except Exception as exc:
                await socket.send_json(response(request_id, "agent.error", "error", {"code": "agent_failed", "message": str(exc)}))
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=AGENT_HOST, port=AGENT_PORT)
