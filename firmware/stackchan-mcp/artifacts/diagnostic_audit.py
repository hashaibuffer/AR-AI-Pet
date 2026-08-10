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


async def main():
    async with streamablehttp_client(
        "http://127.0.0.1:8767/mcp",
        headers={"Authorization": "Bearer ar-aipet-dev-20260807"},
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for name in ("gateway_config_get", "uart_diag", "check_vm_en", "get_head_angles"):
                result = await session.call_tool(name, {})
                print(json.dumps({"tool": name, "isError": result.isError, "content": decode(result)}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
