from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.experience_protocol import ProtocolValidationError, validate_action_result, validate_experience_event
from app.persona import BehaviorRuleEngine, PersonaConfigError, PersonaLoader


class ExperienceProtocolTests(unittest.TestCase):
    def _event(self) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "eventId": str(uuid.uuid4()), "sourceEventId": None, "personaId": "gentle-companion",
            "mode": "conversation", "priority": 100, "expiresAt": now,
            "speech": {}, "innerOs": {}, "robot": {}, "xr": {}, "app": {}, "interruptible": True,
        }

    def test_valid_experience_event_and_action_result(self) -> None:
        self.assertEqual(validate_experience_event(self._event())["mode"], "conversation")
        action = {
            "actionId": str(uuid.uuid4()), "deviceId": "mock-robot", "actionType": "nod", "status": "completed",
            "startedAt": datetime.now(timezone.utc).isoformat(), "completedAt": datetime.now(timezone.utc).isoformat(),
            "requestedParameters": {}, "measuredResult": {}, "error": None, "sourceEventId": None,
        }
        self.assertEqual(validate_action_result(action)["status"], "completed")

    def test_invalid_event_is_rejected(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_experience_event({"mode": "conversation"})


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
