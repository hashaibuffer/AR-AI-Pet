"""In-process business and semantic robot tools.

The public MCP adapter and the local Agent use the same semantic names.  The
local path calls these functions directly; the FastMCP hub remains an external
compatibility adapter and must not become a second state owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from .data_service_client import DataServiceClient


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]

    def model_dump(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "inputSchema": self.input_schema}


@dataclass(frozen=True)
class ToolResult:
    value: Any
    is_error: bool = False

    @property
    def structured_content(self) -> dict[str, Any]:
        return {"result": self.value}


ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]
RobotStopHandler = Callable[[str], Awaitable[Any]]


def _schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required or []}


class InternalToolRegistry:
    def __init__(self, data_service: DataServiceClient, robot_stop_handler: RobotStopHandler | None = None) -> None:
        self.data_service = data_service
        self.robot_stop_handler = robot_stop_handler
        self._handlers: dict[str, ToolHandler] = {
            "system.health": self._system_health,
            "pet.state.get": self._state_get,
            "schedule.list": self._schedule_list,
            "schedule.upsert": self._schedule_upsert,
            "schedule.complete": self._schedule_complete,
            "schedule.snooze": self._schedule_snooze,
            "farm.get_state": self._farm_get_state,
            "farm.get_available_actions": self._farm_get_available_actions,
            "farm.perform_action": self._farm_perform_action,
            "game.start": self._game_start,
            "game.get_state": self._game_get_state,
            "game.submit_action": self._game_submit_action,
            "sensor.latest": self._sensor_latest,
            "sensor.query_recent": self._sensor_query_recent,
            "device.capabilities": self._device_capabilities,
            "robot.react": self._robot_react,
            "robot.stop": self._robot_stop,
            "robot.get_status": self._robot_get_status,
            "action.latest": self._action_latest,
            "action.query_recent": self._action_query_recent,
            "persona.list": self._persona_list,
            "persona.get": self._persona_get,
            "persona.select": self._persona_select,
        }
        string = {"type": "string"}
        integer = {"type": "integer"}
        self._specs = [
            ToolSpec("system.health", "Check the project data layer.", _schema({})),
            ToolSpec("pet.state.get", "Read pet, home or farm state.", _schema({"domain": {"type": "string", "enum": ["pet", "home", "farm"]}})),
            ToolSpec("schedule.list", "List active reminders.", _schema({"limit": integer})),
            ToolSpec("schedule.upsert", "Create or update one reminder.", _schema({"title": string, "description": string, "starts_at": string, "remind_at": string, "repeat_type": string}, ["title", "starts_at", "remind_at"])),
            ToolSpec("schedule.complete", "Complete one reminder.", _schema({"schedule_id": string}, ["schedule_id"])),
            ToolSpec("schedule.snooze", "Move one reminder later.", _schema({"schedule_id": string, "minutes": integer}, ["schedule_id"])),
            ToolSpec("farm.get_state", "Read autonomous farm state.", _schema({})),
            ToolSpec("farm.get_available_actions", "List available farm actions.", _schema({})),
            ToolSpec("farm.perform_action", "Perform one farm action.", _schema({"action": {"type": "string", "enum": ["water", "plant", "harvest", "rest"]}}, ["action"])),
            ToolSpec("game.start", "Start a Yahtzee game against the pet.", _schema({})),
            ToolSpec("game.get_state", "Read the active game.", _schema({})),
            ToolSpec("game.submit_action", "Save a Unity-authoritative game snapshot.", _schema({"game_id": string, "action": string, "state": {"type": "object"}}, ["game_id", "action", "state"])),
            ToolSpec("sensor.latest", "Read the latest sensor observation.", _schema({"sensor_type": string})),
            ToolSpec("sensor.query_recent", "Read recent sensor observations.", _schema({"sensor_type": string, "limit": integer})),
            ToolSpec("device.capabilities", "Read semantic device capabilities.", _schema({"device_id": string})),
            ToolSpec("robot.react", "Request a semantic robot reaction.", _schema({"action_type": string, "parameters": {"type": "object"}, "source_event_id": string, "action_id": string}, ["action_type"])),
            ToolSpec("robot.stop", "Stop current robot motion.", _schema({"device_id": string, "source_event_id": string, "action_id": string})),
            ToolSpec("robot.get_status", "Read robot action status.", _schema({"device_id": string})),
            ToolSpec("action.latest", "Read latest action lifecycle record.", _schema({"device_id": string})),
            ToolSpec("action.query_recent", "Read recent action lifecycle records.", _schema({"limit": integer, "action_type": string})),
            ToolSpec("persona.list", "List available personas.", _schema({})),
            ToolSpec("persona.get", "Read selected persona.", _schema({})),
            ToolSpec("persona.select", "Select a persona.", _schema({"persona_id": string}, ["persona_id"])),
        ]

    async def list_tools(self) -> list[ToolSpec]:
        return list(self._specs)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        handler = self._handlers.get(name)
        if handler is None:
            return ToolResult({"error": f"unknown tool: {name}"}, is_error=True)
        try:
            return ToolResult(await handler(arguments))
        except Exception as exc:
            return ToolResult({"error": str(exc)}, is_error=True)

    async def _system_health(self, _: dict[str, Any]) -> dict[str, Any]:
        snapshot = await self.data_service.request("bootstrap.get")
        return {"status": "ok", "userId": snapshot["userId"], "petId": snapshot["petId"]}

    async def _state_get(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("state.get", {"domain": args.get("domain", "pet")})

    async def _schedule_list(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        result = await self.data_service.request("bootstrap.get")
        return result.get("schedules", [])[: max(1, min(int(args.get("limit", 20)), 100))]

    async def _schedule_upsert(self, args: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "id": args.get("schedule_id"), "title": str(args["title"]).strip(), "description": args.get("description"),
            "startsAt": args["starts_at"], "remindAt": args["remind_at"], "repeatType": args.get("repeat_type", "none"), "status": "active",
        }
        if not payload["title"]:
            raise ValueError("title must not be empty")
        return await self.data_service.request("schedule.upsert", payload)

    async def _schedule_complete(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("schedule.complete", {"id": args["schedule_id"]})

    async def _schedule_snooze(self, args: dict[str, Any]) -> dict[str, Any]:
        minutes = max(1, min(int(args.get("minutes", 10)), 1440))
        return await self.data_service.request("schedule.snooze", {"id": args["schedule_id"], "minutes": minutes})

    async def _farm_get_state(self, _: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("state.get", {"domain": "farm"})

    async def _farm_get_available_actions(self, _: dict[str, Any]) -> list[str]:
        result = await self.data_service.request("farm.get_available_actions")
        return result.get("actions", [])

    async def _farm_perform_action(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("farm.perform_action", {"action": args["action"]})

    async def _game_start(self, _: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("game.start", {"gameType": "yahtzee"})

    async def _game_get_state(self, _: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("game.get_state")

    async def _game_submit_action(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("game.submit_action", {"gameId": args["game_id"], "action": args["action"], "state": args["state"], "result": args.get("result"), "sourceDevice": args.get("source_device", "agent")})

    async def _sensor_latest(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("sensor.latest", {"sensorType": args.get("sensor_type")})

    async def _sensor_query_recent(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("sensor.query_recent", {"sensorType": args.get("sensor_type"), "limit": max(1, min(int(args.get("limit", 10)), 50))})

    async def _device_capabilities(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"deviceId": args.get("device_id", "mock-robot"), "capabilities": ["nod", "wave", "dance", "farm_tend", "stop"]}

    async def _robot_react(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"status": "deferred", "actionId": args.get("action_id"), "actionType": args["action_type"], "parameters": args.get("parameters") or {}, "sourceEventId": args.get("source_event_id")}

    async def _robot_stop(self, args: dict[str, Any]) -> dict[str, Any]:
        dispatch: dict[str, Any] = {"status": "not_configured"}
        if self.robot_stop_handler is not None:
            result = await self.robot_stop_handler("agent_tool")
            dispatch = result if isinstance(result, dict) else {"status": "sent"}
        stored = await self.data_service.request("robot.action.stop", {"sourceEventId": args.get("source_event_id"), "actionId": args.get("action_id"), "deviceId": args.get("device_id", "mock-robot")})
        return {**stored, "dispatch": dispatch}

    async def _robot_get_status(self, args: dict[str, Any]) -> dict[str, Any]:
        latest = await self.data_service.request("action.latest", {"deviceId": args.get("device_id", "mock-robot")})
        return {"deviceId": args.get("device_id", "mock-robot"), "status": latest.get("status", "idle") if latest else "idle", "connected": True, "latestAction": latest}

    async def _action_latest(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("action.latest", {"deviceId": args.get("device_id", "mock-robot")})

    async def _action_query_recent(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        result = await self.data_service.request("action.query_recent", {"limit": max(1, min(int(args.get("limit", 10)), 50)), "actionType": args.get("action_type")})
        return result.get("actions", [])

    async def _persona_list(self, _: dict[str, Any]) -> list[dict[str, Any]]:
        from .persona import PersonaLoader
        from .settings import PERSONA_ROOT
        return PersonaLoader(PERSONA_ROOT).list()

    async def _persona_get(self, _: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("persona.get")

    async def _persona_select(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.data_service.request("persona.select", {"personaId": args["persona_id"], "personaVersion": args.get("persona_version", "1.0")})
