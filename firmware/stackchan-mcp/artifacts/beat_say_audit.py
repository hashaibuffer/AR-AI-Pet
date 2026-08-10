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
            started = await session.call_tool("beat_mode_start", {"duration_sec": 12, "motion_intensity": 0.3})
            spoken = await session.call_tool("say", {"text": "舞蹈与语音并行测试。", "voice": "edge-tts", "speaker_name": "zh-CN-XiaoxiaoNeural"})
            await asyncio.sleep(2)
            status = await session.call_tool("beat_meta_snapshot", {})
            stopped = await session.call_tool("beat_mode_stop", {})
            print(json.dumps({"start": decode(started), "say": decode(spoken), "status": decode(status), "stop": decode(stopped)}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
