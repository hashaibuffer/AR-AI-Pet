from __future__ import annotations

import asyncio
import json
import os
import uuid

import websockets


URL = os.getenv("MEMORY_HEALTH_URL", "ws://localhost:8083/ws")


async def main() -> None:
    request_id = f"memory-health-{uuid.uuid4().hex}"
    async with asyncio.timeout(3):
        async with websockets.connect(URL, open_timeout=3) as socket:
            await socket.send(json.dumps({"requestId": request_id, "type": "memory.health", "payload": {}}))
            while True:
                message = json.loads(await socket.recv())
                if message.get("requestId") != request_id:
                    continue
                if message.get("type") != "memory.health.result" or message.get("status") != "ok":
                    raise RuntimeError(f"unexpected memory health response: {message}")
                return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"MEMORY_HEALTH_FAILED: {exc}")
        raise SystemExit(1) from exc
