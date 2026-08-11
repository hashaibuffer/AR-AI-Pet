from __future__ import annotations

import asyncio
from datetime import datetime
import json
import os
import uuid

import websockets


URL = os.getenv("AGENT_URL", "ws://localhost:8082/ws")


async def chat(socket, text: str, conversation_id: str | None = None) -> dict:
    request_id = f"agent-smoke-{uuid.uuid4().hex}"
    await socket.send(json.dumps({
        "requestId": request_id,
        "type": "agent.chat",
        "payload": {"text": text, "conversationId": conversation_id},
    }, ensure_ascii=False))
    accepted = False
    while True:
        message = json.loads(await socket.recv())
        if message.get("requestId") != request_id:
            continue
        if message.get("type") == "agent.accepted":
            accepted = True
            continue
        assert accepted, message
        assert message.get("type") in {"agent.result", "agent.error"}, message
        return message


async def main() -> None:
    async with websockets.connect(URL) as socket:
        request_id = f"agent-ping-{uuid.uuid4().hex}"
        await socket.send(json.dumps({"requestId": request_id, "type": "ping", "payload": {}}))
        pong = json.loads(await socket.recv())
        assert pong["requestId"] == request_id and pong["type"] == "pong" and pong["status"] == "ok", pong

        normal = await chat(socket, "你好，本地 Agent。")
        assert normal["type"] == "agent.result", normal
        first = normal["payload"]["conversationId"]
        assert first and normal["payload"]["text"]

        reminder = await chat(socket, "明天下午三点提醒我开会", first)
        assert reminder["type"] == "agent.result", reminder
        assert reminder["payload"]["conversationId"] == first
        assert any(call["name"] == "schedule.upsert" and call["status"] == "ok" for call in reminder["payload"]["toolCalls"]), reminder

        listed = await chat(socket, "我最近有什么日程？", first)
        assert listed["type"] == "agent.result", listed
        assert listed["payload"]["conversationId"] == first
        assert any(call["name"] == "schedule.list" and call["status"] == "ok" for call in listed["payload"]["toolCalls"]), listed

        failed = await chat(socket, "测试工具失败", first)
        assert failed["type"] in {"agent.result", "agent.error"}, failed
        if failed["type"] == "agent.result":
            assert any(call["status"] == "error" for call in failed["payload"]["toolCalls"]), failed

    print(f"AGENT_SMOKE_OK {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
