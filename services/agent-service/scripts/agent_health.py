from __future__ import annotations

import asyncio
import json
import os
import uuid

import websockets


URL = os.getenv("AGENT_HEALTH_URL", "ws://localhost:8082/ws")


async def main() -> None:
    request_id = f"agent-health-{uuid.uuid4().hex}"
    async with asyncio.timeout(2):
        async with websockets.connect(URL, open_timeout=2) as socket:
            await socket.send(json.dumps({"requestId": request_id, "type": "ping", "payload": {}}))
            while True:
                message = json.loads(await socket.recv())
                if message.get("requestId") != request_id:
                    continue
                if message.get("type") != "pong" or message.get("status") != "ok":
                    raise RuntimeError(f"unexpected Agent health response: {message}")
                return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"AGENT_HEALTH_FAILED: {exc}")
        raise SystemExit(1) from exc
