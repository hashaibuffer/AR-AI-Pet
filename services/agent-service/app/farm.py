from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from sqlalchemy import text

from .db import as_json, get_identity, session, utc_now

STAGES = ["seed", "sprout", "growing", "ripe"]
STAGE_SECONDS = {"seed": 30, "sprout": 60, "growing": 90}


def parse_time(value: str | None) -> datetime:
    if not value:
        return utc_now()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def advance_farm() -> dict[str, Any] | None:
    """補算时间差；不依赖后台循环执行次数。"""
    now = utc_now()
    with session() as conn:
        user_id, pet_id = get_identity(conn)
        row = conn.execute(text("""
            SELECT id, revision, data FROM state_documents
            WHERE pet_id = :pet_id AND domain = 'farm' FOR UPDATE
        """), {"pet_id": pet_id}).mappings().one()
        data = dict(row["data"])
        changed = False
        for plot in data.get("plots", []):
            stage = plot.get("stage")
            started = parse_time(plot.get("stageStartedAt"))
            original_stage = stage
            while stage in STAGE_SECONDS and (now - started).total_seconds() >= STAGE_SECONDS[stage]:
                started += timedelta(seconds=STAGE_SECONDS[stage])
                stage = STAGES[STAGES.index(stage) + 1]
            if stage != original_stage:
                plot["stage"] = stage
                plot["stageStartedAt"] = started.isoformat()
                changed = True
        if not changed:
            return None
        data["currentActivity"] = "harvesting" if any(p.get("stage") == "ripe" for p in data.get("plots", [])) else "watering"
        data["lastTickAt"] = now.isoformat()
        revision = int(row["revision"]) + 1
        conn.execute(text("""
            UPDATE state_documents
            SET data = CAST(:data AS jsonb), revision = :revision, updated_at = :updated_at
            WHERE id = :id
        """), {"id": row["id"], "data": as_json(data), "revision": revision, "updated_at": now})
        conn.execute(text("""
            INSERT INTO events (id, user_id, pet_id, event_type, source, payload, occurred_at, created_at)
            VALUES (:id, :user_id, :pet_id, 'farm.activity_changed', 'system', CAST(:payload AS jsonb), :occurred_at, :created_at)
        """), {"id": uuid.uuid4(), "user_id": user_id, "pet_id": pet_id,
                "payload": as_json({"revision": revision, "data": data}), "occurred_at": now, "created_at": now})
        return {"domain": "farm", "revision": revision, "data": data}
