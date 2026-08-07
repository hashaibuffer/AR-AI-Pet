from __future__ import annotations

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://araipet:araipet@localhost:5432/araipet")
WS_HOST = os.getenv("WS_HOST", "0.0.0.0")
WS_PORT = int(os.getenv("WS_PORT", "8080"))
FARM_TICK_SECONDS = int(os.getenv("FARM_TICK_SECONDS", "30"))
PROTOCOL_VERSION = "0.1"
