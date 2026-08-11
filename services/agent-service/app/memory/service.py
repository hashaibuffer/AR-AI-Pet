from __future__ import annotations

from typing import Any

from ..data_service_client import DataServiceClient
from ..settings import (
    MEM0_COLLECTION,
    MEM0_EMBEDDER_API_KEY,
    MEM0_EMBEDDER_BASE_URL,
    MEM0_EMBEDDER_MODEL,
    MEM0_EMBEDDING_DIMS,
    MEM0_ENABLED,
    MEM0_HISTORY_DB_PATH,
    MEM0_LLM_API_KEY,
    MEM0_LLM_BASE_URL,
    MEM0_LLM_MODEL,
    MEM0_LLM_PROVIDER,
    MEM0_QDRANT_URL,
    MEM0_EMBEDDER_PROVIDER,
    MEMORY_MOCK_PATH,
    MEMORY_PROVIDER,
)
from .mem0_provider import Mem0Provider, UnavailableMemoryProvider
from .mock_provider import MockMemoryProvider
from .provider import MemoryProvider, MemoryProviderError
from .worker import MemoryWorker


def create_provider() -> MemoryProvider:
    if MEMORY_PROVIDER == "mock" or not MEM0_ENABLED:
        return MockMemoryProvider(MEMORY_MOCK_PATH)
    if MEMORY_PROVIDER != "mem0":
        return UnavailableMemoryProvider("unsupported memory provider")
    try:
        return Mem0Provider(
            qdrant_url=MEM0_QDRANT_URL,
            collection=MEM0_COLLECTION,
            history_db_path=MEM0_HISTORY_DB_PATH,
            llm_provider=MEM0_LLM_PROVIDER,
            llm_base_url=MEM0_LLM_BASE_URL,
            llm_api_key=MEM0_LLM_API_KEY,
            llm_model=MEM0_LLM_MODEL,
            embedder_provider=MEM0_EMBEDDER_PROVIDER,
            embedder_base_url=MEM0_EMBEDDER_BASE_URL,
            embedder_api_key=MEM0_EMBEDDER_API_KEY,
            embedder_model=MEM0_EMBEDDER_MODEL,
            embedding_dims=MEM0_EMBEDDING_DIMS,
        )
    except Exception as exc:
        return UnavailableMemoryProvider(str(exc))


class MemoryService:
    def __init__(self, data_service: DataServiceClient, provider: MemoryProvider) -> None:
        self.data_service = data_service
        self.provider = provider
        self.worker = MemoryWorker(data_service, provider)

    async def health(self) -> dict[str, Any]:
        result = await self.provider.health()
        provider_status = result.get("status", "degraded")
        if provider_status not in {"ok", "degraded"}:
            provider_status = "degraded"
        return {
            "status": provider_status,
            "provider": result.get("provider", self.provider.name),
            "providerStatus": provider_status,
        }

    async def search(self, payload: dict[str, Any]) -> dict[str, Any]:
        user_id = str(payload.get("userId", "")).strip()
        query = str(payload.get("query", "")).strip()
        limit = max(1, min(int(payload.get("limit", 5)), 5))
        if not user_id or not query:
            raise ValueError("memory.search requires userId and query")
        try:
            memories = await self.provider.search(user_id=user_id, query=query, limit=limit)
        except MemoryProviderError:
            return {"status": "unavailable", "memories": []}
        return {"status": "ok", "memories": memories}
