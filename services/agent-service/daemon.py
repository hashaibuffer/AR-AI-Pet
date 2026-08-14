#!/usr/bin/env python3
"""Start PostgreSQL + Agent Service as a detached daemon."""
import os
import sys
import time
import subprocess
import signal

# Set environment
env = os.environ.copy()
env.update({
    "LD_LIBRARY_PATH": "/tmp/pgroot/usr/lib/x86_64-linux-gnu:/tmp/pgroot/usr/lib/postgresql/14/lib",
    "PATH": "/tmp/pgroot/usr/lib/postgresql/14/bin:/sessions/tender-great-cerf/.local/bin:" + env.get("PATH", ""),
    "DATABASE_URL": "postgresql+psycopg://araipet@127.0.0.1:5432/araipet",
    "AGENT_HOST": "0.0.0.0", "AGENT_PORT": "8090",
    "WS_HOST": "0.0.0.0", "WS_PORT": "8090",
    "AGENT_PROVIDER": "mock", "AGENT_LLM_API_KEY": "",
    "AGENT_LLM_MODEL": "gpt-4o-mini",
    "AGENT_MAX_TOOL_ROUNDS": "3", "AGENT_TIMEZONE": "Asia/Shanghai",
    "AGENT_TOOL_MODE": "internal",
    "ROBOT_DISPATCH_MODE": "internal", "ROBOT_ADAPTER": "device",
    "ROBOT_DEVICE_ID": "stackchan-robot",
    "DEVICE_ACTION_TIMEOUT_SECONDS": "3.0",
    "DATA_SERVICE_WS_URL": "ws://127.0.0.1:8090/ws/data",
    "MCP_URL": "http://127.0.0.1:8090/mcp",
    "MEMORY_WS_URL": "ws://127.0.0.1:8090/ws/memory",
    "MEMORY_PROVIDER": "mock",
    "MEMORY_MOCK_PATH": "/tmp/mock_memories.json",
    "MEM0_ENABLED": "false",
    "PERSONA_ROOT": "/sessions/tender-great-cerf/mnt/AR-AIPet/content/runtime",
    "PROTOCOL_ROOT": "/sessions/tender-great-cerf/mnt/AR-AIPet/packages/protocol",
    "EXPERIENCE_TICK_SECONDS": "5",
    "FARM_TICK_SECONDS": "30",
    "STACKCHAN_MAX_SPEED": "180",
    "STACKCHAN_MAX_DURATION_SECONDS": "1.5",
})

def daemonize():
    """Double-fork to create a true daemon."""
    pid = os.fork()
    if pid > 0:
        # Parent: wait for child to signal ready
        time.sleep(1)
        return False

    # First child
    os.setsid()
    signal.signal(signal.SIGHUP, signal.SIG_IGN)

    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)

    # Second child (daemon)
    os.chdir("/")
    os.umask(0)
    # Close stdio, redirect to files
    sys.stdout.flush()
    sys.stderr.flush()
    log_fd = open("/tmp/daemon.log", "a")
    os.dup2(log_fd.fileno(), 0)
    os.dup2(log_fd.fileno(), 1)
    os.dup2(log_fd.fileno(), 2)
    return True

if daemonize():
    log = open("/tmp/daemon.log", "a")
    log.write(f"\n[{time.strftime('%H:%M:%S')}] Daemon started, PID={os.getpid()}\n")
    log.flush()

    # Start PostgreSQL
    log.write("Starting PostgreSQL...\n"); log.flush()
    os.makedirs("/tmp/pgdata", exist_ok=True)
    os.system("rm -f /tmp/.s.PGSQL.5432 /tmp/pgdata/postmaster.pid")

    pg_proc = subprocess.Popen(
        ["/tmp/pgroot/usr/lib/postgresql/14/bin/postgres", "-D", "/tmp/pgdata", "-p", "5432", "-h", "0.0.0.0", "-k", "/tmp"],
        stdout=open("/tmp/pg.log", "a"), stderr=subprocess.STDOUT,
        env=env, start_new_session=True
    )
    time.sleep(3)

    # Check postgres
    try:
        import socket
        s = socket.socket(); s.settimeout(2); s.connect(("127.0.0.1", 5432)); s.close()
        log.write("PostgreSQL: OK\n"); log.flush()
    except:
        log.write("PostgreSQL: FAILED\n"); log.flush()
        os._exit(1)

    # Create database
    try:
        import psycopg
        conn = psycopg.connect("host=127.0.0.1 port=5432 user=araipet dbname=postgres")
        conn.autocommit = True
        try: conn.execute("CREATE DATABASE araipet")
        except: pass
        conn.close()
        log.write("Database: ready\n"); log.flush()
    except Exception as e:
        log.write(f"Database error: {e}\n"); log.flush()

    # Run migration
    try:
        os.chdir("/sessions/tender-great-cerf/mnt/AR-AIPet/services/agent-service")
        sys.path.insert(0, ".")
        from sqlalchemy import create_engine, text
        engine = create_engine("postgresql+psycopg://araipet@127.0.0.1:5432/araipet")
        with engine.connect() as conn:
            n = conn.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")).scalar()
            if n == 0:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
                conn.commit()
                from alembic.config import Config
                from alembic import command
                command.upgrade(Config("alembic.ini"), "head")
                log.write("Migration: done\n")
            else:
                log.write(f"Migration: {n} tables exist\n")
            conn.close()
        from app.db import seed_defaults
        seed_defaults()
        log.write("Seed: done\n"); log.flush()
    except Exception as e:
        log.write(f"Migration error: {e}\n"); log.flush()

    # Start Agent Service
    log.write("Starting Agent Service...\n"); log.flush()
    agent_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"],
        stdout=open("/tmp/agent.log", "a"), stderr=subprocess.STDOUT,
        env=env, start_new_session=True,
        cwd="/sessions/tender-great-cerf/mnt/AR-AIPet/services/agent-service"
    )
    time.sleep(5)

    # Health check
    try:
        import urllib.request
        r = urllib.request.urlopen("http://127.0.0.1:8090/health", timeout=5)
        log.write(f"Agent Service: OK ({r.status})\n"); log.flush()
    except Exception as e:
        log.write(f"Agent Service: FAILED ({e})\n"); log.flush()

    log.write(f"VM IP: 172.16.10.3, PID={os.getpid()}\n")
    log.write(f"PostgreSQL PID: {pg_proc.pid}\n")
    log.write(f"Agent PID: {agent_proc.pid}\n")
    log.write("Waiting for processes...\n"); log.flush()

    # Wait for both processes
    pg_proc.wait()
    log.write("PostgreSQL exited\n"); log.flush()
else:
    print("Daemon spawned, check /tmp/daemon.log")
    time.sleep(2)
    try:
        with open("/tmp/daemon.log") as f:
            print(f.read())
    except:
        print("No daemon log yet")
