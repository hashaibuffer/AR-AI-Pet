import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def decode(result):
    values = []
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            try:
                values.append(json.loads(text))
            except json.JSONDecodeError:
                values.append(text)
    return values


async def call(session, name, args):
    result = await session.call_tool(name, args)
    item = {"tool": name, "isError": result.isError, "content": decode(result)}
    print(json.dumps(item, ensure_ascii=False))
    return item


async def main():
    async with streamablehttp_client(
        "http://127.0.0.1:8767/mcp",
        headers={"Authorization": "Bearer ar-aipet-dev-20260807"},
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            before = await call(session, "gateway_config_get", {})
            await call(session, "gateway_config_set", {"fallback_url": "ws://192.168.50.133:8765"})
            after_set = await call(session, "gateway_config_get", {})
            await call(session, "gateway_config_set", {"fallback_url": ""})
            after_restore = await call(session, "gateway_config_get", {})
            assert after_set["content"][0]["fallback_url"] == "ws://192.168.50.133:8765"
            assert after_restore["content"][0]["fallback_url"] == before["content"][0]["fallback_url"]


if __name__ == "__main__":
    asyncio.run(main())
