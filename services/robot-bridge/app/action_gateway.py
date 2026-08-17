from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Mapping
from typing import Any

from websockets.asyncio.server import ServerConnection, Server, serve
from websockets.exceptions import ConnectionClosed


LOG = logging.getLogger("robot-bridge.action-gateway")


class ActionGatewayError(RuntimeError):
    """Raised when the StackChan action-only WebSocket cannot execute a tool."""


class DeviceActionSession:
    """One outbound StackChan action-gateway connection.

    StackChan owns the connection and sends the initial ``hello``. The gateway
    then sends normal MCP JSON-RPC requests over the same WebSocket. No audio
    or conversation messages are handled here; those remain on Xiaozhi's
    primary connection.
    """

    def __init__(self, socket: ServerConnection, device_id: str, session_id: str) -> None:
        self.socket = socket
        self.device_id = device_id
        self.session_id = session_id
        self._next_request_id = 0
        self._pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._send_lock = asyncio.Lock()
        self._closed = asyncio.Event()

    @property
    def closed(self) -> bool:
        return self._closed.is_set()

    async def send_hello(self) -> None:
        await self.socket.send(json.dumps({
            "type": "hello",
            "version": 1,
            "transport": "websocket",
            "session_id": self.session_id,
        }))

    async def call_tool(
        self,
        name: str,
        arguments: Mapping[str, Any],
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        if self.closed:
            raise ActionGatewayError("device_action_session_closed")
        self._next_request_id += 1
        request_id = self._next_request_id
        loop = asyncio.get_running_loop()
        waiter: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[request_id] = waiter
        message = {
            "session_id": self.session_id,
            "type": "mcp",
            "payload": {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": name, "arguments": dict(arguments)},
                "id": request_id,
            },
        }
        try:
            async with self._send_lock:
                await self.socket.send(json.dumps(message, ensure_ascii=False))
            response = await asyncio.wait_for(waiter, timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise ActionGatewayError(f"device_tool_timeout:{name}") from exc
        except (ConnectionClosed, OSError) as exc:
            raise ActionGatewayError(f"device_tool_send_failed:{name}") from exc
        finally:
            self._pending.pop(request_id, None)
        if "error" in response:
            raise ActionGatewayError(str(response["error"]))
        result = response.get("result")
        if not isinstance(result, dict):
            raise ActionGatewayError(f"invalid_device_tool_result:{name}")
        if result.get("isError") is True:
            raise ActionGatewayError(f"device_tool_error:{name}")
        return result

    def handle_message(self, message: dict[str, Any]) -> None:
        if message.get("type") != "mcp":
            return
        payload = message.get("payload")
        if not isinstance(payload, dict) or "id" not in payload:
            return
        try:
            request_id = int(payload["id"])
        except (TypeError, ValueError):
            return
        waiter = self._pending.get(request_id)
        if waiter is not None and not waiter.done():
            waiter.set_result(payload)

    def close(self) -> None:
        self._closed.set()
        for waiter in self._pending.values():
            if not waiter.done():
                waiter.set_exception(ActionGatewayError("device_action_session_closed"))
        self._pending.clear()


class DeviceActionGateway:
    """Small action-only MCP WebSocket server hosted by Robot Bridge."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        token: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.token = token
        self._server: Server | None = None
        self._sessions: dict[str, DeviceActionSession] = {}
        self._latest: DeviceActionSession | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._server = await serve(self._handle_connection, self.host, self.port)
        LOG.info("action gateway listening on ws://%s:%s", self.host, self.port)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
            self._latest = None
        for session in sessions:
            session.close()

    async def _handle_connection(self, socket: ServerConnection) -> None:
        headers = getattr(getattr(socket, "request", None), "headers", {})
        if self.token:
            expected = f"Bearer {self.token}"
            if headers.get("Authorization", "") != expected:
                await socket.close(code=1008, reason="invalid action gateway token")
                return
        try:
            raw = await asyncio.wait_for(socket.recv(), timeout=10)
            hello = json.loads(raw)
            if not isinstance(hello, dict) or hello.get("type") != "hello":
                await socket.close(code=1002, reason="hello required")
                return
            device_id = str(headers.get("Device-Id", "stackchan"))
            session = DeviceActionSession(socket, device_id, f"action-{uuid.uuid4().hex}")
            async with self._lock:
                old = self._sessions.get(device_id)
                if old is not None:
                    old.close()
                self._sessions[device_id] = session
                self._latest = session
            await session.send_hello()
            LOG.info("StackChan action session connected device=%s", device_id)
            async for raw in socket:
                try:
                    message = json.loads(raw)
                except (TypeError, json.JSONDecodeError):
                    LOG.warning("ignored non-JSON action gateway frame")
                    continue
                if isinstance(message, dict):
                    session.handle_message(message)
        except (ConnectionClosed, asyncio.TimeoutError, OSError) as exc:
            LOG.info("StackChan action session closed: %s", exc)
        finally:
            session = locals().get("session")
            if isinstance(session, DeviceActionSession):
                session.close()
                async with self._lock:
                    if self._sessions.get(session.device_id) is session:
                        self._sessions.pop(session.device_id, None)
                    if self._latest is session:
                        self._latest = next(iter(self._sessions.values()), None)

    async def _select(self, device_id: str) -> DeviceActionSession:
        async with self._lock:
            session = self._sessions.get(device_id)
            if session is None and len(self._sessions) == 1:
                session = next(iter(self._sessions.values()))
            if session is None:
                session = self._latest
        if session is None or session.closed:
            raise ActionGatewayError(f"device_not_connected:{device_id}")
        return session

    async def call_tool(
        self,
        device_id: str,
        name: str,
        arguments: Mapping[str, Any],
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        session = await self._select(device_id)
        return await session.call_tool(name, arguments, timeout)

    async def status(self, device_id: str) -> dict[str, Any]:
        async with self._lock:
            session = self._sessions.get(device_id)
            if session is None and len(self._sessions) == 1:
                session = next(iter(self._sessions.values()))
        return {
            "deviceId": device_id,
            "connected": bool(session is not None and not session.closed),
            "sessionId": session.session_id if session is not None else None,
            "connectedDeviceId": session.device_id if session is not None else None,
        }


__all__ = ["ActionGatewayError", "DeviceActionGateway", "DeviceActionSession"]
