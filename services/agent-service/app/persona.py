from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


class PersonaConfigError(ValueError):
    pass


class PersonaLoader:
    REQUIRED = ("version", "traits", "speechStyle", "innerOsStyle", "expressionMapping", "behaviorWeights", "preferredActions", "forbiddenTopics")

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._data: dict[str, Any] | None = None

    def _read(self) -> dict[str, Any]:
        if self._data is None:
            try:
                self._data = json.loads((self.root / "personas.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise PersonaConfigError(f"cannot load personas from {self.root}") from exc
        return self._data

    def list(self) -> list[dict[str, str]]:
        personas = self._read().get("personas", {})
        return [{"personaId": key, "version": value.get("version", "")} for key, value in personas.items()]

    def load(self, persona_id: str | None = None) -> dict[str, Any]:
        data = self._read()
        personas = data.get("personas")
        selected = persona_id or data.get("defaultPersonaId")
        if not isinstance(personas, dict) or not isinstance(selected, str) or selected not in personas:
            raise PersonaConfigError(f"unknown persona: {selected}")
        persona = personas[selected]
        missing = [field for field in self.REQUIRED if field not in persona]
        if missing:
            raise PersonaConfigError(f"persona {selected} missing fields: {', '.join(missing)}")
        return {"personaId": selected, **persona}


class BehaviorRuleEngine:
    def __init__(self, root: str | Path, *, clock: Callable[[], datetime] | None = None, rng: random.Random | None = None) -> None:
        self.root = Path(root)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.rng = rng or random.Random()
        self._rules: list[dict[str, Any]] | None = None
        self._last_trigger: dict[str, str] = {}
        self._daily_count: dict[str, tuple[str, int]] = {}
        self.behavior_weights: dict[str, float] = {}

    def set_behavior_weights(self, weights: dict[str, Any] | None) -> None:
        self.behavior_weights = {str(key): max(0.0, float(value)) for key, value in (weights or {}).items()}

    def _read(self) -> list[dict[str, Any]]:
        if self._rules is None:
            try:
                data = json.loads((self.root / "behaviors.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise PersonaConfigError(f"cannot load behaviors from {self.root}") from exc
            self._rules = list(data.get("behaviors", []))
        return self._rules

    def runtime_state(self) -> dict[str, Any]:
        return {"lastTrigger": self._last_trigger, "dailyCount": self._daily_count}

    def restore_runtime_state(self, state: dict[str, Any]) -> None:
        self._last_trigger = {str(k): str(v) for k, v in (state.get("lastTrigger") or {}).items()}
        self._daily_count = {str(k): (str(v[0]), int(v[1])) for k, v in (state.get("dailyCount") or {}).items() if isinstance(v, (list, tuple)) and len(v) == 2}

    def select(self, *, trigger_type: str, text: str = "", context: dict[str, Any] | None = None) -> dict[str, Any] | None:
        context = context or {}
        now = self.clock()
        candidates: list[dict[str, Any]] = []
        for rule in self._read():
            if rule.get("triggerType") != trigger_type:
                continue
            if rule.get("contains") and not any(word in text for word in rule["contains"]):
                continue
            conditions = rule.get("conditions") or {}
            if any(context.get(key) != expected for key, expected in conditions.items()):
                continue
            if any(cap not in set(context.get("capabilities", [])) for cap in rule.get("requiredCapabilities", [])):
                continue
            if self.rng.random() > float(rule.get("probability", 1)):
                continue
            key = str(rule.get("id"))
            previous = self._last_trigger.get(key)
            if previous:
                previous_time = datetime.fromisoformat(previous)
                if (now - previous_time).total_seconds() < int(rule.get("cooldown", 0)):
                    continue
            quiet_hours = rule.get("quietHours", [])
            if now.hour in quiet_hours:
                continue
            day, count = self._daily_count.get(key, (now.date().isoformat(), 0))
            if day == now.date().isoformat() and int(rule.get("maxPerDay", 0)) and count >= int(rule["maxPerDay"]):
                continue
            candidates.append(rule)
        if not candidates:
            return None
        weights = [self.behavior_weights.get(str(rule.get("robotBehaviorIntent", "")), float(rule.get("weight", 1))) for rule in candidates]
        if not any(weights):
            weights = [1.0 for _ in candidates]
        selected = self.rng.choices(candidates, weights=weights, k=1)[0]
        key = str(selected["id"])
        self._last_trigger[key] = now.isoformat()
        day, count = self._daily_count.get(key, (now.date().isoformat(), 0))
        self._daily_count[key] = (now.date().isoformat(), count + 1 if day == now.date().isoformat() else 1)
        return selected
