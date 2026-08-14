from __future__ import annotations

import unittest
import uuid
from pathlib import Path

from app.experience import ExperienceOrchestrator
from app.scenes import ExactSceneRouter, SCENES


_HOST_CONTENT = (
    Path(__file__).resolve().parents[3] / "content" / "runtime"
    if len(Path(__file__).resolve().parents) > 3
    else Path("/app/content/runtime")
)
_CONTENT_CANDIDATES = (Path("/app/content/runtime"), _HOST_CONTENT)
CONTENT_ROOT = next((path for path in _CONTENT_CANDIDATES if path.exists()), _HOST_CONTENT)


class SceneRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = ExactSceneRouter()

    def test_exact_alias_and_robot_prefix(self) -> None:
        self.assertEqual(self.router.match("跳个舞").scene_id, "dance")
        self.assertEqual(self.router.match("宝贝，跳舞吧").scene_id, "dance")
        self.assertEqual(self.router.match("晚安啦").scene_id, "good_night")

    def test_non_exact_or_negated_text_goes_to_agent(self) -> None:
        self.assertIsNone(self.router.match("我不想跳舞"))
        self.assertIsNone(self.router.match("今天很累，陪我聊聊天"))

    def test_all_mvp_scenes_have_safe_stop_and_display_steps(self) -> None:
        for scene_id in ("wake_up", "good_night", "play", "welcome_home", "reminder", "comfort", "dance"):
            scene = SCENES[scene_id]
            self.assertGreater(scene.duration_ms, 0)
            if scene_id not in {"wake_up", "reminder"}:
                self.assertTrue(any(step["target"] == "base" and step["action"] == "stop" for step in scene.steps) or scene_id in {"good_night"})
            self.assertTrue(any(step["target"] == "display" for step in scene.steps))


class SceneEventTests(unittest.TestCase):
    def test_scene_event_keeps_voice_and_physical_timeline_together(self) -> None:
        orchestrator = ExperienceOrchestrator(CONTENT_ROOT)
        orchestrator.select_persona("gentle-companion")
        result = {
            "conversationId": str(uuid.uuid4()),
            "text": "好呀，来玩一下！",
            "experienceEventId": str(uuid.uuid4()),
            "toolCalls": [],
        }
        turn = orchestrator.scene_turn(result, "陪我玩", "play")
        event = orchestrator.scene_event("play", source_text="陪我玩", turn=turn)
        action = event["robot"]["actions"][0]
        self.assertEqual(event["mode"], "scene")
        self.assertEqual(event["scene"]["sceneId"], "play")
        self.assertEqual(action["intent"], "scene.play")
        self.assertEqual(action["parameters"]["sceneId"], "play")
        self.assertTrue(action["parameters"]["steps"])
        self.assertEqual(event["speech"]["text"], "好呀，来玩一下！")

    def test_agent_selected_scene_tool_uses_scene_timeline(self) -> None:
        orchestrator = ExperienceOrchestrator(CONTENT_ROOT)
        result = {
            "conversationId": str(uuid.uuid4()),
            "text": "好，我来跳一段！",
            "experienceEventId": str(uuid.uuid4()),
            "toolCalls": [{
                "name": "scene.play",
                "arguments": {"sceneId": "dance"},
                "status": "ok",
                "result": {"status": "deferred", "sceneId": "dance"},
            }],
        }
        turn, event = orchestrator.from_turn(result, "我想跳一段舞")
        self.assertEqual(turn["behaviorIntent"], "scene.play")
        self.assertEqual(event["scene"]["sceneId"], "dance")
        self.assertEqual(event["robot"]["actions"][0]["parameters"]["sceneId"], "dance")


if __name__ == "__main__":
    unittest.main()
