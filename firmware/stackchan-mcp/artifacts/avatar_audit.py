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
            result = await session.call_tool(
                "load_avatar_set",
                {
                    "archive_path": r"D:\projects\stackchan-b-evaluation\artifacts\avatar_demo_layered.rgb565",
                    "mode": "layered",
                    "timeout": 90,
                },
            )
            print(json.dumps({"tool": "load_avatar_set", "content": decode(result)}, ensure_ascii=False))
            for face in ("idle", "happy", "surprised"):
                result = await session.call_tool("set_avatar", {"face": face})
                print(json.dumps({"tool": "set_avatar", "face": face, "content": decode(result)}, ensure_ascii=False))
            for mouth in ("closed", "open", "e"):
                result = await session.call_tool("set_mouth", {"mouth": mouth})
                print(json.dumps({"tool": "set_mouth", "mouth": mouth, "content": decode(result)}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
