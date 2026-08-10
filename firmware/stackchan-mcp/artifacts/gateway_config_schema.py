import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client(
        "http://127.0.0.1:8767/mcp",
        headers={"Authorization": "Bearer ar-aipet-dev-20260807"},
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for t in tools.tools:
                if t.name == "gateway_config_set":
                    print(json.dumps({"name": t.name, "description": t.description, "inputSchema": t.inputSchema}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
