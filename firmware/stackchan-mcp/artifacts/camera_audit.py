import asyncio
import json
import subprocess
import time
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main() -> None:
    artifact = Path(__file__).parent
    log = artifact / "camera_serial.log"
    with log.open("wb") as out:
        reader = subprocess.Popen(
            [
                r"D:\Espressif\python_env\idf5.5_py3.11_env\Scripts\python.exe",
                str(artifact / "camera_serial_reader.py"),
                "COM7",
                "12",
            ],
            stdout=out,
            stderr=subprocess.STDOUT,
        )
        await asyncio.sleep(0.5)
        async with streamablehttp_client(
            "http://127.0.0.1:8767/mcp",
            headers={"Authorization": "Bearer ar-aipet-dev-20260807"},
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "take_photo", {"question": "Describe the current frame briefly."}
                )
                values = []
                for block in result.content:
                    text = getattr(block, "text", None)
                    if text:
                        try:
                            values.append(json.loads(text))
                        except json.JSONDecodeError:
                            values.append(text)
                print(json.dumps({"isError": result.isError, "content": values}, ensure_ascii=False))
        reader.wait(timeout=12)


if __name__ == "__main__":
    asyncio.run(main())
