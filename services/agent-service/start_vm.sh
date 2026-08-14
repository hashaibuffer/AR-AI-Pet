#!/bin/bash
export LD_LIBRARY_PATH=/tmp/pgroot/usr/lib/x86_64-linux-gnu:/tmp/pgroot/usr/lib/postgresql/14/lib
export PATH=/tmp/pgroot/usr/lib/postgresql/14/bin:$PATH
export DATABASE_URL="postgresql+psycopg://araipet@127.0.0.1:5432/araipet"
export AGENT_HOST=0.0.0.0
export AGENT_PORT=8090
export WS_HOST=0.0.0.0
export WS_PORT=8090
export AGENT_PROVIDER=mock
export AGENT_LLM_API_KEY=""
export AGENT_LLM_MODEL=gpt-4o-mini
export AGENT_MAX_TOOL_ROUNDS=3
export AGENT_TIMEZONE=Asia/Shanghai
export AGENT_TOOL_MODE=internal
export ROBOT_DISPATCH_MODE=internal
export ROBOT_ADAPTER=device
export ROBOT_DEVICE_ID=stackchan-robot
export DEVICE_ACTION_TIMEOUT_SECONDS=3.0
export DATA_SERVICE_WS_URL="ws://127.0.0.1:8090/ws/data"
export MCP_URL="http://127.0.0.1:8090/mcp"
export MEMORY_WS_URL="ws://127.0.0.1:8090/ws/memory"
export MEMORY_PROVIDER=mock
export MEMORY_MOCK_PATH="/tmp/mock_memories.json"
export MEM0_ENABLED=false
export PERSONA_ROOT="/sessions/tender-great-cerf/mnt/AR-AIPet/content/runtime"
export PROTOCOL_ROOT="/sessions/tender-great-cerf/mnt/AR-AIPet/packages/protocol"
export EXPERIENCE_TICK_SECONDS=5
export FARM_TICK_SECONDS=30
export STACKCHAN_MAX_SPEED=180
export STACKCHAN_MAX_DURATION_SECONDS=1.5

cd /sessions/tender-great-cerf/mnt/AR-AIPet/services/agent-service

echo "=== 1. Start PostgreSQL ==="
rm -f /tmp/.s.PGSQL.5432 /tmp/pgdata/postmaster.pid
postgres -D /tmp/pgdata -p 5432 -h 0.0.0.0 -k /tmp > /tmp/pg.log 2>&1 &
PG_PID=$!
sleep 3
python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',5432)); print('PostgreSQL: OK'); s.close()" || { echo "PostgreSQL FAILED"; exit 1; }

echo "=== 2. Create database ==="
python3 -c "
import psycopg
conn = psycopg.connect('host=127.0.0.1 port=5432 user=araipet dbname=postgres')
conn.autocommit = True
try:
    conn.execute('CREATE DATABASE araipet')
    print('Database created')
except:
    print('Database already exists')
conn.close()
"

echo "=== 3. Install Python deps ==="
pip3 install --break-system-packages -q fastapi uvicorn[standard] websockets jsonschema sqlalchemy psycopg[binary] mem0ai fastmcp httpx alembic 2>&1 | tail -3

echo "=== 4. Run migration ==="
python3 -c "
import sys; sys.path.insert(0, '.')
from app.db import engine, seed_defaults
from sqlalchemy import text
with engine.connect() as conn:
    # Check if tables exist
    result = conn.execute(text(\"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'\")).scalar()
    if result == 0:
        print('Creating extension...')
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS pgcrypto'))
        conn.commit()
        print('Running migration...')
        import subprocess
        subprocess.run(['alembic', 'upgrade', 'head'], check=True)
    else:
        print(f'Tables already exist ({result} tables)')
        conn.close()

print('Seeding defaults...')
seed_defaults()
print('Database ready')
"

echo "=== 5. Start Agent Service (unified) ==="
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8090
