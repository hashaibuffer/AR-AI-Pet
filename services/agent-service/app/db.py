from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from sqlalchemy import create_engine, text

from .settings import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@contextmanager
def session() -> Iterator[Any]:
    with engine.begin() as connection:
        yield connection


def as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def seed_defaults() -> None:
    now = utc_now()
    with session() as conn:
        user = conn.execute(text("SELECT id FROM users ORDER BY created_at LIMIT 1")).scalar()
        if user is None:
            user = uuid.uuid4()
            conn.execute(text("""
                INSERT INTO users (id, display_name, timezone, created_at, updated_at)
                VALUES (:id, 'Demo User', 'Asia/Shanghai', :now, :now)
            """), {"id": user, "now": now})
        pet = conn.execute(text("SELECT id FROM pets WHERE user_id = :user_id"), {"user_id": user}).scalar()
        if pet is None:
            pet = uuid.uuid4()
            conn.execute(text("""
                INSERT INTO pets (id, user_id, name, persona_version, created_at, updated_at)
                VALUES (:id, :user_id, '小屿', 'v0.1', :now, :now)
            """), {"id": pet, "user_id": user, "now": now})
        defaults = {
            "pet": {"mood": "neutral", "energy": 75, "intimacy": 0, "lastInteractionAt": now.isoformat()},
            "home": {"activeThemeResourceId": "home.default", "unlockedResourceIds": [], "displaySettings": {}},
            "farm": {
                "plots": [{"id": "plot-0-0", "cropId": "crop.tomato", "stage": "seed", "stageStartedAt": now.isoformat(), "waterCount": 0}],
                "inventory": {}, "currentActivity": "resting", "lastTickAt": now.isoformat()
            },
        }
        for domain, data in defaults.items():
            exists = conn.execute(text("SELECT 1 FROM state_documents WHERE pet_id = :pet_id AND domain = :domain"), {"pet_id": pet, "domain": domain}).scalar()
            if not exists:
                conn.execute(text("""
                    INSERT INTO state_documents (id, user_id, pet_id, domain, schema_version, revision, data, updated_at)
                    VALUES (:id, :user_id, :pet_id, :domain, 1, 1, CAST(:data AS jsonb), :now)
                """), {"id": uuid.uuid4(), "user_id": user, "pet_id": pet, "domain": domain, "data": as_json(data), "now": now})


def get_identity(conn: Any) -> tuple[uuid.UUID, uuid.UUID]:
    row = conn.execute(text("""
        SELECT users.id AS user_id, pets.id AS pet_id
        FROM users JOIN pets ON pets.user_id = users.id
        ORDER BY users.created_at LIMIT 1
    """)).mappings().one()
    return row["user_id"], row["pet_id"]


def row_json(row: Any) -> dict[str, Any]:
    result = dict(row)
    for key, value in list(result.items()):
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
        elif isinstance(value, uuid.UUID):
            result[key] = str(value)
    return result
