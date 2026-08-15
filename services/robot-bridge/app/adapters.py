from __future__ import annotations

import asyncio
import time
from typing import Any, Protocol

from .action_gateway import ActionGatewayError, DeviceActionGateway
from .scene_mapper import DeviceCommand, SceneStepMapper


class RobotAdapter(Protocol):
    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]: ...


async def execute_timeline(
    commands: list[DeviceCommand],
    call_tool,
) -> list[dict[str, Any]]:
    """Run semantic commands at their scene-relative timestamps.

    Commands at the same timestamp are dispatched by independent device
    lanes.  The base can therefore keep moving while the display/LED changes,
    while commands within one lane remain ordered.  Voice is intentionally
    not a lane here: the primary Xiaozhi audio path still owns speech and the
    current MVP keeps voice before/after a scene.
    """

    def lane(tool: str) -> str:
        if tool in {"self.robot.base_move", "self.robot.base_stop"}:
            return "base"
        if tool in {"self.display.set_emotion"}:
            return "display"
        if tool in {"self.led.set_all", "self.led.clear"}:
            return "led"
        if tool == "self.robot.set_head_angles":
            return "head"
        return tool

    async def run_lane(lane_commands: list[DeviceCommand]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for command in lane_commands:
            result = await call_tool(command.tool, command.arguments)
            results.append({"command": command.as_dict(), "result": result})
        return results

    started = time.monotonic()
    results: list[dict[str, Any]] = []
    by_time: dict[int, list[DeviceCommand]] = {}
    for command in commands:
        by_time.setdefault(command.at_ms, []).append(command)

    for at_ms in sorted(by_time):
        wait_seconds = at_ms / 1000 - (time.monotonic() - started)
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        lanes: dict[str, list[DeviceCommand]] = {}
        for command in by_time[at_ms]:
            lanes.setdefault(lane(command.tool), []).append(command)
        lane_results = await asyncio.gather(*(run_lane(items) for items in lanes.values()))
        for items in lane_results:
            results.extend(items)
    return results


class StackChanAdapter:
    """Real semantic adapter backed by the independent StackChan MCP socket."""

    supported = {
        "blink",
        "nod",
        "wave",
        "dance",
        "scene.play",
        "farm_tend",
        "stop",
    }

    def __init__(
        self,
        gateway: DeviceActionGateway,
        device_id: str = "stackchan",
        timeout_seconds: float = 5.0,
    ) -> None:
        self.gateway = gateway
        self.device_id = device_id
        self.timeout_seconds = timeout_seconds
        self.scene_mapper = SceneStepMapper()

    async def _call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self.gateway.call_tool(
            self.device_id,
            tool,
            arguments,
            timeout=self.timeout_seconds,
        )

    async def execute(self, intent: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if intent not in self.supported:
            return {"status": "failed", "error": f"unsupported_intent:{intent}", "measuredResult": {}}
        try:
            if intent == "scene.play":
                commands = self.scene_mapper.map_scene(parameters)
                results = await execute_timeline(commands, self._call)
                return {
                    "status": "completed",
                    "error": None,
                    "measuredResult": {
                        "adapter": "stackchan-action-gateway",
                        "deviceId": self.device_id,
                        "sceneId": parameters.get("sceneId"),
                        "mappedCommands": [item["command"] for item in results],
                        "deviceResults": results,
                    },
                }

            if intent == "dance":
                result = await self._call(
                    "self.scene.play",
                    {"scene_id": str(parameters.get("sceneId") or "dance")},
                )
                return {
                    "status": "completed",
                    "error": None,
                    "measuredResult": {
                        "adapter": "stackchan-action-gateway",
                        "deviceId": self.device_id,
                        "mappedCommands": [{"tool": "self.scene.play", "arguments": {"scene_id": str(parameters.get("sceneId") or "dance")}}],
                        "deviceResults": [result],
                    },
                }
            command = self._simple_command(intent, parameters)
            result = await self._call(command.tool, command.arguments)
            return {
                "status": "completed",
                "error": None,
                "measuredResult": {
                    "adapter": "stackchan-action-gateway",
                    "deviceId": self.device_id,
                    "mappedCommands": [command.as_dict()],
                    "deviceResults": [result],
                },
            }
        except (ActionGatewayError, ValueError) as exc:
            return {
                "status": "failed",
                "error": str(exc),
                "measuredResult": {"adapter": "stackchan-action-gateway", "deviceId": self.device_id},
            }

    def _simple_command(self, intent: str, parameters: dict[str, Any]) -> DeviceCommand:
        if intent == "stop":
            return DeviceCommand(0, "self.scene.stop", {}, -1)
        if intent == "nod":
            return DeviceCommand(0, "self.robot.set_head_angles", {"yaw": 0, "pitch": 30, "speed_dps": 300}, -1)
        if intent == "wave":
            return DeviceCommand(0, "self.robot.set_head_angles", {"yaw": 22, "pitch": 45, "speed_dps": 300}, -1)
        if intent == "blink":
            return DeviceCommand(0, "self.display.set_emotion", {"emotion": "winking"}, -1)
        if intent == "farm_tend":
            return DeviceCommand(0, "self.display.set_emotion", {"emotion": "happy"}, -1)
        raise ValueError(f"unsupported_intent:{intent}")


__all__ = ["RobotAdapter", "StackChanAdapter", "execute_timeline"]
