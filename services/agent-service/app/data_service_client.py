from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import websockets


class DataServiceError(RuntimeError):
    """A clear failure returned by or while contacting the data service."""

    def __init__(self, message: str, *, status: str = "error", payload: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


class DataServiceClient:
    def __init__(self, url: str, timeout_seconds: float = 5.0) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    async def request(self, message_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = f"mcp-{uuid.uuid4().hex}"
        message = {
            "requestId": request_id,
            "type": message_type,
            "payload": payload or {},
        }
        try:
            async with asyncio.timeout(self.timeout_seconds):
                async with websockets.connect(
                    self.url,
                    open_timeout=self.timeout_seconds,
                    close_timeout=self.timeout_seconds,
                ) as socket:
                    await socket.send(json.dumps(message))
                    while True:
                        raw = await socket.recv()
                        incoming = json.loads(raw)
                        if incoming.get("requestId") != request_id:
                            continue
                        status = incoming.get("status", "error")
                        result = incoming.get("payload") or {}
                        if status != "ok":
                            detail = result.get("code") if isinstance(result, dict) else result
                            raise DataServiceError(
                                f"data service rejected {message_type}: {status} ({detail})",
                                status=status,
                                payload=result,
                            )
                        return result
        except DataServiceError:
            raise
        except TimeoutError as exc:
            raise DataServiceError(
                f"data service timeout after {self.timeout_seconds:g}s: {message_type}",
                status="unavailable",
            ) from exc
        except (OSError, websockets.WebSocketException, json.JSONDecodeError) as exc:
            raise DataServiceError(
                f"data service unavailable at {self.url}: {message_type}",
                status="unavailable",
            ) from exc
