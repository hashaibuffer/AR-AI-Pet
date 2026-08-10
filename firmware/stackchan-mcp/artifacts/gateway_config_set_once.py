import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    async with streamablehttp_client("http://127.0.0.1:8767/mcp", headers={"Authorization": "Bearer ar-aipet-dev-20260807"}) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("initialized", flush=True)
            result = await session.call_tool("gateway_config_set", {"fallback_url": "ws://192.168.50.133:8765"})
            values = [getattr(block, "text", "") for block in result.content]
            print(json.dumps({"isError": result.isError, "content": values}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
