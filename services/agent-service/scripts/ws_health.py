from __future__ import annotations

import asyncio
import json
import os
import uuid

import websockets


URL = os.getenv("WS_HEALTH_URL", "ws://localhost:8080/ws")
TIMEOUT_SECONDS = float(os.getenv("WS_HEALTH_TIMEOUT_SECONDS", "2"))


async def main() -> None:
    request_id = f"health-{uuid.uuid4().hex}"
    async with asyncio.timeout(TIMEOUT_SECONDS):
        async with websockets.connect(URL, open_timeout=TIMEOUT_SECONDS) as socket:
            await socket.send(json.dumps({"requestId": request_id, "type": "ping", "payload": {}}))
            while True:
                message = json.loads(await socket.recv())
                if message.get("requestId") != request_id:
                    continue
                if message.get("type") != "pong" or message.get("status") != "ok":
                    raise RuntimeError(f"unexpected health response: {message}")
                return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"WS_HEALTH_FAILED: {exc}")
        raise SystemExit(1) from exc
