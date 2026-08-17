from __future__ import annotations

import unittest

from app.adapters import StackChanAdapter


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, device_id: str, tool: str, arguments: dict, timeout: float) -> dict:
        self.calls.append((tool, dict(arguments)))
        return {"status": "accepted", "deviceId": device_id}


class StackChanAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_fixed_scene_uses_one_firmware_local_call(self) -> None:
        gateway = FakeGateway()
        adapter = StackChanAdapter(gateway)

        result = await adapter.execute("scene.play", {
            "sceneId": "dance",
            "durationMs": 12000,
            "steps": [{"atMs": 0, "target": "display", "action": "emotion", "value": "laughing"}],
        })

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["measuredResult"]["execution"], "firmware-local-scene")
        self.assertEqual(gateway.calls, [("self.scene.play", {"scene_id": "dance"})])


if __name__ == "__main__":
    unittest.main()
