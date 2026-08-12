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

    def _event(self, *, turn: dict[str, Any], mode: str, behavior: dict[str, Any], source_event_id: str | None = None,
               speech: str | None = None, inner_os: str | None = None, event_id: str | None = None,
               action_id: str | None = None) -> dict[str, Any]:
        now = utc_now()
        persona = self.personas.load(self.persona_id)
        intent = str(behavior.get("robotBehaviorIntent", "nod"))
        event = {
            "version": "0.1",
            "eventId": event_id or str(uuid.uuid4()),
            "sourceEventId": source_event_id,
            "personaId": persona["personaId"],
            "mode": mode,
            "priority": int(behavior.get("priority", turn.get("priority", 20))),
            "expiresAt": (now + timedelta(seconds=30)).isoformat(),
            "speech": {"text": speech if speech is not None else turn.get("spokenText", ""),
                       "emotion": behavior.get("emotion", turn.get("emotion", "calm")), "interruptible": True},
            "innerOs": {"text": inner_os if inner_os is not None else turn.get("innerOsText", ""), "durationMs": 4000, "anchor": "robot"},
            "robot": {"actions": [{"actionId": action_id or str(uuid.uuid4()), "intent": intent, "parameters": {}}]},
            "xr": {"visible": True, "mode": "inner-os"},
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
            "innerOsText": f"我会陪你完成：{result.get('text', '')[:32]}",
            "emotion": behavior.get("emotion", "warm"),
            "behaviorIntent": behavior.get("robotBehaviorIntent", "nod"),
            "priority": 100,
            "interruptible": True,
            "toolCallSummaries": result.get("toolCalls", []),
            "sourceEventId": None,
            "timestamp": utc_now().isoformat(),
        })
        event_id = result.get("experienceEventId")
        return turn, self._event(turn=turn, mode="conversation", behavior=behavior, event_id=event_id, action_id=event_id)

    def reminder_event(self, reminder: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="schedule.triggered", context={"requiresUserPresent": True, "capabilities": ["wave"]}) or {"emotion": "warm", "priority": 80, "robotBehaviorIntent": "wave"}
        return self._event(
            turn={"spokenText": f"提醒你：{reminder.get('title', '有一项日程到时间了')}", "innerOsText": "该提醒已经到时间了。", "emotion": behavior.get("emotion")},
            mode="reminder", behavior=behavior, source_event_id=reminder.get("eventId"),
            speech=f"提醒你：{reminder.get('title', '有一项日程到时间了')}", inner_os="该提醒已经到时间了。",
        )

    def farm_event(self, farm: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="farm", context={"requiresUserPresent": False, "requiresIdle": True, "capabilities": ["farm_tend"]}) or {"emotion": "calm", "priority": 20}
        return self._event(
            turn={"spokenText": "我去农场看一下。", "innerOsText": "轮到我自己照顾农场了。", "emotion": "calm"},
            mode="farm", behavior={**behavior, "robotBehaviorIntent": "farm_tend", "priority": 20},
            inner_os="轮到我自己照顾农场了。", speech="我去农场看一下。",
        )

    def sensor_event(self, observation: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="sensor.face", context={"requiresUserPresent": True, "capabilities": ["wave"]}) or {"emotion": "warm", "priority": 60, "robotBehaviorIntent": "wave"}
        present = bool((observation.get("value") or {}).get("present"))
        return self._event(
            turn={"spokenText": "我看到你了。" if present else "", "innerOsText": "检测到新的面对面互动。", "emotion": behavior.get("emotion", "warm")},
            mode="sensor", behavior=behavior, source_event_id=None,
            speech="我看到你了。" if present else "", inner_os="检测到新的面对面互动。",
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
                await self.data_service.request("farm.perform_action", {"action": actions[0]})
            events.append(self.orchestrator.farm_event(snapshot["farmChanged"]))
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
                events.append(self.orchestrator._event(turn={"spokenText": "我在这里陪你。", "innerOsText": "安静陪你一会儿。"}, mode="companion", behavior=companion))
            invite = self.orchestrator.rules.select(trigger_type="game_invite", context=context)
            if invite:
                events.append(self.orchestrator._event(turn={"spokenText": "要不要和我玩一局快艇骰子？", "innerOsText": "想和你来一局。"}, mode="game", behavior=invite))
        if events:
            state = dict(pet_state.get("data") or {})
            state["behaviorRuntime"] = self.orchestrator.runtime_state()
            await self.data_service.request("state.put", {"domain": "pet", "expectedRevision": pet_state["revision"], "data": state})
        return events
