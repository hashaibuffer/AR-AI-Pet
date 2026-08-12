from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP

from .data_service_client import DataServiceClient
from .settings import MCP_HOST, MCP_PORT
from .settings import DATA_SERVICE_TIMEOUT_SECONDS, DATA_SERVICE_WS_URL


mcp = FastMCP(
    "AR-AIPet MCP Hub",
    instructions=(
        "Use these tools for the single-user AR-AIPet project. "
        "PostgreSQL is the source of truth. Read state before making decisions, "
        "and report tool failures instead of claiming success."
    ),
)

data_service = DataServiceClient(DATA_SERVICE_WS_URL, DATA_SERVICE_TIMEOUT_SECONDS)


@mcp.tool(
    name="system.health",
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def system_health() -> dict[str, Any]:
    """Check whether the project database and default single-user data are available."""
    snapshot = await data_service.request("bootstrap.get")
    return {
        "status": "ok",
        "userId": snapshot["userId"],
        "petId": snapshot["petId"],
    }


@mcp.tool(
    name="pet.state.get",
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def pet_state_get(domain: Literal["pet", "home", "farm"] = "pet") -> dict[str, Any]:
    """Read the latest structured pet, home, or autonomous farm state."""
    return await data_service.request("state.get", {"domain": domain})


@mcp.tool(
    name="schedule.list",
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
async def schedule_list(limit: int = 20) -> list[dict[str, Any]]:
    """List upcoming active reminders, ordered by reminder time."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    snapshot = await data_service.request("bootstrap.get")
    return snapshot["schedules"][:limit]


@mcp.tool(
    name="schedule.upsert",
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
)
async def schedule_save(
    title: str,
    starts_at: str,
    remind_at: str,
    description: str | None = None,
    repeat_type: Literal["none", "daily", "weekly"] = "none",
    schedule_id: str | None = None,
) -> dict[str, Any]:
    """Create or update one reminder. Times must be ISO 8601 values with a timezone."""
    if not title.strip():
        raise ValueError("title must not be empty")
    payload: dict[str, Any] = {
        "title": title.strip(),
        "description": description,
        "startsAt": starts_at,
        "remindAt": remind_at,
        "repeatType": repeat_type,
        "status": "active",
    }
    if schedule_id:
        payload["id"] = schedule_id
    return await data_service.request("schedule.upsert", payload)


@mcp.tool(name="schedule.complete", annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
async def schedule_complete(schedule_id: str) -> dict[str, Any]:
    """Complete one reminder by id."""
    return await data_service.request("schedule.complete", {"id": schedule_id})


@mcp.tool(name="schedule.snooze", annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
async def schedule_snooze(schedule_id: str, minutes: int = 10) -> dict[str, Any]:
    """Move one reminder later by a bounded number of minutes."""
    if not 1 <= minutes <= 1440:
        raise ValueError("minutes must be between 1 and 1440")
    return await data_service.request("schedule.snooze", {"id": schedule_id, "minutes": minutes})


@mcp.tool(name="farm.get_state", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def farm_get_state() -> dict[str, Any]:
    """Read the autonomous farm state."""
    return await data_service.request("state.get", {"domain": "farm"})


@mcp.tool(name="farm.get_available_actions", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def farm_get_available_actions() -> list[str]:
    """List semantic farm actions available to the pet."""
    result = await data_service.request("farm.get_available_actions")
    return result.get("actions", [])


@mcp.tool(name="farm.perform_action", annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
async def farm_perform_action(action: Literal["water", "plant", "harvest", "rest"]) -> dict[str, Any]:
    """Perform one semantic autonomous farm action."""
    return await data_service.request("farm.perform_action", {"action": action})


@mcp.tool(name="game.start", annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
async def game_start() -> dict[str, Any]:
    """Start a single-user Yahtzee game against the pet."""
    return await data_service.request("game.start", {"gameType": "yahtzee"})


@mcp.tool(name="game.get_state", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def game_get_state() -> dict[str, Any]:
    """Read the active Yahtzee game."""
    return await data_service.request("game.get_state")


@mcp.tool(name="game.submit_action", annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
async def game_submit_action(action: Literal["roll", "keep", "score"], indices: list[int] | None = None, score: int | None = None) -> dict[str, Any]:
    """Apply one semantic Yahtzee action; the data service owns the rules."""
    payload: dict[str, Any] = {"action": action}
    if indices is not None:
        payload["indices"] = indices
    if score is not None:
        payload["score"] = score
    return await data_service.request("game.submit_action", payload)


@mcp.tool(name="game.end", annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
async def game_end(game_id: str, result: dict[str, Any]) -> dict[str, Any]:
    """Finish the active Yahtzee game."""
    from datetime import datetime, timezone
    return await data_service.request("game-session.save", {"id": game_id, "gameType": "yahtzee", "status": "completed", "state": {}, "result": result, "endedAt": datetime.now(timezone.utc).isoformat()})


@mcp.tool(name="sensor.latest", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def sensor_latest(sensor_type: str | None = None) -> dict[str, Any]:
    """Read the latest accepted sensor observation."""
    return await data_service.request("sensor.latest", {"sensorType": sensor_type})


@mcp.tool(name="sensor.query_recent", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def sensor_query_recent(sensor_type: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    """Read recent sensor observations."""
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    result = await data_service.request("sensor.query_recent", {"sensorType": sensor_type, "limit": limit})
    return result.get("observations", [])


@mcp.tool(name="device.capabilities", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def device_capabilities(device_id: str = "mock-robot") -> dict[str, Any]:
    """Read semantic device capabilities without exposing motor parameters."""
    return {"deviceId": device_id, "capabilities": ["nod", "wave", "dance", "farm_tend", "stop"]}


@mcp.tool(name="robot.react", annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
async def robot_react(action_type: str, parameters: dict[str, Any] | None = None, source_event_id: str | None = None, action_id: str | None = None) -> dict[str, Any]:
    """Request one semantic robot reaction."""
    return await data_service.request("robot.action.request", {"actionId": action_id, "actionType": action_type, "parameters": parameters or {}, "sourceEventId": source_event_id})


@mcp.tool(name="robot.stop", annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False})
async def robot_stop(source_event_id: str | None = None) -> dict[str, Any]:
    """Request the highest-priority semantic stop action."""
    return await data_service.request("robot.action.stop", {"sourceEventId": source_event_id})


@mcp.tool(name="robot.get_status", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def robot_get_status(device_id: str = "mock-robot") -> dict[str, Any]:
    """Read the mock robot semantic status."""
    latest = await data_service.request("action.latest", {"deviceId": device_id})
    status = latest.get("status", "idle") if latest else "idle"
    return {"deviceId": device_id, "status": status, "connected": True, "capabilities": ["nod", "wave", "dance", "farm_tend", "stop"], "latestAction": latest}


@mcp.tool(name="action.latest", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def action_latest(device_id: str = "mock-robot") -> dict[str, Any]:
    """Read the most recent semantic action lifecycle record."""
    return await data_service.request("action.latest", {"deviceId": device_id})


@mcp.tool(name="action.query_recent", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def action_query_recent(limit: int = 10, action_type: str | None = None) -> list[dict[str, Any]]:
    """Read recent action requests and lifecycle results."""
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    result = await data_service.request("action.query_recent", {"limit": limit, "actionType": action_type})
    return result.get("actions", [])


_PERSONAS = {
    "gentle-companion": {"personaId": "gentle-companion", "version": "0.1"},
    "energetic-partner": {"personaId": "energetic-partner", "version": "0.1"},
}


@mcp.tool(name="persona.list", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def persona_list() -> list[dict[str, Any]]:
    """List the built-in single-user personas."""
    return list(_PERSONAS.values())


@mcp.tool(name="persona.get", annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
async def persona_get() -> dict[str, Any]:
    """Read the persisted active persona selection."""
    return await data_service.request("persona.get")


@mcp.tool(name="persona.select", annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
async def persona_select(persona_id: Literal["gentle-companion", "energetic-partner"], persona_version: str = "0.1") -> dict[str, Any]:
    """Persist the active persona selection."""
    return await data_service.request("persona.select", {"personaId": persona_id, "personaVersion": persona_version})


if __name__ == "__main__":
    mcp.run(transport="http", host=MCP_HOST, port=MCP_PORT)
