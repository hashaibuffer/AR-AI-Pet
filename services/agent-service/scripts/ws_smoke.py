from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
import uuid

import websockets

URL = os.getenv("WS_URL", "ws://localhost:8080/ws")


async def request(socket, message_type: str, payload: dict) -> dict:
    request_id = f"smoke-{uuid.uuid4().hex}"
    await socket.send(json.dumps({"requestId": request_id, "type": message_type, "payload": payload}))
    while True:
        message = json.loads(await socket.recv())
        if message.get("requestId") == request_id:
            return message


async def event(socket, message_type: str) -> dict:
    while True:
        message = json.loads(await socket.recv())
        if message.get("type") == message_type:
            return message


async def main() -> None:
    async with websockets.connect(URL) as socket, websockets.connect(URL) as watcher:
        pong = await request(socket, "ping", {})
        assert pong["requestId"].startswith("smoke-")
        assert pong["type"] == "pong"
        assert pong["status"] == "ok"
        boot = await request(socket, "bootstrap.get", {})
        assert boot["status"] == "ok"
        farm = next(item for item in boot["payload"]["states"] if item["domain"] == "farm")
        farm_data = dict(farm["data"])
        old = "2020-01-01T00:00:00Z"
        farm_data["lastTickAt"] = old
        for plot in farm_data.get("plots", []):
            plot["stage"] = "seed"
            plot["stageStartedAt"] = old
        saved = await request(socket, "state.put", {"domain": "farm", "expectedRevision": farm["revision"], "data": farm_data})
        assert saved["status"] == "ok", saved
        updated = await request(socket, "state.get", {"domain": "farm"})
        assert updated["status"] == "ok"
        pushed = await event(watcher, "farm.state.changed")
        assert pushed["status"] == "ok"
        assert pushed["payload"]["revision"] == updated["payload"]["revision"]
        now = datetime.now(timezone.utc)
        schedule = await request(socket, "schedule.upsert", {"title": "Smoke reminder", "startsAt": (now + timedelta(hours=1)).isoformat(), "remindAt": (now + timedelta(minutes=55)).isoformat(), "repeatType": "none", "status": "active"})
        assert schedule["status"] == "ok", schedule
        game = await request(socket, "game-session.save", {"gameType": "yahtzee", "status": "playing", "schemaVersion": 1, "state": {"round": 1, "isUserTurn": True, "dice": [1, 2, 3, 4, 5], "keep": [False] * 5, "rollsThisTurn": 1, "userScores": {}, "petScores": {}}})
        assert game["status"] == "ok", game
        invalid_end = await request(socket, "game-session.save", {"id": game["payload"]["id"], "gameType": "yahtzee", "status": "completed", "schemaVersion": 1, "state": game["payload"]["state"]})
        assert invalid_end["status"] == "error", invalid_end
        ended = await request(socket, "game-session.save", {"id": game["payload"]["id"], "gameType": "yahtzee", "status": "completed", "schemaVersion": 1, "state": game["payload"]["state"], "result": {"winner": "user", "userScore": 42, "petScore": 35}, "endedAt": datetime.now(timezone.utc).isoformat()})
        assert ended["status"] == "ok", ended
        assert ended["payload"]["status"] == "completed"
        assert ended["payload"]["result"]["winner"] == "user"
        conversation = await request(socket, "conversation.append", {"role": "user", "content": "测试消息", "channel": "unity_text"})
        assert conversation["status"] == "ok", conversation
        conflict = await request(socket, "state.put", {"domain": "farm", "expectedRevision": 1, "data": {}})
        assert conflict["status"] == "conflict", conflict
        print("WS_SMOKE_OK")


if __name__ == "__main__":
    asyncio.run(main())
