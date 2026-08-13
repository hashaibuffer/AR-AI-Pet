from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path

from websockets.asyncio.server import serve

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import StackChanWebSocketAdapter  # noqa: E402


class StackChanAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.messages: list[dict] = []

        async def handler(socket) -> None:
            async for raw in socket:
                self.messages.append(json.loads(raw))

        self.server = await serve(handler, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        self.adapter = StackChanWebSocketAdapter(
            f"ws://127.0.0.1:{self.port}/ws",
            max_duration_seconds=0.1,
        )

    async def asyncTearDown(self) -> None:
        await self.adapter.close()
        self.server.close()
        await self.server.wait_closed()

    async def _wait_for_messages(self, count: int) -> None:
        for _ in range(20):
            if len(self.messages) >= count:
                return
            await asyncio.sleep(0.01)
        self.fail(f"expected {count} StackChan calls, got {len(self.messages)}")

    async def test_nod_maps_to_head_angle_sequence(self) -> None:
        outcome = await self.adapter.execute("nod", {})
        await self._wait_for_messages(2)

        self.assertEqual(outcome["status"], "dispatched")
        self.assertTrue(outcome["measuredResult"]["transportAccepted"])
        self.assertFalse(outcome["measuredResult"]["physicalConfirmed"])
        self.assertEqual(
            [message["params"]["name"] for message in self.messages],
            ["self.robot.set_head_angles", "self.robot.set_head_angles"],
        )
        self.assertEqual(self.messages[0]["params"]["arguments"]["pitch"], 15)
        self.assertEqual(self.messages[1]["params"]["arguments"]["pitch"], 0)

    async def test_base_move_is_bounded_and_stops(self) -> None:
        outcome = await self.adapter.execute(
            "base_move",
            {"direction": "forward", "speed": 180, "durationSeconds": 0.05},
        )
        await self._wait_for_messages(2)

        self.assertEqual(outcome["status"], "dispatched")
        self.assertEqual(self.messages[0]["params"]["name"], "self.robot.base_move")
        self.assertEqual(self.messages[0]["params"]["arguments"], {"direction": "forward", "speed": 180})
        self.assertEqual(self.messages[1]["params"]["name"], "self.robot.base_stop")

    async def test_stop_sends_motion_and_base_stop(self) -> None:
        await self.adapter.execute("nod", {})
        await self._wait_for_messages(2)
        self.messages.clear()
        await self.adapter.stop("test")
        await self._wait_for_messages(2)
        self.assertEqual(
            [message["params"]["name"] for message in self.messages],
            ["self.robot.stop_motion", "self.robot.base_stop"],
        )

    async def test_unsafe_parameters_are_rejected_without_send(self) -> None:
        outcome = await self.adapter.execute("base_move", {"direction": "forward", "speed": 999})
        self.assertEqual(outcome["status"], "failed")
        self.assertIn("unsafe_base_speed", outcome["error"])
        await asyncio.sleep(0.02)
        self.assertEqual(self.messages, [])

    async def test_unknown_intent_is_rejected(self) -> None:
        outcome = await self.adapter.execute("teleport", {})
        self.assertEqual(outcome["status"], "failed")
        self.assertEqual(outcome["error"], "unsupported_intent:teleport")


if __name__ == "__main__":
    unittest.main()
