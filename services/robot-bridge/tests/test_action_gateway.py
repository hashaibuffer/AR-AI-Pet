from __future__ import annotations

import asyncio
import json
import unittest

from app.action_gateway import DeviceActionSession


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, value: str) -> None:
        self.sent.append(value)


class ActionGatewaySessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_call_uses_stackchan_mcp_envelope_and_resolves_reply(self) -> None:
        socket = FakeSocket()
        session = DeviceActionSession(socket, "AA:BB", "action-test")
        task = asyncio.create_task(
            session.call_tool("self.display.set_emotion", {"emotion": "happy"}, timeout=1)
        )
        while not socket.sent:
            await asyncio.sleep(0)
        request = json.loads(socket.sent[0])
        self.assertEqual(request["type"], "mcp")
        self.assertEqual(request["session_id"], "action-test")
        self.assertEqual(request["payload"]["method"], "tools/call")
        self.assertEqual(request["payload"]["params"]["name"], "self.display.set_emotion")
        session.handle_message({
            "type": "mcp",
            "payload": {
                "jsonrpc": "2.0",
                "id": request["payload"]["id"],
                "result": {"content": [{"type": "text", "text": "true"}], "isError": False},
            },
        })
        result = await task
        self.assertFalse(result["isError"])


if __name__ == "__main__":
    unittest.main()
