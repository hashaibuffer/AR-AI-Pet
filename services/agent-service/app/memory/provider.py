from __future__ import annotations

from typing import Any


class MemoryProvider:
    """Reserved interface for the later self-hosted Mem0 worker."""

    async def add(self, *, user_id: str, messages: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
        raise RuntimeError("Mem0 is not enabled in this MVP slice")

    async def search(self, *, user_id: str, query: str) -> list[dict[str, Any]]:
        raise RuntimeError("Mem0 is not enabled in this MVP slice")
