from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class ProtocolValidationError(ValueError):
    pass


def _protocol_root() -> Path:
    configured = os.getenv("PROTOCOL_ROOT")
    if configured:
        return Path(configured)
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / "packages" / "protocol"
    if candidate.exists():
        return candidate
    return Path("/app/packages/protocol")


def _validator(name: str) -> Draft202012Validator:
    path = _protocol_root() / "schemas" / f"{name}.schema.json"
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProtocolValidationError(f"protocol schema unavailable: {path}") from exc
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate(name: str, value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProtocolValidationError(f"{name} must be an object")
    errors = sorted(_validator(name).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        path = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise ProtocolValidationError(f"{name} invalid at {path}: {errors[0].message}")
    return value


def validate_agent_turn_result(value: dict[str, Any]) -> dict[str, Any]:
    return _validate("agent-turn-result", value)


def validate_experience_event(value: dict[str, Any]) -> dict[str, Any]:
    return _validate("experience-event", value)


def validate_sensor_observation(value: dict[str, Any]) -> dict[str, Any]:
    return _validate("sensor-observation", value)


def validate_action_result(value: dict[str, Any]) -> dict[str, Any]:
    return _validate("action-result", value)
