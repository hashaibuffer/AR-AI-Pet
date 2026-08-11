from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.agent_runtime import AgentRuntime, SAFE_FAILURE_MESSAGE
from app.llm_provider import AssistantDecision, ToolCall


class FakeDataService:
    def __init__(self) -> None:
        self.messages: list[tuple[str | None, str, str]] = []

    async def request(self, _message_type: str, payload: dict) -> dict:
        conversation_id = payload.get("conversationId") or "conversation-1"
        self.messages.append((conversation_id, payload["role"], payload["content"]))
        return {"conversationId": conversation_id, "messageId": "message-1"}


class AlwaysToolProvider:
    async def complete(self, _messages: list[dict], _tools: list[dict]) -> AssistantDecision:
        return AssistantDecision(None, [ToolCall("tool-1", "schedule_list", {"limit": 1})])


class FailingProvider:
    async def complete(self, _messages: list[dict], _tools: list[dict]) -> AssistantDecision:
        raise RuntimeError("provider internals must not be persisted")


class FakeClient:
    def __init__(self, _url: str) -> None:
        self.calls = 0

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def list_tools(self) -> list[SimpleNamespace]:
        return [SimpleNamespace(model_dump=lambda: {"name": "schedule.list", "description": "list", "inputSchema": {}})]

    async def call_tool(self, _name: str, _arguments: dict) -> SimpleNamespace:
        self.calls += 1
        return SimpleNamespace(is_error=False, data={"items": []})


class AgentRuntimeBoundaryTests(unittest.TestCase):
    def test_tool_round_limit_is_exact(self) -> None:
        async def run() -> tuple[dict, FakeClient]:
            data = FakeDataService()
            client = FakeClient("unused")
            with patch("app.agent_runtime.Client", return_value=client):
                result = await AgentRuntime(
                    mcp_url="unused", data_service=data, provider=AlwaysToolProvider(), max_tool_rounds=3
                ).chat("请查询日程")
            return result, client

        result, client = asyncio.run(run())
        self.assertEqual(client.calls, 3)
        self.assertIn("达到上限", result["text"])
        self.assertEqual(len(result["toolCalls"]), 3)

    def test_failure_persists_safe_assistant_message_with_same_conversation(self) -> None:
        async def run() -> tuple[FakeDataService, Exception]:
            data = FakeDataService()
            with patch("app.agent_runtime.Client", return_value=FakeClient("unused")):
                with self.assertRaises(Exception) as raised:
                    await AgentRuntime(
                        mcp_url="unused", data_service=data, provider=FailingProvider(), max_tool_rounds=3
                    ).chat("触发失败")
            return data, raised.exception

        data, error = asyncio.run(run())
        self.assertEqual(str(error), "本轮 Agent 处理失败")
        self.assertEqual([item[0] for item in data.messages], ["conversation-1", "conversation-1"])
        self.assertEqual(data.messages[-1][1:], ("assistant", SAFE_FAILURE_MESSAGE))
        self.assertNotIn("provider internals", SAFE_FAILURE_MESSAGE)


if __name__ == "__main__":
    unittest.main()
