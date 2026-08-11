from __future__ import annotations

import asyncio
import os

from fastmcp import Client


URL = os.getenv("MCP_HEALTH_URL", "http://localhost:8081/mcp")


async def main() -> None:
    async with Client(URL) as client:
        result = await client.call_tool("system.health", {})
        if result.data.get("status") != "ok":
            raise RuntimeError(f"unexpected MCP health result: {result.data}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"MCP_HEALTH_FAILED: {exc}")
        raise SystemExit(1) from exc
