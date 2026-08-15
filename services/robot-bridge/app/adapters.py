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

    This is intentionally a simple one-shot scheduler. It does not arbitrate
    overlapping scenes or interruption priorities yet; the bridge's existing
    stop path remains available for the next iteration.
    """

    started = time.monotonic()
    results: list[dict[str, Any]] = []
    for command in commands:
        wait_seconds = command.at_ms / 1000 - (time.monotonic() - started)
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        result = await call_tool(command.tool, command.arguments)
        results.append({"command": command.as_dict(), "result": result})
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
