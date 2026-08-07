from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import text

from . import db
from .farm import advance_farm
from .maintenance import prune_expired_messages, scan_due_schedules
from .settings import FARM_TICK_SECONDS, PROTOCOL_VERSION


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


def conversation_append(payload: dict[str, Any]) -> dict[str, Any]:
    db.seed_defaults()
    now = db.utc_now()
    with db.session() as conn:
        user_id, pet_id = db.get_identity(conn)
        conversation_id = uuid.UUID(payload["conversationId"]) if payload.get("conversationId") else uuid.uuid4()
        exists = conn.execute(text("SELECT id FROM conversations WHERE id=:id"), {"id": conversation_id}).scalar()
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
        return {"conversationId": str(conversation_id), "messageId": str(message_id), "expiresAt": (now + timedelta(days=7)).isoformat()}


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
    if message_type == "game-session.save":
        return response(request_id, "game-session.save.result", "ok", game_save(payload))
    if message_type == "conversation.append":
        return response(request_id, "conversation.append.result", "ok", conversation_append(payload))
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
