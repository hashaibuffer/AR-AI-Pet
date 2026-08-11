from __future__ import annotations

import unittest

from app.memory.service import MemoryService


class FakeProvider:
    name = "fake"

    def __init__(self, status: str) -> None:
        self.status = status

    async def health(self) -> dict[str, str]:
        return {"status": self.status, "provider": self.name}

    async def add(self, **_):
        return []

    async def search(self, **_):
        return []


class MemoryHealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_ok_is_top_level_ok(self) -> None:
        result = await MemoryService(None, FakeProvider("ok")).health()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["providerStatus"], "ok")

    async def test_provider_degraded_is_top_level_degraded(self) -> None:
        result = await MemoryService(None, FakeProvider("degraded")).health()
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["providerStatus"], "degraded")
