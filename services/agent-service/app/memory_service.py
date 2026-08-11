from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .data_service_client import DataServiceClient
from .memory.service import MemoryService, create_provider
from .settings import DATA_SERVICE_TIMEOUT_SECONDS, DATA_SERVICE_WS_URL, MEMORY_HOST, MEMORY_PORT


def response(request_id: str | None, message_type: str, status: str, payload: Any = None) -> dict[str, Any]:
    return {"requestId": request_id, "type": message_type, "status": status, "payload": payload or {}}


service = MemoryService(DataServiceClient(DATA_SERVICE_WS_URL, DATA_SERVICE_TIMEOUT_SECONDS), create_provider())


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop = asyncio.Event()
    worker_task = asyncio.create_task(service.worker.run_forever(stop))
    try:
        yield
    finally:
        stop.set()
        await worker_task


app = FastAPI(title="AR-AIPet Memory Service", version="0.1", lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket) -> None:
    await socket.accept()
    try:
        while True:
            message = json.loads(await socket.receive_text())
            request_id = message.get("requestId") or f"memory-{uuid.uuid4().hex}"
            message_type = message.get("type")
            payload = message.get("payload") or {}
            try:
                if message_type == "ping" or message_type == "memory.health":
                    result = await service.health()
                    await socket.send_json(response(request_id, "memory.health.result", "ok", result))
                elif message_type == "memory.search":
                    result = await service.search(payload)
                    await socket.send_json(response(request_id, "memory.search.result", "ok", result))
                else:
                    await socket.send_json(response(request_id, "error", "error", {"code": "unsupported_message"}))
            except Exception as exc:
                await socket.send_json(response(request_id, "error", "error", {"code": "memory_unavailable", "message": str(exc)[:200]}))
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=MEMORY_HOST, port=MEMORY_PORT)
