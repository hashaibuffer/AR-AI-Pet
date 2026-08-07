"""create the single-user MVP schema"""

from alembic import op

revision = "0001_mvp_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            display_name TEXT NOT NULL,
            timezone TEXT NOT NULL DEFAULT 'Asia/Shanghai',
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        CREATE TABLE pets (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            persona_version TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        CREATE TABLE state_documents (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            domain TEXT NOT NULL CHECK (domain IN ('pet', 'home', 'farm')),
            schema_version INTEGER NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            data JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            UNIQUE (pet_id, domain)
        );
        CREATE INDEX idx_state_documents_user_domain ON state_documents (user_id, domain);
        CREATE TABLE schedules (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            starts_at TIMESTAMPTZ NOT NULL,
            remind_at TIMESTAMPTZ NOT NULL,
            repeat_type TEXT NOT NULL CHECK (repeat_type IN ('none', 'daily', 'weekly')),
            status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'cancelled')),
            reminded_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX idx_schedules_user_starts ON schedules (user_id, starts_at);
        CREATE INDEX idx_schedules_active_remind ON schedules (remind_at) WHERE status = 'active';
        CREATE TABLE game_sessions (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            game_type TEXT NOT NULL CHECK (game_type = 'yahtzee'),
            schema_version INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('playing', 'completed', 'abandoned')),
            state JSONB NOT NULL,
            result JSONB,
            started_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            ended_at TIMESTAMPTZ
        );
        CREATE INDEX idx_games_pet_status ON game_sessions (pet_id, status, updated_at DESC);
        CREATE INDEX idx_games_user_started ON game_sessions (user_id, started_at DESC);
        CREATE TABLE conversations (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            channel TEXT NOT NULL CHECK (channel IN ('unity_text', 'unity_voice', 'stackchan')),
            message_count INTEGER NOT NULL DEFAULT 0,
            started_at TIMESTAMPTZ NOT NULL,
            ended_at TIMESTAMPTZ
        );
        CREATE TABLE messages (
            id UUID PRIMARY KEY,
            conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX idx_messages_conversation_created ON messages (conversation_id, created_at);
        CREATE INDEX idx_messages_expires ON messages (expires_at);
        CREATE TABLE events (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            event_type TEXT NOT NULL,
            source TEXT NOT NULL CHECK (source IN ('unity', 'agent', 'stackchan', 'system')),
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            occurred_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX idx_events_pet_occurred ON events (pet_id, occurred_at DESC);
        CREATE INDEX idx_events_type_occurred ON events (event_type, occurred_at DESC);
        CREATE TABLE memory_jobs (
            id UUID PRIMARY KEY,
            source_event_id UUID NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
            status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'ignored')),
            attempts INTEGER NOT NULL DEFAULT 0,
            next_retry_at TIMESTAMPTZ,
            last_error TEXT,
            created_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ
        );
        CREATE INDEX idx_memory_jobs_pending ON memory_jobs (next_retry_at) WHERE status IN ('pending', 'failed');
        CREATE TABLE memory_refs (
            id UUID PRIMARY KEY,
            memory_job_id UUID NOT NULL REFERENCES memory_jobs(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            mem0_memory_id TEXT NOT NULL UNIQUE,
            memory_bucket TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );
    """)


def downgrade() -> None:
    for table in ("memory_refs", "memory_jobs", "events", "messages", "conversations", "game_sessions", "schedules", "state_documents", "pets", "users"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
