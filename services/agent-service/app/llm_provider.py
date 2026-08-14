from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

import httpx


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class AssistantDecision:
    text: str | None
    tool_calls: list[ToolCall]
    raw_message: dict[str, Any] | None = None


class LLMProviderError(RuntimeError):
    pass


class LLMProvider(Protocol):
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AssistantDecision: ...


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(item.get("text", "") for item in content if isinstance(item, dict))
    return ""


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AssistantDecision:
        if not self.api_key:
            raise LLMProviderError("AGENT_LLM_API_KEY is not configured")
        body: dict[str, Any] = {"model": self.model, "messages": messages, "temperature": 0.2}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMProviderError(f"LLM request failed: {exc}") from exc

        try:
            message = result["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("LLM response did not contain a chat message") from exc
        calls: list[ToolCall] = []
        for call in message.get("tool_calls", []) or []:
            function = call.get("function", {})
            try:
                arguments = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError as exc:
                raise LLMProviderError("LLM returned invalid tool arguments") from exc
            if not isinstance(arguments, dict):
                raise LLMProviderError("LLM tool arguments must be an object")
            calls.append(ToolCall(str(call.get("id", "tool-call")), function["name"], arguments))
        return AssistantDecision(_message_text(message) or None, calls, message)


class MockProvider:
    """Deterministic provider used only by the local Agent smoke test."""

    def __init__(self, timezone_name: str = "Asia/Shanghai") -> None:
        try:
            self.timezone = ZoneInfo(timezone_name)
        except Exception:
            self.timezone = ZoneInfo("UTC")

    def _schedule_arguments(self, text: str) -> dict[str, Any]:
        now = datetime.now(self.timezone)
        day = now.date() + timedelta(days=1 if "明天" in text else 0)
        match = re.search(r"(上午|下午)?\s*(\d{1,2})\s*点", text)
        hour = int(match.group(2)) if match else 15
        if match and match.group(1) == "下午" and hour < 12:
            hour += 12
        starts = datetime(day.year, day.month, day.day, hour, 0, tzinfo=self.timezone)
        title = "开会" if "开会" in text else "日程提醒"
        return {
            "title": title,
            "description": None,
            "starts_at": starts.isoformat(),
            "remind_at": (starts - timedelta(minutes=5)).isoformat(),
            "repeat_type": "none",
        }

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AssistantDecision:
        user_text = next((_message_text(item) for item in reversed(messages) if item.get("role") == "user"), "")
        has_tool_result = any(item.get("role") == "tool" for item in messages)
        if not has_tool_result and ("跳舞" in user_text or "跳个舞" in user_text):
            robot_tool = next((tool for tool in tools if tool["function"]["name"] == "robot_react"), None)
            if robot_tool:
                return AssistantDecision(None, [ToolCall("mock-dance", "robot_react", {"action_type": "dance", "parameters": {}})])
        if not has_tool_result and any(word in user_text for word in ("前进", "后退", "左转", "右转")):
            robot_tool = next((tool for tool in tools if tool["function"]["name"] == "robot_react"), None)
            if robot_tool:
                direction = next(
                    word for word in ("前进", "后退", "左转", "右转") if word in user_text
                )
                return AssistantDecision(
                    None,
                    [ToolCall(
                        "mock-base-move",
                        "robot_react",
                        {"action_type": "base_move", "parameters": {"direction": direction, "speed": 100}},
                    )],
                )
        if has_tool_result and any(item.get("name") == "robot_react" for item in messages if item.get("role") == "tool"):
            if "前进" in user_text:
                return AssistantDecision("好，我让它前进。", [])
            if "后退" in user_text:
                return AssistantDecision("好，我让它后退。", [])
            if "左转" in user_text:
                return AssistantDecision("好，我让它左转。", [])
            if "右转" in user_text:
                return AssistantDecision("好，我让它右转。", [])
            return AssistantDecision("好呀，我们一起跳舞。", [])
        if not has_tool_result and "提醒" in user_text:
            schedule_tool = next((tool for tool in tools if tool["function"]["name"] == "schedule_upsert"), None)
            if schedule_tool:
                return AssistantDecision(
                    None,
                    [ToolCall("mock-schedule", "schedule_upsert", self._schedule_arguments(user_text))],
                )
        if not has_tool_result and "工具失败" in user_text:
            schedule_tool = next((tool for tool in tools if tool["function"]["name"] == "schedule_upsert"), None)
            if schedule_tool:
                return AssistantDecision(
                    None,
                    [ToolCall("mock-failure", "schedule_upsert", {"title": "", "starts_at": "bad", "remind_at": "bad", "repeat_type": "none"})],
                )
        if not has_tool_result and "日程" in user_text:
            schedule_tool = next((tool for tool in tools if tool["function"]["name"] == "schedule_list"), None)
            if schedule_tool:
                return AssistantDecision(None, [ToolCall("mock-list", "schedule_list", {"limit": 100})])
        if has_tool_result:
            result = next((item.get("content", "") for item in reversed(messages) if item.get("role") == "tool"), "")
            if "error" in result.lower() or "failed" in result.lower():
                return AssistantDecision(f"我暂时无法完成这个请求：{result}", [])
            if any(item.get("name") == "schedule_list" for item in messages if item.get("role") == "tool"):
                return AssistantDecision("这是当前保存的日程。", [])
            return AssistantDecision("已完成，我已经把这条日程保存好了。", [])
        system_text = next((_message_text(item) for item in messages if item.get("role") == "system"), "")
        if "喜欢" in user_text and "草莓" in system_text and "香菜" in system_text:
            return AssistantDecision("你最喜欢草莓，不喜欢香菜。", [])
        return AssistantDecision("这是本地 Mock Agent 的回复：" + (user_text or "你好。"), [])


def create_provider(
    mode: str,
    *,
    base_url: str,
    api_key: str,
    model: str,
    timezone_name: str,
    timeout_seconds: float,
) -> LLMProvider:
    if mode == "mock":
        return MockProvider(timezone_name)
    if mode == "openai":
        return OpenAICompatibleProvider(base_url, api_key, model, timeout_seconds)
    raise ValueError(f"unsupported AGENT_PROVIDER: {mode}")
