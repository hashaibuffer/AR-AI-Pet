from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PersonaConfigError(ValueError):
    pass


class PersonaLoader:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._data: dict[str, Any] | None = None

    def _read(self) -> dict[str, Any]:
        if self._data is None:
            path = self.root / "personas.json"
            try:
                self._data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise PersonaConfigError(f"cannot load personas: {path}") from exc
        return self._data

    def load(self, persona_id: str | None = None) -> dict[str, Any]:
        data = self._read()
        personas = data.get("personas")
        selected = persona_id or data.get("defaultPersonaId")
        if not isinstance(personas, dict) or not isinstance(selected, str) or selected not in personas:
            raise PersonaConfigError("persona configuration has no valid default persona")
        persona = personas[selected]
        required = ("version", "traits", "speechStyle", "innerOsStyle", "expressionMapping", "behaviorWeights", "preferredActions", "forbiddenTopics")
        missing = [field for field in required if field not in persona]
        if missing:
            raise PersonaConfigError(f"persona {selected} missing fields: {', '.join(missing)}")
        return {"personaId": selected, **persona}


class BehaviorRuleEngine:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._rules: list[dict[str, Any]] | None = None
        self._last_trigger: dict[str, datetime] = {}
        self._daily_count: dict[str, tuple[str, int]] = {}

    def _read(self) -> list[dict[str, Any]]:
        if self._rules is None:
            path = self.root / "behaviors.json"
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise PersonaConfigError(f"cannot load behaviors: {path}") from exc
            self._rules = list(data.get("behaviors", []))
        return self._rules

    def select(self, *, trigger_type: str, text: str = "", is_busy: bool = False, is_user_present: bool = True) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        candidates: list[dict[str, Any]] = []
        for rule in self._read():
            if rule.get("triggerType") != trigger_type:
                continue
            contains = rule.get("contains", [])
            if contains and not any(word in text for word in contains):
                continue
            if not is_user_present and trigger_type in {"sensor.face", "text"}:
                continue
            if is_busy and int(rule.get("priority", 0)) < 80:
                continue
            quiet_hours = rule.get("quietHours", [])
            if isinstance(quiet_hours, list) and now.hour in quiet_hours:
                continue
            previous = self._last_trigger.get(str(rule.get("id")))
            if previous and (now - previous).total_seconds() < int(rule.get("cooldown", 0)):
                continue
            day, count = self._daily_count.get(str(rule.get("id")), (now.date().isoformat(), 0))
            if day == now.date().isoformat() and int(rule.get("maxPerDay", 0)) > 0 and count >= int(rule.get("maxPerDay")):
                continue
            candidates.append(rule)
        if not candidates:
            return {"id": "conversation", "priority": 100, "emotion": "warm", "robotBehaviorIntent": "nod"}
        selected = sorted(candidates, key=lambda item: int(item.get("priority", 0)), reverse=True)[0]
        key = str(selected.get("id"))
        self._last_trigger[key] = now
        day, count = self._daily_count.get(key, (now.date().isoformat(), 0))
        self._daily_count[key] = (now.date().isoformat(), count + 1 if day == now.date().isoformat() else 1)
        return selected
