from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime

import websockets


DATA_URL = os.getenv("DATA_SERVICE_WS_URL", "ws://localhost:8080/ws")


async def request(socket, message_type: str, payload: dict | None = None) -> dict:
    request_id = f"conversation-recent-{uuid.uuid4().hex}"
    await socket.send(json.dumps({"requestId": request_id, "type": message_type, "payload": payload or {}}, ensure_ascii=False))
    while True:
        message = json.loads(await socket.recv())
        if message.get("requestId") != request_id:
            continue
        if message.get("status") != "ok":
            raise RuntimeError(message)
        return message.get("payload") or {}


async def main() -> None:
    async with websockets.connect(DATA_URL) as socket:
        conversation = await request(socket, "conversation.append", {"role": "user", "content": "recent-0"})
        conversation_id = conversation["conversationId"]
        for index in range(1, 8):
            await request(socket, "conversation.append", {
                "conversationId": conversation_id,
                "role": "assistant" if index % 2 else "user",
                "content": f"recent-{index}",
            })
        result = await request(socket, "conversation.get", {"conversationId": conversation_id, "limit": 3})
        messages = result["messages"]
        assert [item["content"] for item in messages] == ["recent-5", "recent-6", "recent-7"], messages
        created = [item["created_at"] for item in messages]
        assert created == sorted(created), created
    print(f"CONVERSATION_RECENT_SMOKE_OK {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
