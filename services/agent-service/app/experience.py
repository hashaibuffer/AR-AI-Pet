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

    def _event(self, *, turn: dict[str, Any], mode: str, behavior: dict[str, Any], source_event_id: str | None = None,
               speech: str | None = None, inner_os: str | None = None) -> dict[str, Any]:
        now = utc_now()
        persona = self.personas.load()
        intent = str(behavior.get("robotBehaviorIntent", "nod"))
        event = {
            "eventId": str(uuid.uuid4()),
            "sourceEventId": source_event_id,
            "personaId": persona["personaId"],
            "mode": mode,
            "priority": int(behavior.get("priority", turn.get("priority", 20))),
            "expiresAt": (now + timedelta(seconds=30)).isoformat(),
            "speech": {"text": speech if speech is not None else turn.get("spokenText", ""),
                       "emotion": behavior.get("emotion", turn.get("emotion", "calm")), "interruptible": True},
            "innerOs": {"text": inner_os if inner_os is not None else turn.get("innerOsText", ""), "durationMs": 4000, "anchor": "robot"},
            "robot": {"actions": [{"intent": intent, "parameters": {}}]},
            "xr": {"visible": True, "mode": "inner-os"},
            "app": {"refresh": True, "section": "home"},
            "interruptible": True,
        }
        return validate_experience_event(event)

    def from_turn(self, result: dict[str, Any], text: str) -> tuple[dict[str, Any], dict[str, Any]]:
        behavior = self.rules.select(trigger_type="text", text=text)
        if behavior.get("id") == "conversation":
            behavior = self.rules.select(trigger_type="turn", text=text)
        turn = validate_agent_turn_result({
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
        return turn, self._event(turn=turn, mode="conversation", behavior=behavior)

    def reminder_event(self, reminder: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="schedule.triggered")
        return self._event(
            turn={"spokenText": f"提醒你：{reminder.get('title', '有一项日程到时间了')}", "innerOsText": "该提醒已经到时间了。", "emotion": behavior.get("emotion")},
            mode="reminder", behavior=behavior, source_event_id=reminder.get("eventId"),
            speech=f"提醒你：{reminder.get('title', '有一项日程到时间了')}", inner_os="该提醒已经到时间了。",
        )

    def farm_event(self, farm: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="companion")
        return self._event(
            turn={"spokenText": "我去农场看一下。", "innerOsText": "轮到我自己照顾农场了。", "emotion": "calm"},
            mode="farm", behavior={**behavior, "robotBehaviorIntent": "farm_tend", "priority": 20},
            inner_os="轮到我自己照顾农场了。", speech="我去农场看一下。",
        )

    def sensor_event(self, observation: dict[str, Any]) -> dict[str, Any]:
        behavior = self.rules.select(trigger_type="sensor.face")
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
        events = [self.orchestrator.reminder_event(item) for item in snapshot.get("reminders", [])]
        if snapshot.get("farmChanged"):
            events.append(self.orchestrator.farm_event(snapshot["farmChanged"]))
        observations = (await self.data_service.request("sensor.query_recent", {"limit": 1})).get("observations", [])
        latest = observations[0] if observations else None
        if latest and self._sensor_initialized and latest.get("observationId") != self._last_sensor_id:
            events.append(self.orchestrator.sensor_event(latest))
        if latest:
            self._last_sensor_id = latest.get("observationId")
        self._sensor_initialized = True
        return events
