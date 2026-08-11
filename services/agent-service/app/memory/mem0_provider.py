from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

from .provider import MemoryProviderError


class Mem0Provider:
    name = "mem0"

    def __init__(
        self,
        *,
        qdrant_url: str,
        collection: str,
        history_db_path: str,
        llm_provider: str,
        llm_base_url: str,
        llm_api_key: str,
        llm_model: str,
        embedder_provider: str,
        embedder_base_url: str,
        embedder_api_key: str,
        embedder_model: str,
        embedding_dims: int,
    ) -> None:
        try:
            from mem0 import Memory
        except Exception as exc:
            raise MemoryProviderError("mem0ai import failed") from exc
        parsed = urlparse(qdrant_url)
        if not parsed.hostname:
            raise MemoryProviderError("invalid MEM0_QDRANT_URL")
        qdrant_config: dict[str, Any] = {
            "host": parsed.hostname,
            "port": parsed.port or (443 if parsed.scheme == "https" else 6333),
            "https": parsed.scheme == "https",
            "collection_name": collection,
            "embedding_model_dims": embedding_dims,
        }
        self.memory = Memory.from_config({
            "vector_store": {"provider": "qdrant", "config": qdrant_config},
            "llm": {"provider": llm_provider, "config": self._model_config(llm_provider, llm_base_url, llm_api_key, llm_model)},
            "embedder": {"provider": embedder_provider, "config": self._embedder_config(embedder_provider, embedder_base_url, embedder_api_key, embedder_model, embedding_dims)},
            "history_db_path": history_db_path,
        })

    @staticmethod
    def _model_config(provider: str, base_url: str, api_key: str, model: str) -> dict[str, Any]:
        config: dict[str, Any] = {"model": model, "api_key": api_key}
        if provider in {"openai", "deepseek"}:
            config["openai_base_url"] = base_url
        elif provider == "lmstudio":
            config["lmstudio_base_url"] = base_url
        elif provider == "ollama":
            config["ollama_base_url"] = base_url
        return config

    @staticmethod
    def _embedder_config(provider: str, base_url: str, api_key: str, model: str, dims: int) -> dict[str, Any]:
        config: dict[str, Any] = {"model": model, "api_key": api_key, "embedding_dims": dims}
        if provider == "openai":
            config["openai_base_url"] = base_url
        elif provider == "lmstudio":
            config["lmstudio_base_url"] = base_url
        elif provider == "ollama":
            config["ollama_base_url"] = base_url
        return config

    @staticmethod
    def _normalize(item: dict[str, Any]) -> dict[str, Any]:
        metadata = item.get("metadata") or {}
        return {
            "memoryId": str(item.get("id", "")),
            "text": str(item.get("memory", item.get("text", ""))),
            "score": float(item["score"]) if item.get("score") is not None else None,
            "metadata": metadata if isinstance(metadata, dict) else {},
        }

    async def add(self, *, user_id: str, messages: list[dict[str, Any]], metadata: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            result = await asyncio.to_thread(self.memory.add, messages, user_id=user_id, metadata=metadata, infer=True)
            values = result.get("results", []) if isinstance(result, dict) else result
            return [self._normalize(item) for item in (values or []) if isinstance(item, dict) and item.get("id")]
        except Exception as exc:
            raise MemoryProviderError("mem0 add failed") from exc

    async def search(self, *, user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        try:
            result = await asyncio.to_thread(self.memory.search, query, filters={"user_id": user_id}, top_k=limit)
            values = result.get("results", []) if isinstance(result, dict) else result
            return [self._normalize(item) for item in (values or []) if isinstance(item, dict) and item.get("id")]
        except Exception as exc:
            raise MemoryProviderError("mem0 search failed") from exc

    async def health(self) -> dict[str, Any]:
        return {"status": "ok", "provider": self.name}


class UnavailableMemoryProvider:
    name = "unavailable"

    def __init__(self, reason: str) -> None:
        self.reason = reason[:200]

    async def add(self, **_: Any) -> list[dict[str, Any]]:
        raise MemoryProviderError("memory provider unavailable")

    async def search(self, **_: Any) -> list[dict[str, Any]]:
        raise MemoryProviderError("memory provider unavailable")

    async def health(self) -> dict[str, Any]:
        return {"status": "degraded", "provider": self.name}
