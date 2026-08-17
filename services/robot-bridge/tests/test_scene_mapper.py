from __future__ import annotations

import unittest

from app.scene_mapper import SceneMappingError, SceneStepMapper


def scene(*steps: dict, duration_ms: int = 7000) -> dict:
    return {"sceneId": "test", "durationMs": duration_ms, "steps": list(steps)}


class SceneMapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = SceneStepMapper()

    def test_maps_display_led_head_and_base_to_existing_tools(self) -> None:
        commands = self.mapper.map_scene(scene(
            {"atMs": 0, "target": "display", "action": "icon", "value": "music"},
            {"atMs": 0, "target": "led", "action": "effect", "value": "color_cycle"},
            {"atMs": 300, "target": "head", "action": "pose", "value": "nod"},
            {"atMs": 1000, "target": "base", "action": "move", "value": "turn_left_short"},
            {"atMs": 1600, "target": "base", "action": "stop", "value": "immediate"},
        ))
        tools = [command.tool for command in commands]
        self.assertIn("self.display.set_emotion", tools)
        self.assertIn("self.led.set_all", tools)
        self.assertIn("self.robot.set_head_angles", tools)
        self.assertIn("self.robot.base_move", tools)
        self.assertIn("self.robot.base_stop", tools)
        self.assertEqual(commands[0].arguments, {"emotion": "laughing"})

    def test_automatically_adds_stop_for_unfinished_move(self) -> None:
        commands = self.mapper.map_scene(scene(
            {"atMs": 100, "target": "base", "action": "move", "value": "forward_gentle"},
        ))
        self.assertEqual(commands[-1].tool, "self.robot.base_stop")
        self.assertEqual(commands[-1].at_ms, 7000)

    def test_rejects_unknown_device_step(self) -> None:
        with self.assertRaises(SceneMappingError):
            self.mapper.map_scene(scene(
                {"atMs": 0, "target": "base", "action": "dance", "value": "fast"},
            ))


if __name__ == "__main__":
    unittest.main()
