from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP

from .farm import advance_farm
from .server import bootstrap, schedule_upsert, state_get
from .settings import MCP_HOST, MCP_PORT


mcp = FastMCP(
    "AR-AIPet MCP Hub",
    instructions=(
        "Use these tools for the single-user AR-AIPet project. "
        "PostgreSQL is the source of truth. Read state before making decisions, "
        "and report tool failures instead of claiming success."
    ),
)


@mcp.tool(
    name="system.health",
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
def system_health() -> dict[str, Any]:
    """Check whether the project database and default single-user data are available."""
    snapshot = bootstrap()
    return {
        "status": "ok",
        "userId": snapshot["userId"],
        "petId": snapshot["petId"],
    }


@mcp.tool(
    name="pet.state.get",
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
def pet_state_get(domain: Literal["pet", "home", "farm"] = "pet") -> dict[str, Any]:
    """Read the latest structured pet, home, or autonomous farm state."""
    if domain == "farm":
        advance_farm()
    return state_get({"domain": domain})


@mcp.tool(
    name="schedule.list",
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
def schedule_list(limit: int = 20) -> list[dict[str, Any]]:
    """List upcoming active reminders, ordered by reminder time."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    return bootstrap()["schedules"][:limit]


@mcp.tool(
    name="schedule.upsert",
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
)
def schedule_save(
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
    return schedule_upsert(payload)


if __name__ == "__main__":
    mcp.run(transport="http", host=MCP_HOST, port=MCP_PORT)
