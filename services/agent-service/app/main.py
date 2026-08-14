"""Unified AR-AIPet application entry point.

The migration keeps the existing data and Agent handlers intact while running
them in one FastAPI process. Legacy ``/ws`` and data endpoints remain for
compatibility; new clients use ``/ws/app``, ``/ws/data`` and ``/ws/device``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from . import agent_gateway, memory_service, mcp_hub, server


# Keep one FastMCP ASGI instance so its session manager is initialized by the
# unified application's lifespan and reused by the mounted route.
mcp_app = mcp_hub.mcp.http_app()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Run both existing service loops under one process lifecycle."""

    async with mcp_app.router.lifespan_context(mcp_app):
        async with server.lifespan(server.app):
            async with memory_service.lifespan(memory_service.app):
                async with agent_gateway.lifespan(agent_gateway.app):
                    yield


app = FastAPI(title="AR-AIPet Server", version="0.3", lifespan=lifespan)

# New explicit endpoints.
app.add_api_websocket_route("/ws/app", agent_gateway.websocket_endpoint)
app.add_api_websocket_route("/ws/data", server.websocket_endpoint)
app.add_api_websocket_route("/ws/device", agent_gateway.device_websocket_endpoint)
app.add_api_websocket_route("/ws/memory", memory_service.websocket_endpoint)

# Compatibility endpoints. Existing Unity/Agent and data smoke scripts keep
# working during the migration and can be removed only after consumers move.
app.add_api_websocket_route("/ws", agent_gateway.websocket_endpoint)
app.add_api_websocket_route("/ws-legacy-data", server.websocket_endpoint)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ar-aipet-server", "version": app.version}


@app.get("/health/data")
async def data_health() -> dict[str, str]:
    return {"status": "ok", "service": "data-layer", "version": server.PROTOCOL_VERSION}


@app.get("/health/device")
async def device_health() -> dict[str, object]:
    sessions = await agent_gateway.device_sessions.snapshot()
    return {
        "status": "ok",
        "service": "device-gateway",
        "sessionCount": len(sessions),
        "deviceSessions": sessions,
    }


# FastMCP's HTTP app already exposes the ``/mcp`` route.  Mount it at the
# application root *after* the explicit routes so the same process owns the
# exact `/mcp` endpoint without Starlette's `/mcp` -> `/mcp/` redirect.
app.mount("/", mcp_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=agent_gateway.AGENT_HOST, port=agent_gateway.AGENT_PORT)
