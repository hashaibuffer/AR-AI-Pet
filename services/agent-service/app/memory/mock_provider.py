from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .provider import MemoryProviderError


class MockMemoryProvider:
    """Deterministic, file-backed provider for local architecture tests."""

    name = "mock"

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError) as exc:
            raise MemoryProviderError("mock memory store is unreadable") from exc

    def _write(self, data: list[dict[str, Any]]) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, self.path)

    @staticmethod
    def _extract(messages: list[dict[str, Any]], bucket: str) -> list[str]:
        user_text = "\n".join(str(item.get("content", "")) for item in messages if item.get("role") == "user")
        values: list[str] = []
        for pattern, prefix in ((r"(?<!不)(?:最)?喜欢([^，,。！？!?]+)", "用户喜欢"), (r"不喜欢([^，,。！？!?]+)", "用户不喜欢")):
            for match in re.finditer(pattern, user_text):
                value = match.group(1).strip()
                if value:
                    values.append(f"{prefix}{value}")
        if not values and bucket == "profile":
            match = re.search(r"(?:我是|我叫|来自)([^，,。！？!?]+)", user_text)
            if match:
                values.append(f"用户{match.group(0).strip()}")
        return list(dict.fromkeys(values))

    async def add(self, *, user_id: str, messages: list[dict[str, Any]], metadata: dict[str, Any]) -> list[dict[str, Any]]:
        bucket = metadata.get("memoryBucket", "profile")
        values = self._extract(messages, bucket)
        async with self._lock:
            data = self._read()
            existing = {(item.get("userId"), item.get("text")) for item in data}
            result: list[dict[str, Any]] = []
            for text in values:
                if (user_id, text) in existing:
                    item = next(item for item in data if item.get("userId") == user_id and item.get("text") == text)
                else:
                    memory_id = "mock-" + hashlib.sha1(f"{user_id}:{text}".encode()).hexdigest()[:16]
                    item = {"memoryId": memory_id, "text": text, "score": 1.0, "metadata": {"memoryBucket": bucket}, "userId": user_id}
                    data.append(item)
                    existing.add((user_id, text))
                result.append({key: item[key] for key in ("memoryId", "text", "score", "metadata")})
            self._write(data)
            return result

    async def search(self, *, user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        async with self._lock:
            data = self._read()
        terms = [term for term in re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", query) if len(term) > 1]
        matches: list[dict[str, Any]] = []
        for item in data:
            if item.get("userId") != user_id:
                continue
            text = str(item.get("text", ""))
            score = 1.0 if "喜欢" in query and "喜欢" in text else sum(term in text for term in terms) / max(len(terms), 1)
            if score > 0:
                matches.append({"memoryId": item["memoryId"], "text": text, "score": float(score), "metadata": item.get("metadata", {})})
        return sorted(matches, key=lambda item: item["score"], reverse=True)[: max(1, min(limit, 20))]

    async def health(self) -> dict[str, Any]:
        async with self._lock:
            self._read()
        return {"status": "ok", "provider": self.name}
