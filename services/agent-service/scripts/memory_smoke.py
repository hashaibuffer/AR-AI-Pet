from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from datetime import datetime

import websockets


DATA_URL = os.getenv("DATA_SERVICE_WS_URL", "ws://localhost:8080/ws")
MEMORY_URL = os.getenv("MEMORY_URL", "ws://localhost:8083/ws")
AGENT_URL = os.getenv("AGENT_URL", "ws://localhost:8082/ws")


async def request(socket, message_type: str, payload: dict | None = None) -> dict:
    request_id = f"memory-smoke-{uuid.uuid4().hex}"
    await socket.send(json.dumps({"requestId": request_id, "type": message_type, "payload": payload or {}}, ensure_ascii=False))
    while True:
        message = json.loads(await socket.recv())
        if message.get("requestId") != request_id:
            continue
        assert message.get("status") == "ok", message
        return message.get("payload") or {}


async def agent_chat(socket, text: str) -> dict:
    request_id = f"memory-agent-smoke-{uuid.uuid4().hex}"
    await socket.send(json.dumps({"requestId": request_id, "type": "agent.chat", "payload": {"text": text}}, ensure_ascii=False))
    while True:
        message = json.loads(await socket.recv())
        if message.get("requestId") != request_id:
            continue
        if message.get("type") == "agent.accepted":
            continue
        assert message.get("status") == "ok", message
        return message["payload"]


async def main() -> None:
    async with websockets.connect(DATA_URL) as data, websockets.connect(MEMORY_URL) as memory:
        identity = await request(data, "bootstrap.get")
        conversation = await request(data, "conversation.append", {
            "role": "user", "content": "我最喜欢草莓，不喜欢香菜。", "channel": "unity_text",
        })
        completed = await request(data, "conversation.append", {
            "conversationId": conversation["conversationId"], "role": "assistant",
            "content": "记住了你的口味。", "channel": "unity_text", "memoryEligible": True,
        })
        assert completed.get("memoryJobId"), completed
        found: list[dict] = []
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            result = await request(memory, "memory.search", {
                "userId": identity["userId"], "query": "我喜欢什么，不喜欢什么？", "limit": 5,
            })
            found = result.get("memories", [])
            if any("草莓" in item.get("text", "") for item in found) and any("香菜" in item.get("text", "") for item in found):
                break
            await asyncio.sleep(1)
        assert any("草莓" in item.get("text", "") for item in found), found
        assert any("香菜" in item.get("text", "") for item in found), found
        assert all(item.get("memoryId") for item in found), found
        context = await request(data, "conversation.get", {"conversationId": conversation["conversationId"], "limit": 10})
        assert [item["role"] for item in context["messages"]] == ["user", "assistant"], context
    async with websockets.connect(AGENT_URL) as agent:
        answer = await agent_chat(agent, "我喜欢什么，不喜欢什么？")
        assert "草莓" in answer["text"] and "香菜" in answer["text"], answer
        assert answer["memoryStatus"] == "used", answer
        assert answer["memoryIds"], answer
    print(f"MEMORY_SMOKE_OK {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
