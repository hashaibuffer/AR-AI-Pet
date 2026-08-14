from __future__ import annotations

import unittest

from app.devices.session import DeviceSessionManager


class DeviceHealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_session_snapshot_is_explicit(self) -> None:
        manager = DeviceSessionManager()

        self.assertEqual(await manager.snapshot(), [])

    def test_scheme_b_uses_numeric_rpc_id_and_preserves_semantic_mapping(self) -> None:
        message = DeviceSessionManager._scheme_b_call(
            7, {"intent": "dance", "parameters": {}}
        )

        self.assertIsInstance(message["id"], int)
        self.assertEqual(message["id"], 7)
        self.assertEqual(message["params"]["name"], "self.robot.set_head_angles")


if __name__ == "__main__":
    unittest.main()
