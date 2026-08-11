from __future__ import annotations

from typing import Any, Protocol


class MemoryProviderError(RuntimeError):
    """Safe provider failure; callers must not expose provider internals."""


class MemoryProvider(Protocol):
    name: str

    async def add(
        self,
        *,
        user_id: str,
        messages: list[dict[str, Any]],
        metadata: dict[str, Any],
    ) -> list[dict[str, Any]]: ...

    async def search(self, *, user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]: ...

    async def health(self) -> dict[str, Any]: ...
