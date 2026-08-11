from __future__ import annotations

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://araipet:araipet@localhost:5432/araipet")
WS_HOST = os.getenv("WS_HOST", "0.0.0.0")
WS_PORT = int(os.getenv("WS_PORT", "8080"))
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8081"))
DATA_SERVICE_WS_URL = os.getenv("DATA_SERVICE_WS_URL", "ws://localhost:8080/ws")
DATA_SERVICE_TIMEOUT_SECONDS = float(os.getenv("DATA_SERVICE_TIMEOUT_SECONDS", "5"))
MCP_URL = os.getenv("MCP_URL", "http://localhost:8081/mcp")
AGENT_HOST = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8082"))
AGENT_PROVIDER = os.getenv("AGENT_PROVIDER", "openai")
AGENT_LLM_BASE_URL = os.getenv("AGENT_LLM_BASE_URL", "https://api.openai.com/v1")
AGENT_LLM_API_KEY = os.getenv("AGENT_LLM_API_KEY", "")
AGENT_LLM_MODEL = os.getenv("AGENT_LLM_MODEL", "gpt-4o-mini")
AGENT_LLM_TIMEOUT_SECONDS = float(os.getenv("AGENT_LLM_TIMEOUT_SECONDS", "30"))
AGENT_MAX_TOOL_ROUNDS = int(os.getenv("AGENT_MAX_TOOL_ROUNDS", "3"))
AGENT_TIMEZONE = os.getenv("AGENT_TIMEZONE", "Asia/Shanghai")
FARM_TICK_SECONDS = int(os.getenv("FARM_TICK_SECONDS", "30"))
PROTOCOL_VERSION = "0.1"
