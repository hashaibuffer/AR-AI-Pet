from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import websockets
from fastmcp import Client

from mock_clients import MockRobot, MockUnity


AGENT_URL = os.getenv("AGENT_URL", "ws://localhost:8082/ws")
DATA_URL = os.getenv("DATA_SERVICE_WS_URL", "ws://localhost:8080/ws")
MCP_URL = os.getenv("MCP_URL", "http://localhost:8081/mcp")


async def request(socket, message_type: str, payload: dict | None = None) -> dict:
    request_id = f"experience-smoke-{uuid.uuid4().hex}"
    await socket.send(json.dumps({"requestId": request_id, "type": message_type, "payload": payload or {}}, ensure_ascii=False))
    while True:
        message = json.loads(await socket.recv())
        if message.get("requestId") != request_id:
            continue
        assert message.get("status") == "ok", message
        return message.get("payload") or {}


async def agent_chat(socket, text: str) -> dict:
    request_id = f"chat-{uuid.uuid4().hex}"
    await socket.send(json.dumps({"requestId": request_id, "type": "agent.chat", "payload": {"text": text}}))
    while True:
        message = json.loads(await socket.recv())
        if message.get("requestId") != request_id:
            continue
        if message.get("type") == "agent.accepted":
            continue
        assert message.get("status") == "ok", message
        return message["payload"]


async def main() -> None:
    async with websockets.connect(DATA_URL) as data, websockets.connect(AGENT_URL) as agent:
        now = datetime.now(timezone.utc)
        unity = MockUnity(AGENT_URL, "mock-unity")
        robot = MockRobot(AGENT_URL, "mock-robot")
        await unity.connect()
        await robot.connect()
        personas = await request(agent, "persona.list")
        assert {item["personaId"] for item in personas} >= {"gentle-companion", "energetic-partner", "prickly-softheart"}, personas
        selected = await request(agent, "persona.select", {"personaId": "energetic-partner", "personaVersion": "1.0"})
        assert selected["personaId"] == "energetic-partner", selected
        await request(data, "schedule.upsert", {
            "title": f"体验编排 smoke {uuid.uuid4().hex[:6]}",
            "startsAt": (now - timedelta(minutes=1)).isoformat(),
            "remindAt": (now - timedelta(seconds=1)).isoformat(),
            "repeatType": "none",
            "status": "active",
        })

        chat_task = asyncio.create_task(agent_chat(agent, "陪我跳舞吧"))
        unity_event, robot_event = await asyncio.gather(unity.next_event(), robot.next_event())
        assert unity_event["eventId"] == robot_event["eventId"], (unity_event, robot_event)
        assert unity_event["xr"]["displayActionId"] != robot_event["robot"]["actions"][0]["actionId"], (unity_event, robot_event)
        assert unity_event["mode"] == "conversation", unity_event
        assert unity_event["robot"]["actions"][0]["intent"] == "dance", unity_event
        await asyncio.gather(unity.acknowledge(unity_event, "display"), robot.acknowledge(robot_event, "dance"))
        result = await chat_task
        assert result["agentTurn"]["behaviorIntent"] == "dance", result
        assert any(call["name"] == "robot.react" and call["status"] == "ok" for call in result["toolCalls"]), result
        assert result["experienceEventId"] == unity_event["eventId"], result

        reminder_unity, reminder_robot = await asyncio.gather(unity.next_event(), robot.next_event())
        assert reminder_unity["eventId"] == reminder_robot["eventId"], (reminder_unity, reminder_robot)
        assert reminder_unity["mode"] == "reminder", reminder_unity
        await asyncio.gather(unity.acknowledge(reminder_unity, "display"), robot.acknowledge(reminder_robot, "wave"))
        observation_id = str(uuid.uuid4())
        await request(data, "sensor.observation.append", {"observation": {
            "version": "0.1", "observationId": observation_id, "deviceId": "mock-robot", "sensorType": "camera.face",
            "observedAt": datetime.now(timezone.utc).isoformat(), "value": {"present": True},
            "confidence": 0.99, "unit": "normalized", "source": "mock", "privacyClass": "local",
        }})
        sensor_unity, sensor_robot = await asyncio.gather(unity.next_event(), robot.next_event())
        assert sensor_unity["eventId"] == sensor_robot["eventId"], (sensor_unity, sensor_robot)
        assert sensor_unity["mode"] == "sensor", sensor_unity
        await asyncio.gather(unity.acknowledge(sensor_unity, "display"), robot.acknowledge(sensor_robot, "wave"))
        actions = await request(data, "action.query_recent", {"limit": 20})
        statuses = {item.get("status") for item in actions.get("actions", [])}
        assert {"accepted", "started", "completed"} <= statuses, actions
        pending_chat = asyncio.create_task(agent_chat(agent, "陪我跳舞"))
        pending_unity, pending_robot = await asyncio.gather(unity.next_event(), robot.next_event())
        command_task = asyncio.create_task(robot.next_command())
        async with Client(MCP_URL) as mcp:
            stopped = await mcp.call_tool("robot.stop", {"device_id": "mock-robot", "source_event_id": pending_robot["eventId"]})
        command = await command_task
        assert command["actionId"] == pending_robot["robot"]["actions"][0]["actionId"], command
        await robot.acknowledge_command(command)
        await unity.acknowledge(pending_unity, "display")
        await pending_chat
        await unity.socket.close()
        await robot.socket.close()
    print(f"AGENT_EXPERIENCE_SMOKE_OK {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
