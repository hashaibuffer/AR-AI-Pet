from __future__ import annotations

import asyncio
import json
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import text

from . import db
from .farm import advance_farm
from .maintenance import prune_expired_messages, scan_due_schedules
from .experience_protocol import ProtocolValidationError, validate_action_result, validate_experience_event, validate_sensor_observation
from .settings import (
    FARM_TICK_SECONDS,
    MEMORY_JOB_LEASE_SECONDS,
    MEMORY_MAX_ATTEMPTS,
    MEMORY_RETRY_BASE_SECONDS,
    PROTOCOL_VERSION,
)


class Connections:
    def __init__(self) -> None:
        self.items: set[WebSocket] = set()

    async def add(self, socket: WebSocket) -> None:
        await socket.accept()
        self.items.add(socket)

    def remove(self, socket: WebSocket) -> None:
        self.items.discard(socket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for socket in self.items:
            try:
                await socket.send_json(message)
            except Exception:
                dead.append(socket)
        for socket in dead:
            self.remove(socket)


connections = Connections()


def response(request_id: str | None, message_type: str, status: str, payload: Any = None) -> dict[str, Any]:
    return {"requestId": request_id, "type": message_type, "status": status, "payload": payload or {}}


def parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


async def recalc_farm_and_broadcast() -> dict[str, Any] | None:
    changed = advance_farm()
    if changed:
        await connections.broadcast({"type": "farm.state.changed", "status": "ok", "payload": changed})
    return changed


def bootstrap() -> dict[str, Any]:
    db.seed_defaults()
    with db.session() as conn:
        user_id, pet_id = db.get_identity(conn)
        states = conn.execute(text("""
            SELECT domain, schema_version, revision, data, updated_at
            FROM state_documents WHERE pet_id = :pet_id
        """), {"pet_id": pet_id}).mappings().all()
        schedules = conn.execute(text("""
            SELECT * FROM schedules WHERE user_id = :user_id AND status = 'active' ORDER BY remind_at
        """), {"user_id": user_id}).mappings().all()
        games = conn.execute(text("""
            SELECT * FROM game_sessions WHERE user_id = :user_id AND status = 'playing'
            ORDER BY updated_at DESC LIMIT 1
        """), {"user_id": user_id}).mappings().all()
        return {
            "userId": str(user_id),
            "petId": str(pet_id),
            "states": [{"domain": row["domain"], "schemaVersion": row["schema_version"], "revision": row["revision"],
                         "data": row["data"], "updatedAt": row["updated_at"].isoformat()} for row in states],
            "schedules": [db.row_json(row) for row in schedules],
            "activeGame": db.row_json(games[0]) if games else None,
        }


def state_get(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    domain = payload.get("domain")
    if domain not in {"pet", "home", "farm"}:
        raise ValueError("invalid state domain")
    with db.session() as conn:
        _, pet_id = db.get_identity(conn)
        row = conn.execute(text("""
            SELECT domain, schema_version, revision, data, updated_at
            FROM state_documents WHERE pet_id = :pet_id AND domain = :domain
        """), {"pet_id": pet_id, "domain": domain}).mappings().one()
        return {"domain": row["domain"], "schemaVersion": row["schema_version"], "revision": row["revision"],
                "data": row["data"], "updatedAt": row["updated_at"].isoformat()}


def state_put(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    db.seed_defaults()
    domain = payload.get("domain")
    expected = payload.get("expectedRevision")
    data = payload.get("data")
    if domain not in {"pet", "home", "farm"} or not isinstance(data, dict) or not isinstance(expected, int):
        raise ValueError("state.put requires domain, expectedRevision and object data")
    now = db.utc_now()
    with db.session() as conn:
        user_id, pet_id = db.get_identity(conn)
        row = conn.execute(text("""
            SELECT id, revision, data FROM state_documents
            WHERE pet_id = :pet_id AND domain = :domain FOR UPDATE
        """), {"pet_id": pet_id, "domain": domain}).mappings().one()
        if row["revision"] != expected:
            return "conflict", {"latestRevision": row["revision"], "latestState": row["data"]}
        revision = expected + 1
        conn.execute(text("""
            UPDATE state_documents SET data = CAST(:data AS jsonb), revision = :revision, updated_at = :updated_at
            WHERE id = :id
        """), {"id": row["id"], "data": db.as_json(data), "revision": revision, "updated_at": now})
        conn.execute(text("""
            INSERT INTO events (id, user_id, pet_id, event_type, source, payload, occurred_at, created_at)
            VALUES (:id, :user_id, :pet_id, :event_type, 'unity', CAST(:payload AS jsonb), :occurred_at, :created_at)
        """), {"id": uuid.uuid4(), "user_id": user_id, "pet_id": pet_id, "event_type": f"state.{domain}_changed",
                "payload": db.as_json({"revision": revision}), "occurred_at": now, "created_at": now})
        return "ok", {"domain": domain, "revision": revision, "data": data}


def schedule_upsert(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    now = db.utc_now()
    with db.session() as conn:
        user_id, _ = db.get_identity(conn)
        schedule_id = uuid.UUID(payload["id"]) if payload.get("id") else uuid.uuid4()
        values = {"id": schedule_id, "user_id": user_id, "title": payload["title"], "description": payload.get("description"),
                  "starts_at": parse_time(payload["startsAt"]), "remind_at": parse_time(payload["remindAt"]),
                  "repeat_type": payload.get("repeatType", "none"), "status": payload.get("status", "active"), "updated_at": now}
        exists = conn.execute(text("SELECT id FROM schedules WHERE id = :id"), {"id": schedule_id}).scalar()
        if exists:
            conn.execute(text("""
                UPDATE schedules SET title=:title, description=:description, starts_at=:starts_at, remind_at=:remind_at,
                repeat_type=:repeat_type, status=:status, updated_at=:updated_at WHERE id=:id AND user_id=:user_id
            """), values)
        else:
            values["created_at"] = now
            conn.execute(text("""
                INSERT INTO schedules (id,user_id,title,description,starts_at,remind_at,repeat_type,status,created_at,updated_at)
                VALUES (:id,:user_id,:title,:description,:starts_at,:remind_at,:repeat_type,:status,:created_at,:updated_at)
            """), values)
        return db.row_json(conn.execute(text("SELECT * FROM schedules WHERE id = :id"), {"id": schedule_id}).mappings().one())


def schedule_update_status(payload: dict[str, Any], *, status: str) -> dict[str, Any]:
    db.seed_defaults()
    schedule_id = uuid.UUID(payload["id"])
    now = db.utc_now()
    with db.session() as conn:
        user_id, _ = db.get_identity(conn)
        result = conn.execute(text("""
            UPDATE schedules SET status=:status, updated_at=:now, reminded_at=CASE WHEN :status='completed' THEN :now ELSE reminded_at END
            WHERE id=:id AND user_id=:user_id
        """), {"status": status, "now": now, "id": schedule_id, "user_id": user_id})
        if result.rowcount == 0:
            raise ValueError("schedule not found")
        return db.row_json(conn.execute(text("SELECT * FROM schedules WHERE id=:id"), {"id": schedule_id}).mappings().one())


def schedule_snooze(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    schedule_id = uuid.UUID(payload["id"])
    minutes = min(max(int(payload.get("minutes", 10)), 1), 1440)
    now = db.utc_now()
    with db.session() as conn:
        user_id, _ = db.get_identity(conn)
        result = conn.execute(text("""
            UPDATE schedules SET remind_at=remind_at + (:minutes * INTERVAL '1 minute'), status='active', updated_at=:now
            WHERE id=:id AND user_id=:user_id
        """), {"minutes": minutes, "now": now, "id": schedule_id, "user_id": user_id})
        if result.rowcount == 0:
            raise ValueError("schedule not found")
        return db.row_json(conn.execute(text("SELECT * FROM schedules WHERE id=:id"), {"id": schedule_id}).mappings().one())


def game_save(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    now = db.utc_now()
    game_type = payload.get("gameType", "yahtzee")
    status = payload.get("status", "playing")
    result = payload.get("result")
    started_at = parse_time(payload.get("startedAt")) or now
    ended_at = parse_time(payload.get("endedAt"))
    if game_type != "yahtzee":
        raise ValueError("only yahtzee is supported in the MVP")
    if status not in {"playing", "completed", "abandoned"}:
        raise ValueError("invalid game status")
    if status in {"completed", "abandoned"} and ended_at is None:
        raise ValueError("ended games require endedAt")
    if status == "completed" and not isinstance(result, dict):
        raise ValueError("completed games require a result object")
    if status == "playing" and ended_at is not None:
        raise ValueError("playing games cannot have endedAt")
    with db.session() as conn:
        user_id, pet_id = db.get_identity(conn)
        game_id = uuid.UUID(payload["id"]) if payload.get("id") else uuid.uuid4()
        values = {"id": game_id, "user_id": user_id, "pet_id": pet_id, "game_type": game_type,
                  "schema_version": int(payload.get("schemaVersion", 1)), "status": status,
                  "state": db.as_json(payload.get("state", {})), "result": db.as_json(result) if result is not None else None,
                  "started_at": started_at, "updated_at": now, "ended_at": ended_at}
        exists = conn.execute(text("SELECT id FROM game_sessions WHERE id=:id"), {"id": game_id}).scalar()
        if exists:
            conn.execute(text("""
                UPDATE game_sessions SET status=:status, state=CAST(:state AS jsonb), result=CAST(:result AS jsonb),
                updated_at=:updated_at, ended_at=:ended_at WHERE id=:id
            """), values)
        else:
            conn.execute(text("""
                INSERT INTO game_sessions (id,user_id,pet_id,game_type,schema_version,status,state,result,started_at,updated_at,ended_at)
                VALUES (:id,:user_id,:pet_id,:game_type,:schema_version,:status,CAST(:state AS jsonb),CAST(:result AS jsonb),:started_at,:updated_at,:ended_at)
            """), values)
        return db.row_json(conn.execute(text("SELECT * FROM game_sessions WHERE id=:id"), {"id": game_id}).mappings().one())


def farm_perform_action(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    action = payload.get("action")
    if action not in {"water", "plant", "harvest", "rest"}:
        raise ValueError("unsupported farm action")
    now = db.utc_now()
    with db.session() as conn:
        user_id, pet_id = db.get_identity(conn)
        row = conn.execute(text("""
            SELECT id, revision, data FROM state_documents WHERE pet_id=:pet_id AND domain='farm' FOR UPDATE
        """), {"pet_id": pet_id}).mappings().one()
        data = dict(row["data"])
        data["currentActivity"] = {"water": "watering", "plant": "planting", "harvest": "harvesting", "rest": "resting"}[action]
        data["lastAction"] = action
        data["lastTickAt"] = now.isoformat()
        revision = int(row["revision"]) + 1
        conn.execute(text("""
            UPDATE state_documents SET data=CAST(:data AS jsonb), revision=:revision, updated_at=:now WHERE id=:id
        """), {"data": db.as_json(data), "revision": revision, "now": now, "id": row["id"]})
        event_payload = db.as_json({"action": action, "revision": revision, "data": data})
        conn.execute(text("""
            INSERT INTO events (id,user_id,pet_id,event_type,source,payload,occurred_at,created_at)
            VALUES (:id,:user_id,:pet_id,'farm.action.completed','agent',CAST(:payload AS jsonb),:now,:now)
        """), {"id": uuid.uuid4(), "user_id": user_id, "pet_id": pet_id, "payload": event_payload, "now": now})
        return {"domain": "farm", "action": action, "status": "completed", "revision": revision, "data": data}


def sensor_query(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    sensor_type = payload.get("sensorType")
    limit = min(max(int(payload.get("limit", 10)), 1), 50)
    with db.session() as conn:
        params: dict[str, Any] = {"limit": limit}
        condition = "event_type='sensor.observation'"
        if sensor_type:
            condition += " AND payload->>'sensorType'=:sensor_type"
            params["sensor_type"] = sensor_type
        rows = conn.execute(text(f"SELECT payload FROM events WHERE {condition} ORDER BY occurred_at DESC, id DESC LIMIT :limit"), params).mappings().all()
        observations = [row["payload"] for row in rows]
        return {"observations": observations}


def conversation_append(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    now = db.utc_now()
    with db.session() as conn:
        user_id, pet_id = db.get_identity(conn)
        conversation_id = uuid.UUID(payload["conversationId"]) if payload.get("conversationId") else uuid.uuid4()
        exists = conn.execute(text("SELECT id FROM conversations WHERE id=:id AND user_id=:user_id"),
                              {"id": conversation_id, "user_id": user_id}).scalar()
        if not exists:
            conn.execute(text("""
                INSERT INTO conversations (id,user_id,pet_id,channel,message_count,started_at)
                VALUES (:id,:user_id,:pet_id,:channel,0,:now)
            """), {"id": conversation_id, "user_id": user_id, "pet_id": pet_id, "channel": payload.get("channel", "unity_text"), "now": now})
        message_id = uuid.uuid4()
        conn.execute(text("""
            INSERT INTO messages (id,conversation_id,role,content,created_at,expires_at)
            VALUES (:id,:conversation_id,:role,:content,:now,:expires_at)
        """), {"id": message_id, "conversation_id": conversation_id, "role": payload["role"], "content": payload["content"],
                "now": now, "expires_at": now + timedelta(days=7)})
        conn.execute(text("UPDATE conversations SET message_count = message_count + 1 WHERE id=:id"), {"id": conversation_id})
        memory_job_id: uuid.UUID | None = None
        if payload.get("role") == "assistant" and bool(payload.get("memoryEligible", False)):
            user_message_id = conn.execute(text("""
                SELECT id FROM messages
                WHERE conversation_id=:conversation_id AND role='user' AND id<>:assistant_id
                ORDER BY created_at DESC LIMIT 1
            """), {"conversation_id": conversation_id, "assistant_id": message_id}).scalar()
            if user_message_id:
                event_id = uuid.uuid4()
                memory_job_id = uuid.uuid4()
                event_payload = db.as_json({
                    "userMessageId": str(user_message_id),
                    "assistantMessageId": str(message_id),
                    "conversationId": str(conversation_id),
                })
                conn.execute(text("""
                    INSERT INTO events (id,user_id,pet_id,event_type,source,payload,occurred_at,created_at)
                    VALUES (:id,:user_id,:pet_id,'conversation.completed','agent',CAST(:payload AS jsonb),:now,:now)
                """), {"id": event_id, "user_id": user_id, "pet_id": pet_id, "payload": event_payload, "now": now})
                conn.execute(text("""
                    INSERT INTO memory_jobs (id,source_event_id,status,attempts,next_retry_at,last_error,created_at)
                    VALUES (:id,:event_id,'pending',0,:now,NULL,:now)
                """), {"id": memory_job_id, "event_id": event_id, "now": now})
        result = {
            "conversationId": str(conversation_id),
            "messageId": str(message_id),
            "expiresAt": (now + timedelta(days=7)).isoformat(),
            "memoryEligible": bool(payload.get("memoryEligible", False)),
        }
        if memory_job_id:
            result["memoryJobId"] = str(memory_job_id)
        return result


def conversation_get(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    conversation_id = uuid.UUID(payload["conversationId"])
    limit = min(max(int(payload.get("limit", 12)), 1), 50)
    now = db.utc_now()
    with db.session() as conn:
        user_id, _ = db.get_identity(conn)
        conversation = conn.execute(text("""
            SELECT id, channel, started_at, ended_at
            FROM conversations WHERE id=:id AND user_id=:user_id
        """), {"id": conversation_id, "user_id": user_id}).mappings().one_or_none()
        if conversation is None:
            raise ValueError("conversation not found")
        messages = conn.execute(text("""
            SELECT id, role, content, created_at, expires_at
            FROM (
                SELECT id, role, content, created_at, expires_at
                FROM messages
                WHERE conversation_id=:conversation_id AND expires_at > :now
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
            ) recent
            ORDER BY created_at ASC, id ASC
        """), {"conversation_id": conversation_id, "now": now, "limit": limit}).mappings().all()
        return {
            "conversationId": str(conversation["id"]),
            "userId": str(user_id),
            "channel": conversation["channel"],
            "messages": [db.row_json(row) for row in messages],
        }


def proactive_tick(_: dict[str, Any]) -> dict[str, Any]:
    reminders = scan_due_schedules()
    changed = advance_farm()
    return {"reminders": reminders, "farmChanged": changed}


def append_event(payload: dict[str, Any], *, event_type: str, source: str, value: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    now = db.utc_now()
    with db.session() as conn:
        user_id, pet_id = db.get_identity(conn)
        event_id = uuid.UUID(str(value.get("eventId") or value.get("actionId") or value.get("observationId") or uuid.uuid4()))
        conn.execute(text("""
            INSERT INTO events (id,user_id,pet_id,event_type,source,payload,occurred_at,created_at)
            VALUES (:id,:user_id,:pet_id,:event_type,:source,CAST(:payload AS jsonb),:occurred_at,:created_at)
            ON CONFLICT (id) DO NOTHING
        """), {"id": event_id, "user_id": user_id, "pet_id": pet_id, "event_type": event_type,
                "source": source, "payload": db.as_json(value), "occurred_at": now, "created_at": now})
        return {"eventId": str(event_id), "eventType": event_type, "status": "recorded", "payload": value}


def experience_event_append(payload: dict[str, Any]) -> dict[str, Any]:
    event = validate_experience_event(payload["event"] if isinstance(payload.get("event"), dict) else payload)
    return append_event(payload, event_type="experience.event", source="agent", value=event)


def action_result_append(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_action_result(payload["result"] if isinstance(payload.get("result"), dict) else payload)
    source = "unity" if result["deviceId"].startswith("mock-unity") or result["deviceId"].startswith("unity") else "stackchan"
    return append_event(payload, event_type="action.result", source=source, value=result)


def sensor_observation_append(payload: dict[str, Any]) -> dict[str, Any]:
    observation = validate_sensor_observation(payload["observation"] if isinstance(payload.get("observation"), dict) else payload)
    return append_event(payload, event_type="sensor.observation", source="unity", value=observation)


def robot_action_request(payload: dict[str, Any]) -> dict[str, Any]:
    now = db.utc_now()
    action = {
        "actionId": str(uuid.uuid4()), "deviceId": str(payload.get("deviceId", "mock-robot")),
        "actionType": str(payload.get("actionType", "nod")), "status": "accepted",
        "startedAt": now.isoformat(), "completedAt": None,
        "requestedParameters": payload.get("parameters") or {}, "measuredResult": {"simulated": True},
        "error": None, "sourceEventId": payload.get("sourceEventId"),
    }
    validate_action_result(action)
    return action


def memory_job_recover(_: dict[str, Any]) -> dict[str, Any]:
    now = db.utc_now()
    with db.session() as conn:
        result = conn.execute(text("""
            UPDATE memory_jobs
            SET status='pending', next_retry_at=:now, last_error='worker lease expired'
            WHERE status='processing' AND next_retry_at IS NOT NULL AND next_retry_at < :now
        """), {"now": now})
        return {"recovered": result.rowcount}


def memory_job_claim(_: dict[str, Any]) -> dict[str, Any] | None:
    now = db.utc_now()
    lease_until = now + timedelta(seconds=MEMORY_JOB_LEASE_SECONDS)
    with db.session() as conn:
        row = conn.execute(text("""
            SELECT mj.id, mj.attempts, mj.source_event_id, e.user_id, e.pet_id, e.payload
            FROM memory_jobs mj JOIN events e ON e.id=mj.source_event_id
            WHERE (mj.status='pending' OR (mj.status='failed' AND mj.next_retry_at <= :now))
              AND (mj.next_retry_at IS NULL OR mj.next_retry_at <= :now)
            ORDER BY mj.created_at ASC
            FOR UPDATE SKIP LOCKED LIMIT 1
        """), {"now": now}).mappings().one_or_none()
        if row is None:
            return None
        conn.execute(text("""
            UPDATE memory_jobs SET status='processing', attempts=attempts+1, next_retry_at=:lease_until
            WHERE id=:id
        """), {"id": row["id"], "lease_until": lease_until})
        payload = row["payload"] or {}
        user_message_id = uuid.UUID(payload["userMessageId"])
        assistant_message_id = uuid.UUID(payload["assistantMessageId"])
        messages = conn.execute(text("""
            SELECT id, role, content, created_at
            FROM messages WHERE id IN (:user_message_id, :assistant_message_id)
            ORDER BY created_at ASC
        """), {"user_message_id": user_message_id, "assistant_message_id": assistant_message_id}).mappings().all()
        return {
            "jobId": str(row["id"]),
            "attempts": int(row["attempts"]) + 1,
            "userId": str(row["user_id"]),
            "eventId": str(row["source_event_id"]),
            "conversationId": payload.get("conversationId"),
            "messages": [db.row_json(item) for item in messages],
        }


def memory_job_complete(payload: dict[str, Any]) -> dict[str, Any]:
    job_id = uuid.UUID(payload["jobId"])
    refs = payload.get("refs") or []
    now = db.utc_now()
    with db.session() as conn:
        row = conn.execute(text("""
            SELECT mj.status, e.user_id FROM memory_jobs mj JOIN events e ON e.id=mj.source_event_id
            WHERE mj.id=:id FOR UPDATE
        """), {"id": job_id}).mappings().one()
        if row["status"] == "completed":
            return {"jobId": str(job_id), "status": "completed", "refCount": 0}
        for ref in refs:
            memory_id = str(ref.get("memoryId", "")).strip()
            if not memory_id:
                continue
            bucket = ref.get("memoryBucket", "profile")
            if bucket not in {"profile", "preference", "habit", "relationship", "goal", "milestone"}:
                bucket = "profile"
            conn.execute(text("""
                INSERT INTO memory_refs (id,memory_job_id,user_id,mem0_memory_id,memory_bucket,created_at)
                VALUES (:id,:job_id,:user_id,:memory_id,:bucket,:now)
                ON CONFLICT (mem0_memory_id) DO NOTHING
            """), {"id": uuid.uuid4(), "job_id": job_id, "user_id": row["user_id"],
                  "memory_id": memory_id, "bucket": bucket, "now": now})
        conn.execute(text("""
            UPDATE memory_jobs SET status='completed', completed_at=:now, next_retry_at=NULL, last_error=NULL WHERE id=:id
        """), {"id": job_id, "now": now})
        count = conn.execute(text("SELECT count(*) FROM memory_refs WHERE memory_job_id=:id"), {"id": job_id}).scalar_one()
        return {"jobId": str(job_id), "status": "completed", "refCount": int(count)}


def memory_job_fail(payload: dict[str, Any]) -> dict[str, Any]:
    job_id = uuid.UUID(payload["jobId"])
    error = " ".join(str(payload.get("error", "memory provider failed")).split())
    error = re.sub(r"(?:sk|pk)-[A-Za-z0-9_-]{12,}", "[redacted]", error, flags=re.IGNORECASE)
    error = re.sub(r"(?i)(api[_ -]?key|token|password)\s*[:=]\s*\S+", r"\1=[redacted]", error)
    error = error[:500]
    now = db.utc_now()
    with db.session() as conn:
        row = conn.execute(text("SELECT attempts FROM memory_jobs WHERE id=:id FOR UPDATE"), {"id": job_id}).mappings().one()
        attempts = int(row["attempts"])
        retry_at = None if attempts >= MEMORY_MAX_ATTEMPTS else now + timedelta(seconds=MEMORY_RETRY_BASE_SECONDS * (2 ** max(attempts - 1, 0)))
        conn.execute(text("""
            UPDATE memory_jobs SET status='failed', next_retry_at=:retry_at, last_error=:error WHERE id=:id
        """), {"id": job_id, "retry_at": retry_at, "error": error})
        return {"jobId": str(job_id), "status": "failed", "attempts": attempts, "nextRetryAt": retry_at.isoformat() if retry_at else None}


def memory_job_ignore(payload: dict[str, Any]) -> dict[str, Any]:
    job_id = uuid.UUID(payload["jobId"])
    reason = " ".join(str(payload.get("reason", "ignored")).split())[:500]
    now = db.utc_now()
    with db.session() as conn:
        conn.execute(text("""
            UPDATE memory_jobs SET status='ignored', next_retry_at=NULL, completed_at=:now, last_error=:reason WHERE id=:id
        """), {"id": job_id, "now": now, "reason": reason})
        return {"jobId": str(job_id), "status": "ignored"}


async def dispatch(message: dict[str, Any]) -> dict[str, Any]:
    request_id = message.get("requestId")
    message_type = message.get("type")
    payload = message.get("payload") or {}
    if message_type == "ping":
        return response(request_id, "pong", "ok", {"serverTime": db.utc_now().isoformat()})
    if message_type == "bootstrap.get":
        await recalc_farm_and_broadcast()
        return response(request_id, "bootstrap.result", "ok", bootstrap())
    if message_type == "state.get":
        if payload.get("domain") == "farm":
            await recalc_farm_and_broadcast()
        return response(request_id, "state.get.result", "ok", state_get(payload))
    if message_type == "state.put":
        status, result = state_put(payload)
        return response(request_id, "state.put.result", status, result)
    if message_type == "schedule.upsert":
        return response(request_id, "schedule.upsert.result", "ok", schedule_upsert(payload))
    if message_type == "schedule.complete":
        return response(request_id, "schedule.complete.result", "ok", schedule_update_status(payload, status="completed"))
    if message_type == "schedule.snooze":
        return response(request_id, "schedule.snooze.result", "ok", schedule_snooze(payload))
    if message_type == "farm.perform_action":
        return response(request_id, "farm.perform_action.result", "ok", farm_perform_action(payload))
    if message_type == "sensor.latest":
        recent = sensor_query({"sensorType": payload.get("sensorType"), "limit": 1})
        return response(request_id, "sensor.latest.result", "ok", recent.get("observations", [{}])[0] if recent.get("observations") else {})
    if message_type == "sensor.query_recent":
        return response(request_id, "sensor.query_recent.result", "ok", sensor_query(payload))
    if message_type == "game.start":
        return response(request_id, "game.start.result", "ok", game_save({"gameType": "yahtzee", "status": "playing", "state": {}}))
    if message_type == "game-session.save":
        return response(request_id, "game-session.save.result", "ok", game_save(payload))
    if message_type == "conversation.append":
        return response(request_id, "conversation.append.result", "ok", conversation_append(payload))
    if message_type == "conversation.get":
        return response(request_id, "conversation.get.result", "ok", conversation_get(payload))
    if message_type == "proactive.tick":
        return response(request_id, "proactive.tick.result", "ok", proactive_tick(payload))
    if message_type == "experience.event.append":
        return response(request_id, "experience.event.append.result", "ok", experience_event_append(payload))
    if message_type == "action.result.append":
        return response(request_id, "action.result.append.result", "ok", action_result_append(payload))
    if message_type == "sensor.observation.append":
        return response(request_id, "sensor.observation.append.result", "ok", sensor_observation_append(payload))
    if message_type == "robot.action.request":
        return response(request_id, "robot.action.request.result", "ok", robot_action_request(payload))
    if message_type == "memory-job.recover":
        return response(request_id, "memory-job.recover.result", "ok", memory_job_recover(payload))
    if message_type == "memory-job.claim":
        return response(request_id, "memory-job.claim.result", "ok", memory_job_claim(payload) or {})
    if message_type == "memory-job.complete":
        return response(request_id, "memory-job.complete.result", "ok", memory_job_complete(payload))
    if message_type == "memory-job.fail":
        return response(request_id, "memory-job.fail.result", "ok", memory_job_fail(payload))
    if message_type == "memory-job.ignore":
        return response(request_id, "memory-job.ignore.result", "ok", memory_job_ignore(payload))
    return response(request_id, f"{message_type or 'unknown'}.result", "error", {"code": "unsupported_message"})


async def service_loop() -> None:
    while True:
        await asyncio.sleep(FARM_TICK_SECONDS)
        await recalc_farm_and_broadcast()
        for reminder in scan_due_schedules():
            await connections.broadcast({"type": "schedule.reminder", "status": "ok", "payload": reminder})
        prune_expired_messages()


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.seed_defaults()
    task = asyncio.create_task(service_loop())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


app = FastAPI(title="AR-AIPet Data Service", version=PROTOCOL_VERSION, lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket) -> None:
    await connections.add(socket)
    try:
        while True:
            raw = await socket.receive_text()
            message = json.loads(raw)
            try:
                result = await dispatch(message)
            except Exception as exc:
                result = response(message.get("requestId"), "error", "error", {"code": "invalid_request", "message": str(exc)})
            await socket.send_json(result)
    except WebSocketDisconnect:
        connections.remove(socket)
    except Exception:
        connections.remove(socket)
