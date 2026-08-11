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
        expected = {"system.health", "pet.state.get", "schedule.list", "schedule.upsert"}
        assert expected <= names, names

        health = await client.call_tool("system.health", {})
        assert health.data["status"] == "ok", health

        pet = await client.call_tool("pet.state.get", {"domain": "pet"})
        assert pet.data["domain"] == "pet", pet

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
