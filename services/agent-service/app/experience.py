from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import uuid

from .data_service_client import DataServiceClient
from .experience_protocol import validate_agent_turn_result, validate_experience_event
from .persona import BehaviorRuleEngine, PersonaLoader


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExperienceOrchestrator:
    def __init__(self, content_root: str | Path = "content/runtime") -> None:
        self.personas = PersonaLoader(content_root)
        self.rules = BehaviorRuleEngine(content_root)
        self.persona_id: str | None = None

    def ensure_persona(self) -> dict[str, Any]:
        return self.select_persona(self.persona_id or self.personas.load()["personaId"])

    def select_persona(self, persona_id: str) -> dict[str, Any]:
        persona = self.personas.load(persona_id)
        self.persona_id = persona["personaId"]
        self.rules.set_behavior_weights(persona.get("behaviorWeights"))
        return persona

    def runtime_state(self) -> dict[str, Any]:
        return self.rules.runtime_state()

    def restore_runtime_state(self, state: dict[str, Any]) -> None:
        self.rules.restore_runtime_state(state)

    @staticmethod
    def _render(template: Any, fallback: str, context: dict[str, Any]) -> str:
        if not isinstance(template, str) or not template:
            return fallback
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace("{" + str(key) + "}", str(value or ""))
        return rendered

    def _event(
        self,
        *,
        turn: dict[str, Any],
        mode: str,
        behavior: dict[str, Any],
        source_event_id: str | None = None,
        speech: str | None = None,
        inner_os: str | None = None,
        event_id: str | None = None,
        action_id: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        persona = self.personas.load(self.persona_id)
        context = {**turn, "title": turn.get("title", ""), "action": turn.get("action", "")}
        spoken = speech if speech is not None else self._render(behavior.get("speechPrompt"), str(turn.get("spokenText", "")), context)
        thought = inner_os if inner_os is not None else self._render(behavior.get("innerOsPrompt"), str(turn.get("innerOsText", "")), context)
        event = {
            "version": "0.1",
            "eventId": event_id or str(uuid.uuid4()),
            "sourceEventId": source_event_id,
            "personaId": persona["personaId"],
            "mode": mode,
            "priority": int(behavior.get("priority", turn.get("priority", 20))),
            "expiresAt": (now + timedelta(seconds=30)).isoformat(),
            "speech": {"text": spoken, "emotion": behavior.get("emotion", turn.get("emotion", "calm")), "interruptible": True},
            "innerOs": {"text": thought, "durationMs": 4000, "anchor": "robot"},
            "robot": {"actions": [{"actionId": action_id or str(uuid.uuid4()), "intent": str(behavior.get("robotBehaviorIntent", "nod")), "parameters": {}}]},
            "xr": {"visible": True, "mode": "inner-os", "displayActionId": str(uuid.uuid4())},
            "app": {"refresh": True, "section": "home"},
            "interruptible": True,
        }
        return validate_experience_event(event)

    def from_turn(self, result: dict[str, Any], text: str) -> tuple[dict[str, Any], dict[str, Any]]:
        context = {"requiresUserPresent": True, "requiresIdle": True, "capabilities": ["nod", "wave", "dance", "farm_tend", "blink"]}
        behavior = self.rules.select(trigger_type="text", text=text, context=context)
        if behavior is None:
            behavior = self.rules.select(trigger_type="turn", text=text, context=context) or {"emotion": "warm", "priority": 100, "robotBehaviorIntent": "nod"}
        turn = validate_agent_turn_result({
            "version": "0.1",
            "turnId": str(uuid.uuid4()),
            "conversationId": result["conversationId"],
            "spokenText": result.get("text", ""),
            "innerOsText": "我会陪你完成这件事。",
            "emotion": behavior.get("emotion", "warm"),
            "behaviorIntent": behavior.get("robotBehaviorIntent", "nod"),
            "priority": 100,
            "interruptible": True,
            "toolCallSummaries": result.get("toolCalls", []),
            "sourceEventId": None,
            "timestamp": utc_now().isoformat(),
        })
        return turn, self._event(turn=turn, mode="conversation", behavior=behavior, event_id=result.get("experienceEventId"))

    def reminder_event(self, reminder: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="schedule.triggered", context={"requiresUserPresent": True, "capabilities": ["wave"]}) or {"emotion": "warm", "priority": 80, "robotBehaviorIntent": "wave", "speechPrompt": "提醒你：{title}", "innerOsPrompt": "这个提醒到时间了。"}
        return self._event(
            turn={"spokenText": "", "innerOsText": "", "title": reminder.get("title", ""), "emotion": behavior.get("emotion")},
            mode="reminder", behavior=behavior, source_event_id=reminder.get("eventId"),
        )

    def farm_event(self, farm: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="farm", context={"requiresUserPresent": False, "requiresIdle": True, "capabilities": ["farm_tend"]}) or {"emotion": "calm", "priority": 20, "speechPrompt": "我去农场照料一下。", "innerOsPrompt": "轮到我照顾自己的农场了。"}
        return self._event(
            turn={"spokenText": "", "innerOsText": "", "emotion": "calm", "action": farm.get("data", {}).get("lastAction", "")},
            mode="farm", behavior={**behavior, "robotBehaviorIntent": "farm_tend", "priority": 20},
        )

    def sensor_event(self, observation: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="sensor.face", context={"requiresUserPresent": True, "capabilities": ["wave"]}) or {"emotion": "warm", "priority": 60, "robotBehaviorIntent": "wave", "speechPrompt": "我看到你了。", "innerOsPrompt": "检测到新的面对面互动。"}
        present = bool((observation.get("value") or {}).get("present"))
        if not present:
            behavior = {**behavior, "speechPrompt": "", "innerOsPrompt": "我没有看到人。"}
        return self._event(
            turn={"spokenText": "", "innerOsText": "", "emotion": behavior.get("emotion", "warm"), "present": present},
            mode="sensor", behavior=behavior,
        )


class ProactiveScheduler:
    def __init__(self, data_service: DataServiceClient, orchestrator: ExperienceOrchestrator) -> None:
        self.data_service = data_service
        self.orchestrator = orchestrator
        self._sensor_initialized = False
        self._last_sensor_id: str | None = None

    async def tick(self) -> list[dict[str, Any]]:
        snapshot = await self.data_service.request("proactive.tick")
        pet_state = await self.data_service.request("state.get", {"domain": "pet"})
        self.orchestrator.restore_runtime_state((pet_state.get("data") or {}).get("behaviorRuntime") or {})
        events = [self.orchestrator.reminder_event(item) for item in snapshot.get("reminders", [])]
        if snapshot.get("farmChanged"):
            available = await self.data_service.request("farm.get_available_actions")
            actions = [item for item in available.get("actions", []) if item != "rest"]
            if actions:
                farm_result = await self.data_service.request("farm.perform_action", {"action": actions[0]})
            else:
                farm_result = snapshot["farmChanged"]
            events.append(self.orchestrator.farm_event(farm_result))
        observations = (await self.data_service.request("sensor.query_recent", {"limit": 1})).get("observations", [])
        latest = observations[0] if observations else None
        if latest and self._sensor_initialized and latest.get("observationId") != self._last_sensor_id:
            events.append(self.orchestrator.sensor_event(latest))
        if latest:
            self._last_sensor_id = latest.get("observationId")
        self._sensor_initialized = True
        if snapshot.get("idle"):
            context = {"requiresUserPresent": True, "requiresIdle": True, "capabilities": ["nod", "blink"]}
            companion = self.orchestrator.rules.select(trigger_type="companion", context=context)
            if companion:
                events.append(self.orchestrator._event(turn={"spokenText": "", "innerOsText": ""}, mode="companion", behavior=companion))
            invite = self.orchestrator.rules.select(trigger_type="game_invite", context=context)
            if invite:
                events.append(self.orchestrator._event(turn={"spokenText": "", "innerOsText": ""}, mode="game", behavior=invite))
        if events:
            state = dict(pet_state.get("data") or {})
            state["behaviorRuntime"] = self.orchestrator.runtime_state()
            await self.data_service.request("state.put", {"domain": "pet", "expectedRevision": pet_state["revision"], "data": state})
        return events
