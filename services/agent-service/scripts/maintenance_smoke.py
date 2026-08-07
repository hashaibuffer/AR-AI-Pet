from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import sys
import uuid

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.maintenance import prune_expired_messages, scan_due_schedules


def main() -> None:
    db.seed_defaults()
    now = db.utc_now()
    with db.session() as conn:
        user_id, pet_id = db.get_identity(conn)
        schedule_id = uuid.uuid4()
        conn.execute(text("""
            INSERT INTO schedules (id, user_id, title, starts_at, remind_at, repeat_type, status, created_at, updated_at)
            VALUES (:id, :user_id, 'Maintenance smoke reminder', :starts_at, :remind_at, 'none', 'active', :now, :now)
        """), {"id": schedule_id, "user_id": user_id, "starts_at": now - timedelta(minutes=2),
                "remind_at": now - timedelta(minutes=1), "now": now})
        conversation_id = uuid.uuid4()
        conn.execute(text("""
            INSERT INTO conversations (id, user_id, pet_id, channel, message_count, started_at)
            VALUES (:id, :user_id, :pet_id, 'unity_text', 1, :now)
        """), {"id": conversation_id, "user_id": user_id, "pet_id": pet_id, "now": now})
        conn.execute(text("""
            INSERT INTO messages (id, conversation_id, role, content, created_at, expires_at)
            VALUES (:id, :conversation_id, 'user', 'expired smoke message', :now, :expires_at)
        """), {"id": uuid.uuid4(), "conversation_id": conversation_id, "now": now - timedelta(days=8),
                "expires_at": now - timedelta(minutes=1)})

    reminders = scan_due_schedules(now)
    assert any(item["scheduleId"] == str(schedule_id) for item in reminders), reminders
    assert prune_expired_messages(now) == 1
    with db.session() as conn:
        schedule_status = conn.execute(text("SELECT status FROM schedules WHERE id = :id"), {"id": schedule_id}).scalar_one()
        message_count = conn.execute(text("SELECT message_count FROM conversations WHERE id = :id"), {"id": conversation_id}).scalar_one()
    assert schedule_status == "completed", schedule_status
    assert message_count == 0, message_count
    print("MAINTENANCE_SMOKE_OK")


if __name__ == "__main__":
    main()
