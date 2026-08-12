from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import os

from fastmcp import Client


MCP_URL = os.getenv("MCP_URL", "http://localhost:8081/mcp")
SMOKE_SCHEDULE_ID = "00000000-0000-4000-8000-000000000081"


async def main() -> None:
    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools}
        expected = {"system.health", "pet.state.get", "schedule.list", "schedule.upsert", "persona.list", "persona.get", "persona.select", "farm.get_available_actions", "game.get_state", "game.submit_action", "action.latest", "action.query_recent"}
        assert expected <= names, names

        health = await client.call_tool("system.health", {})
        assert health.data["status"] == "ok", health

        pet = await client.call_tool("pet.state.get", {"domain": "pet"})
        assert pet.data["domain"] == "pet", pet

        personas = await client.call_tool("persona.list", {})
        assert personas.data, personas
        selected = await client.call_tool("persona.select", {"persona_id": "gentle-companion"})
        assert selected.data["personaId"] == "gentle-companion", selected
        farm_actions = await client.call_tool("farm.get_available_actions", {})
        assert "rest" in farm_actions.data, farm_actions
        farm_action = next((item for item in farm_actions.data if item != "rest"), "rest")
        farm_result = await client.call_tool("farm.perform_action", {"action": farm_action})
        assert farm_result.data["data"]["lastAction"] == farm_action, farm_result
        started = await client.call_tool("game.start", {})
        game_id = started.data["id"]
        current = await client.call_tool("game.get_state", {})
        assert current.data["id"] == game_id, current
        synced = await client.call_tool("game.submit_action", {"game_id": game_id, "action": "roll", "state": {"turn": "user", "dice": [1, 2, 3, 4, 5], "rollCount": 1}, "source_device": "unity-mock"})
        assert synced.data["state"]["rollCount"] == 1, synced
        assert synced.data["state"]["dice"] == [1, 2, 3, 4, 5], synced
        latest = await client.call_tool("action.latest", {})
        assert isinstance(latest.data, dict), latest

        now = datetime.now(timezone.utc)
        saved = await client.call_tool(
            "schedule.upsert",
            {
                "schedule_id": SMOKE_SCHEDULE_ID,
                "title": "MCP smoke reminder",
                "starts_at": (now + timedelta(hours=1)).isoformat(),
                "remind_at": (now + timedelta(minutes=55)).isoformat(),
                "repeat_type": "none",
            },
        )
        assert saved.data["id"] == SMOKE_SCHEDULE_ID, saved

        schedules = await client.call_tool("schedule.list", {"limit": 100})
        schedule_items = schedules.structured_content["result"]
        assert any(item["id"] == SMOKE_SCHEDULE_ID for item in schedule_items), schedules

    print("MCP_SMOKE_OK")


if __name__ == "__main__":
    asyncio.run(main())
