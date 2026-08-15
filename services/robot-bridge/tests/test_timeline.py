from __future__ import annotations

import time
import unittest

from app.adapters import execute_timeline
from app.scene_mapper import DeviceCommand


class TimelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_commands_keep_relative_order_and_delay(self) -> None:
        calls: list[tuple[str, float]] = []

        async def call_tool(name: str, arguments: dict) -> dict:
            calls.append((name, time.monotonic()))
            return {"isError": False, "content": []}

        started = time.monotonic()
        await execute_timeline([
            DeviceCommand(0, "first", {}, 0),
            DeviceCommand(80, "second", {}, 1),
        ], call_tool)
        self.assertEqual([name for name, _ in calls], ["first", "second"])
        self.assertGreaterEqual(calls[1][1] - started, 0.06)


if __name__ == "__main__":
    unittest.main()
