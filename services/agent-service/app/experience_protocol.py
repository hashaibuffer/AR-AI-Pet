from __future__ import annotations

from datetime import datetime
from typing import Any


class ProtocolValidationError(ValueError):
    pass


def _required(value: dict[str, Any], fields: tuple[str, ...], name: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ProtocolValidationError(f"{name} missing fields: {', '.join(missing)}")


def _uuid(value: Any, field: str) -> None:
    if not isinstance(value, str):
        raise ProtocolValidationError(f"{field} must be a UUID string")
    import uuid

    try:
        uuid.UUID(value)
    except ValueError as exc:
        raise ProtocolValidationError(f"{field} must be a UUID string") from exc


def _timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str):
        raise ProtocolValidationError(f"{field} must be an ISO 8601 timestamp")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProtocolValidationError(f"{field} must be an ISO 8601 timestamp") from exc


def validate_agent_turn_result(value: dict[str, Any]) -> dict[str, Any]:
    _required(value, ("turnId", "conversationId", "spokenText", "innerOsText", "emotion", "behaviorIntent",
                      "priority", "interruptible", "toolCallSummaries", "timestamp"), "AgentTurnResult")
    _uuid(value["turnId"], "turnId")
    _uuid(value["conversationId"], "conversationId")
    _timestamp(value["timestamp"], "timestamp")
    if not isinstance(value["spokenText"], str) or not isinstance(value["innerOsText"], str):
        raise ProtocolValidationError("AgentTurnResult text fields must be strings")
    if not isinstance(value["priority"], int) or not 0 <= value["priority"] <= 100:
        raise ProtocolValidationError("AgentTurnResult priority must be 0..100")
    if not isinstance(value["interruptible"], bool) or not isinstance(value["toolCallSummaries"], list):
        raise ProtocolValidationError("AgentTurnResult has invalid control fields")
    return value


def validate_experience_event(value: dict[str, Any]) -> dict[str, Any]:
    _required(value, ("eventId", "sourceEventId", "personaId", "mode", "priority", "expiresAt", "speech",
                      "innerOs", "robot", "xr", "app", "interruptible"), "ExperienceEvent")
    _uuid(value["eventId"], "eventId")
    if value["sourceEventId"] is not None:
        _uuid(value["sourceEventId"], "sourceEventId")
    _timestamp(value["expiresAt"], "expiresAt")
    if value["mode"] not in {"conversation", "reminder", "farm", "game", "sensor", "companion"}:
        raise ProtocolValidationError("ExperienceEvent mode is invalid")
    if not isinstance(value["priority"], int) or not 0 <= value["priority"] <= 100:
        raise ProtocolValidationError("ExperienceEvent priority must be 0..100")
    for field in ("speech", "innerOs", "robot", "xr", "app"):
        if not isinstance(value[field], dict):
            raise ProtocolValidationError(f"ExperienceEvent {field} must be an object")
    return value


def validate_sensor_observation(value: dict[str, Any]) -> dict[str, Any]:
    _required(value, ("observationId", "deviceId", "sensorType", "observedAt", "value", "confidence", "unit", "source", "privacyClass"), "SensorObservation")
    _uuid(value["observationId"], "observationId")
    _timestamp(value["observedAt"], "observedAt")
    if value["sensorType"] not in {"camera.face", "microphone.asr", "touch", "imu", "base.odometry"}:
        raise ProtocolValidationError("SensorObservation sensorType is invalid")
    if not isinstance(value["confidence"], (int, float)) or not 0 <= value["confidence"] <= 1:
        raise ProtocolValidationError("SensorObservation confidence must be 0..1")
    return value


def validate_action_result(value: dict[str, Any]) -> dict[str, Any]:
    _required(value, ("actionId", "deviceId", "actionType", "status", "startedAt", "completedAt",
                      "requestedParameters", "measuredResult", "error", "sourceEventId"), "ActionResult")
    _uuid(value["actionId"], "actionId")
    if value["sourceEventId"] is not None:
        _uuid(value["sourceEventId"], "sourceEventId")
    for field in ("startedAt", "completedAt"):
        if value[field] is not None:
            _timestamp(value[field], field)
    if value["status"] not in {"accepted", "started", "completed", "failed", "cancelled", "timeout"}:
        raise ProtocolValidationError("ActionResult status is invalid")
    if not isinstance(value["requestedParameters"], dict) or not isinstance(value["measuredResult"], dict):
        raise ProtocolValidationError("ActionResult result fields must be objects")
    return value
