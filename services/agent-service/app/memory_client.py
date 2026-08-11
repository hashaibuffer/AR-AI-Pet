from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import websockets


class MemoryServiceClient:
    def __init__(self, url: str, timeout_seconds: float = 2.0) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    async def request(self, message_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = f"memory-client-{uuid.uuid4().hex}"
        try:
            async with asyncio.timeout(self.timeout_seconds):
                async with websockets.connect(self.url, open_timeout=self.timeout_seconds) as socket:
                    await socket.send(json.dumps({"requestId": request_id, "type": message_type, "payload": payload or {}}, ensure_ascii=False))
                    while True:
                        incoming = json.loads(await socket.recv())
                        if incoming.get("requestId") != request_id:
                            continue
                        if incoming.get("status") != "ok":
                            raise RuntimeError("memory service request failed")
                        return incoming.get("payload") or {}
        except Exception as exc:
            raise RuntimeError("memory service unavailable") from exc
