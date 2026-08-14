from __future__ import annotations

import unittest

from app.devices.session import DeviceSessionManager


class DeviceHealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_session_snapshot_is_explicit(self) -> None:
        manager = DeviceSessionManager()

        self.assertEqual(await manager.snapshot(), [])


if __name__ == "__main__":
    unittest.main()
