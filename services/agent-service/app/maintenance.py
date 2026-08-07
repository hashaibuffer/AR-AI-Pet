from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid
from typing import Any

from sqlalchemy import text

from .db import as_json, get_identity, session, utc_now


REPEAT_DELTA = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
}


def scan_due_schedules(now: datetime | None = None) -> list[dict[str, Any]]:
    """Mark due schedules and create one reminder event per scan."""
    now = now or utc_now()
    reminders: list[dict[str, Any]] = []
    with session() as conn:
        user_id, pet_id = get_identity(conn)
        rows = conn.execute(text("""
            SELECT id, title, description, starts_at, remind_at, repeat_type
            FROM schedules
            WHERE user_id = :user_id
              AND status = 'active'
              AND remind_at <= :now
              AND (reminded_at IS NULL OR reminded_at < remind_at)
            ORDER BY remind_at
            FOR UPDATE SKIP LOCKED
        """), {"user_id": user_id, "now": now}).mappings().all()
        for row in rows:
            due_at = row["remind_at"]
            repeat_type = row["repeat_type"]
            if repeat_type == "none":
                conn.execute(text("""
                    UPDATE schedules
                    SET status = 'completed', reminded_at = :now, updated_at = :now
                    WHERE id = :id AND user_id = :user_id
                """), {"id": row["id"], "user_id": user_id, "now": now})
            else:
                delta = REPEAT_DELTA[repeat_type]
                next_remind = due_at
                next_start = row["starts_at"]
                while next_remind <= now:
                    next_remind += delta
                    next_start += delta
                conn.execute(text("""
                    UPDATE schedules
                    SET starts_at = :starts_at, remind_at = :remind_at,
                        reminded_at = :now, updated_at = :now
                    WHERE id = :id AND user_id = :user_id
                """), {"id": row["id"], "user_id": user_id, "starts_at": next_start,
                       "remind_at": next_remind, "now": now})
            payload = {
                "scheduleId": str(row["id"]),
                "title": row["title"],
                "description": row["description"],
                "remindAt": due_at.isoformat(),
                "triggeredAt": now.isoformat(),
                "repeatType": repeat_type,
            }
            conn.execute(text("""
                INSERT INTO events (id, user_id, pet_id, event_type, source, payload, occurred_at, created_at)
                VALUES (:id, :user_id, :pet_id, 'schedule.triggered', 'system',
                        CAST(:payload AS jsonb), :occurred_at, :created_at)
            """), {"id": uuid.uuid4(), "user_id": user_id, "pet_id": pet_id,
                    "payload": as_json(payload), "occurred_at": now, "created_at": now})
            reminders.append(payload)
    return reminders


def prune_expired_messages(now: datetime | None = None) -> int:
    """Delete raw conversation messages after their seven-day retention window."""
    now = now or utc_now()
    with session() as conn:
        deleted = conn.execute(text("DELETE FROM messages WHERE expires_at <= :now"), {"now": now})
        deleted_count = int(deleted.rowcount or 0)
        if deleted_count:
            conn.execute(text("""
                UPDATE conversations AS c
                SET message_count = (
                    SELECT COUNT(*) FROM messages AS m WHERE m.conversation_id = c.id
                )
                WHERE c.message_count > 0
            """))
        return deleted_count
