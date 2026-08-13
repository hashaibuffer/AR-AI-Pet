from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.experience_protocol import ProtocolValidationError, validate_action_result, validate_experience_event
from app.persona import BehaviorRuleEngine, PersonaConfigError, PersonaLoader
from app.experience import ExperienceOrchestrator, ProactiveScheduler
from app.agent_gateway import ExperienceHub


_HOST_CONTENT = (
    Path(__file__).resolve().parents[3] / "content" / "runtime"
    if len(Path(__file__).resolve().parents) > 3
    else Path("/__missing_content__")
)
_CONTENT_CANDIDATES = (Path("/app/content/runtime"), _HOST_CONTENT)
CONTENT_ROOT = next((path for path in _CONTENT_CANDIDATES if path.exists()), _CONTENT_CANDIDATES[-1])


class ExperienceProtocolTests(unittest.TestCase):
    def _event(self) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "version": "0.1", "eventId": str(uuid.uuid4()), "sourceEventId": None, "personaId": "gentle-companion",
            "mode": "conversation", "priority": 100, "expiresAt": now,
            "speech": {"text": "", "emotion": "calm", "interruptible": True},
            "innerOs": {"text": "", "durationMs": 0, "anchor": "robot"},
            "robot": {"actions": []}, "xr": {"visible": True, "mode": "inner-os", "displayActionId": str(uuid.uuid4())},
            "app": {"refresh": False, "section": "home"}, "interruptible": True,
        }

    def test_valid_experience_event_and_action_result(self) -> None:
        self.assertEqual(validate_experience_event(self._event())["mode"], "conversation")
        action = {
            "version": "0.1", "actionId": str(uuid.uuid4()), "deviceId": "mock-robot", "actionType": "nod", "status": "completed",
            "startedAt": datetime.now(timezone.utc).isoformat(), "completedAt": datetime.now(timezone.utc).isoformat(),
            "requestedParameters": {}, "measuredResult": {}, "error": None, "sourceEventId": None,
        }
        self.assertEqual(validate_action_result(action)["status"], "completed")

    def test_dispatched_action_result_represents_gateway_delivery(self) -> None:
        action = {
            "version": "1.0", "actionId": str(uuid.uuid4()), "deviceId": "stackchan-robot", "actionType": "base_move", "status": "dispatched",
            "startedAt": datetime.now(timezone.utc).isoformat(), "completedAt": datetime.now(timezone.utc).isoformat(),
            "requestedParameters": {"direction": "forward"},
            "measuredResult": {"transportAccepted": True, "physicalConfirmed": False},
            "error": None, "sourceEventId": None,
        }
        self.assertEqual(validate_action_result(action)["status"], "dispatched")

    def test_invalid_event_is_rejected(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_experience_event({"mode": "conversation"})
        invalid = self._event()
        invalid["priority"] = True
        with self.assertRaises(ProtocolValidationError):
            validate_experience_event(invalid)
        invalid = self._event()
        invalid["unexpected"] = True
        with self.assertRaises(ProtocolValidationError):
            validate_experience_event(invalid)


class HubTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def event(priority: int) -> dict:
        return {
            "eventId": str(uuid.uuid4()),
            "priority": priority,
            "expiresAt": "2099-01-01T00:00:00+00:00",
            "xr": {"visible": True, "displayActionId": str(uuid.uuid4())},
            "robot": {"actions": [{"actionId": str(uuid.uuid4())}]},
        }

    async def test_admission_precedes_side_effects_and_waits_for_both_targets(self) -> None:
        hub = ExperienceHub()
        accepted = self.event(20)
        high = self.event(80)
        self.assertTrue((await hub.admit(accepted))["accepted"])
        self.assertFalse((await hub.admit(self.event(10)))["accepted"])
        high_admission = await hub.admit(high)
        self.assertTrue(high_admission["accepted"])
        display_id = high["xr"]["displayActionId"]
        robot_id = high["robot"]["actions"][0]["actionId"]
        await hub.record_result({"actionId": display_id, "status": "completed"})
        self.assertIsNotNone(hub.active_event)
        await hub.record_result({"actionId": robot_id, "status": "dispatched"})
        self.assertIsNone(hub.active_event)


class ConfiguredCopyTests(unittest.TestCase):
    def test_formal_content_catalog_has_personas_and_inner_os(self) -> None:
        orchestrator = ExperienceOrchestrator(CONTENT_ROOT)
        self.assertEqual(
            {item["personaId"] for item in orchestrator.personas.list()},
            {"gentle-companion", "energetic-partner", "prickly-softheart"},
        )
        orchestrator.select_persona("prickly-softheart")
        event = orchestrator.reminder_event({"eventId": str(uuid.uuid4()), "title": "喝水"})
        self.assertIn("喝水", event["speech"]["text"])
        self.assertTrue(event["innerOs"]["text"])

    def test_behavior_copy_and_distinct_display_action_are_configured(self) -> None:
        orchestrator = ExperienceOrchestrator(CONTENT_ROOT)
        orchestrator.select_persona("gentle-companion")
        event = orchestrator.reminder_event({"eventId": str(uuid.uuid4()), "title": "团队会议"})
        self.assertIn("团队会议", event["speech"]["text"])
        self.assertNotEqual(event["xr"]["displayActionId"], event["robot"]["actions"][0]["actionId"])
        self.assertEqual(event["xr"]["expression"], {"emotion": "warm", "face": "smile", "emoji": "😊", "intensity": 1.0})
        self.assertEqual(event["robot"]["actions"][0]["parameters"]["face"], "smile")


class PersonaTests(unittest.TestCase):
    def test_loader_and_rule_engine(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "personas.json").write_text(json.dumps({
                "defaultPersonaId": "demo",
                "personas": {"demo": {"version": "1", "traits": [], "speechStyle": "short", "innerOsStyle": "aside",
                                       "expressionMapping": {}, "behaviorWeights": {}, "preferredActions": [], "forbiddenTopics": []}},
            }), encoding="utf-8")
            (root / "behaviors.json").write_text(json.dumps({"behaviors": [
                {"id": "dance", "triggerType": "text", "contains": ["跳舞"], "priority": 100, "emotion": "excited", "robotBehaviorIntent": "dance"},
            ]}), encoding="utf-8")
            self.assertEqual(PersonaLoader(root).load()["personaId"], "demo")
            self.assertEqual(BehaviorRuleEngine(root).select(trigger_type="text", text="陪我跳舞")["id"], "dance")

    def test_invalid_persona_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "personas.json").write_text(json.dumps({"defaultPersonaId": "bad", "personas": {"bad": {}}}), encoding="utf-8")
            (root / "behaviors.json").write_text(json.dumps({"behaviors": []}), encoding="utf-8")
            with self.assertRaises(PersonaConfigError):
                PersonaLoader(root).load()

    def test_probability_capability_and_cooldown_persist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "personas.json").write_text(json.dumps({"defaultPersonaId": "demo", "personas": {"demo": {
                "version": "1", "traits": [], "speechStyle": "short", "innerOsStyle": "aside",
                "expressionMapping": {}, "behaviorWeights": {}, "preferredActions": [], "forbiddenTopics": []}}}), encoding="utf-8")
            (root / "behaviors.json").write_text(json.dumps({"behaviors": [
                {"id": "never", "triggerType": "companion", "probability": 0, "requiredCapabilities": ["missing"], "cooldown": 10},
                {"id": "once", "triggerType": "companion", "probability": 1, "requiredCapabilities": ["blink"], "cooldown": 60, "maxPerDay": 1},
            ]}), encoding="utf-8")
            clock_value = [datetime(2026, 8, 12, 12, tzinfo=timezone.utc)]
            engine = BehaviorRuleEngine(root, clock=lambda: clock_value[0])
            self.assertIsNone(engine.select(trigger_type="companion", context={"capabilities": []}))
            self.assertEqual(engine.select(trigger_type="companion", context={"capabilities": ["blink"]})["id"], "once")
            self.assertIsNone(engine.select(trigger_type="companion", context={"capabilities": ["blink"]}))
            restored = BehaviorRuleEngine(root, clock=lambda: clock_value[0])
            restored.restore_runtime_state(engine.runtime_state())
            self.assertIsNone(restored.select(trigger_type="companion", context={"capabilities": ["blink"]}))


class _FixedRandom:
    def random(self) -> float:
        return 0.0

    def choices(self, values, weights=None, k=1):
        return [values[-1]]


class _FakeDataService:
    def __init__(self, snapshot: dict):
        self.snapshot = snapshot
        self.calls: list[tuple[str, dict]] = []

    async def request(self, message_type: str, payload: dict | None = None):
        self.calls.append((message_type, payload or {}))
        if message_type == "proactive.tick":
            return self.snapshot
        if message_type == "state.get":
            return {"data": {}, "revision": 1}
        if message_type == "sensor.query_recent":
            return {"observations": []}
        if message_type == "farm.get_available_actions":
            return {"actions": ["water", "rest"]}
        if message_type == "farm.perform_action":
            return {"status": "completed"}
        if message_type == "state.put":
            return {"revision": 2}
        raise AssertionError(message_type)


class ProactiveTests(unittest.IsolatedAsyncioTestCase):
    async def test_idle_companion_and_game_invite(self) -> None:
        orchestrator = ExperienceOrchestrator(CONTENT_ROOT)
        orchestrator.select_persona("energetic-partner")
        orchestrator.rules.rng = _FixedRandom()
        orchestrator.rules.clock = lambda: datetime(2026, 8, 12, 12, tzinfo=timezone.utc)
        data = _FakeDataService({"idle": True, "reminders": [], "farmChanged": None})
        events = await ProactiveScheduler(data, orchestrator).tick()
        self.assertEqual({event["mode"] for event in events}, {"companion", "game"})

    async def test_farm_proactive_action_is_executed_before_event(self) -> None:
        orchestrator = ExperienceOrchestrator(CONTENT_ROOT)
        data = _FakeDataService({"idle": False, "reminders": [], "farmChanged": {"revision": 2}})
        events = await ProactiveScheduler(data, orchestrator).tick()
        self.assertEqual(events[0]["mode"], "farm")
        self.assertIn(("farm.perform_action", {"action": "water"}), data.calls)
