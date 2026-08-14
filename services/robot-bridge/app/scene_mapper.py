from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class SceneMappingError(ValueError):
    """Raised when a scene contains a step outside the device contract."""


@dataclass(frozen=True)
class DeviceCommand:
    """One semantic MCP call scheduled relative to the scene start."""

    at_ms: int
    tool: str
    arguments: dict[str, Any]
    step_index: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "atMs": self.at_ms,
            "tool": self.tool,
            "arguments": dict(self.arguments),
            "stepIndex": self.step_index,
        }


# These names are the built-in Twemoji names in the current StackChan LCD
# renderer.  Scene content may use an icon label, but the device receives a
# real existing Emoji name rather than an invented avatar command.
EMOTION_ALIASES: dict[str, str] = {
    "clock": "thinking",
    "music": "laughing",
}

SUPPORTED_EMOTIONS = {
    "neutral",
    "happy",
    "laughing",
    "funny",
    "sad",
    "angry",
    "crying",
    "loving",
    "embarrassed",
    "surprised",
    "shocked",
    "thinking",
    "winking",
    "cool",
    "relaxed",
    "delicious",
    "kissy",
    "confident",
    "sleepy",
    "silly",
    "confused",
}


LED_EFFECTS: dict[str, tuple[tuple[int, tuple[int, int, int]], ...]] = {
    "warm_fade_in": (
        (0, (20, 8, 1)),
        (250, (100, 35, 4)),
        (500, (255, 110, 12)),
    ),
    "amber_breathe": (
        (0, (160, 55, 5)),
        (450, (30, 10, 1)),
        (900, (160, 55, 5)),
        (1350, (30, 10, 1)),
        (1800, (160, 55, 5)),
    ),
    "amber_breathe_2": (
        (0, (150, 50, 4)),
        (600, (25, 8, 1)),
        (1200, (150, 50, 4)),
        (1800, (25, 8, 1)),
    ),
    "blue_pulse": (
        (0, (0, 0, 140)),
        (450, (0, 0, 15)),
        (900, (0, 0, 140)),
        (1350, (0, 0, 15)),
        (1800, (0, 0, 140)),
        (2250, (0, 0, 15)),
    ),
    "color_cycle": (
        (0, (255, 0, 0)),
        (300, (255, 100, 0)),
        (600, (0, 220, 40)),
        (900, (0, 150, 255)),
        (1200, (40, 40, 255)),
        (1500, (200, 0, 255)),
    ),
    "color_cycle_fast": (
        (0, (255, 0, 0)),
        (180, (255, 180, 0)),
        (360, (0, 220, 50)),
        (540, (0, 160, 255)),
        (720, (50, 40, 255)),
        (900, (220, 0, 220)),
        (1080, (255, 0, 0)),
    ),
}


HEAD_POSES: dict[str, tuple[tuple[int, int], ...]] = {
    "raise": ((0, 45),),
    "look_left": ((-20, 45),),
    "look_right": ((20, 45),),
    "user": ((0, 45),),
    "left": ((-22, 45),),
    "right": ((22, 45),),
    "tilt": ((-12, 40),),
    "down": ((0, 25),),
    "nod": ((0, 30), (0, 45)),
    "nod_twice": ((0, 30), (0, 45), (0, 30), (0, 45)),
    "left_right_left": ((-22, 45), (22, 45), (-22, 45)),
}


BASE_MOVES: dict[str, tuple[str, int]] = {
    "forward_short": ("forward", 45),
    "forward_gentle": ("forward", 30),
    "turn_left_short": ("left", 45),
    "turn_right_short": ("right", 45),
}


class SceneStepMapper:
    """Compile scene semantics into the existing StackChan MCP tool names.

    The mapper intentionally emits no PWM, servo register, or wheel protocol
    values.  It only translates scene content to the safe high-level tools
    already exposed by the firmware.  LED animations are expanded into timed
    ``self.led.set_all`` calls because the firmware exposes one-shot LED tools,
    while head and base safety remains enforced by firmware and the explicit
    ``base_stop`` commands below.
    """

    def map_scene(self, parameters: dict[str, Any]) -> list[DeviceCommand]:
        steps = parameters.get("steps")
        if not isinstance(steps, list) or not steps:
            raise SceneMappingError("scene.play requires a non-empty steps array")
        duration_ms = int(parameters.get("durationMs", 0) or 0)
        if duration_ms <= 0 or duration_ms > 30_000:
            raise SceneMappingError("durationMs must be between 1 and 30000")

        commands: list[DeviceCommand] = []
        for index, raw_step in enumerate(steps):
            if not isinstance(raw_step, dict):
                raise SceneMappingError(f"step[{index}] must be an object")
            try:
                at_ms = int(raw_step["atMs"])
                target = str(raw_step["target"])
                action = str(raw_step["action"])
                value = str(raw_step["value"])
            except (KeyError, TypeError, ValueError) as exc:
                raise SceneMappingError(f"step[{index}] is missing a valid field") from exc
            if at_ms < 0 or at_ms > duration_ms:
                raise SceneMappingError(f"step[{index}] atMs is outside scene duration")
            commands.extend(self._map_step(index, at_ms, target, action, value))

        # A scene may be authored without a final stop.  Add one at the scene
        # boundary so a dropped connection cannot leave the base moving.
        base_moves = [command for command in commands if command.tool == "self.robot.base_move"]
        base_stops = [command for command in commands if command.tool == "self.robot.base_stop"]
        if base_moves and (not base_stops or max(stop.at_ms for stop in base_stops) < max(move.at_ms for move in base_moves)):
            commands.append(DeviceCommand(duration_ms, "self.robot.base_stop", {}, -1))

        return [
            command
            for _, command in sorted(enumerate(commands), key=lambda item: (item[1].at_ms, item[0]))
        ]

    def _map_step(self, index: int, at_ms: int, target: str, action: str, value: str) -> list[DeviceCommand]:
        if target == "display" and action in {"emotion", "icon"}:
            emotion = EMOTION_ALIASES.get(value, value)
            if emotion not in SUPPORTED_EMOTIONS:
                raise SceneMappingError(f"unsupported Emoji: {value}")
            return [DeviceCommand(at_ms, "self.display.set_emotion", {"emotion": emotion}, index)]

        if target == "led" and action == "effect":
            if value == "off":
                return [DeviceCommand(at_ms, "self.led.clear", {}, index)]
            try:
                frames = LED_EFFECTS[value]
            except KeyError as exc:
                raise SceneMappingError(f"unsupported LED effect: {value}") from exc
            return [
                DeviceCommand(
                    at_ms + offset,
                    "self.led.set_all",
                    {"r": rgb[0], "g": rgb[1], "b": rgb[2]},
                    index,
                )
                for offset, rgb in frames
            ]

        if target == "head" and action == "pose":
            try:
                poses = HEAD_POSES[value]
            except KeyError as exc:
                raise SceneMappingError(f"unsupported head pose: {value}") from exc
            # A 160 ms gap gives the servo time to make a visible nod without
            # introducing a new firmware-side animation queue.
            return [
                DeviceCommand(
                    at_ms + position * 160,
                    "self.robot.set_head_angles",
                    {"yaw": yaw, "pitch": pitch, "speed_dps": 300},
                    index,
                )
                for position, (yaw, pitch) in enumerate(poses)
            ]

        if target == "base" and action == "move":
            try:
                direction, speed = BASE_MOVES[value]
            except KeyError as exc:
                raise SceneMappingError(f"unsupported base move: {value}") from exc
            return [DeviceCommand(at_ms, "self.robot.base_move", {"direction": direction, "speed": speed}, index)]

        if target == "base" and action == "stop":
            return [DeviceCommand(at_ms, "self.robot.base_stop", {}, index)]

        raise SceneMappingError(f"unsupported scene step: {target}.{action}={value}")


__all__ = ["DeviceCommand", "SceneMappingError", "SceneStepMapper"]
