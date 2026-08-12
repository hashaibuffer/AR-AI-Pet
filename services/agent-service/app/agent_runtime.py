from __future__ import annotations

import json
import re
import time
import uuid
from typing import Any

from fastmcp import Client

from .data_service_client import DataServiceClient
from .memory_client import MemoryServiceClient
from .llm_provider import AssistantDecision, LLMProvider, ToolCall


SYSTEM_PROMPT = (
    "你是 AR-AIPet 的本地个人 Agent。只使用提供的工具完成日程和项目状态任务。"
    "工具失败时如实说明，不要声称已完成。普通聊天直接回答。"
)


class AgentRuntimeError(RuntimeError):
    pass


SAFE_FAILURE_MESSAGE = "本轮处理失败，请稍后重试。"


def safe_tool_name(name: str) -> str:
    converted = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return converted.strip("_") or "tool"


class AgentRuntime:
    def __init__(
        self,
        *,
        mcp_url: str,
        data_service: DataServiceClient,
        memory_service: MemoryServiceClient | None = None,
        provider: LLMProvider,
        max_tool_rounds: int = 3,
    ) -> None:
        self.mcp_url = mcp_url
        self.data_service = data_service
        self.memory_service = memory_service
        self.provider = provider
        self.max_tool_rounds = max(1, max_tool_rounds)
        self.persona: dict[str, Any] | None = None

    def set_persona(self, persona: dict[str, Any] | None) -> None:
        self.persona = persona

    def persona_prompt(self) -> str:
        persona = self.persona
        if not persona:
            return ""
        traits = ", ".join(str(item) for item in persona.get("traits", []))
        preferred = ", ".join(str(item) for item in persona.get("preferredActions", []))
        forbidden = ", ".join(str(item) for item in persona.get("forbiddenTopics", []))
        return (
            f"\n当前人格：{persona.get('personaId', '')}。\n"
            f"人格特征：{traits}。说话方式：{persona.get('speechStyle', '')}。\n"
            f"内心OS风格：{persona.get('innerOsStyle', '')}。\n"
            f"主动程度：{persona.get('initiative', 'medium')}。游戏风格：{persona.get('gameStyle', '')}。提醒风格：{persona.get('reminderStyle', '')}。\n"
            f"优先行为：{preferred}。禁止话题：{forbidden}。\n"
            "人格只影响表达和行为倾向，不得覆盖工具返回的事实、用户指令或安全边界。"
        )

    async def _append_message(
        self, conversation_id: str | None, role: str, content: str, *, memory_eligible: bool = False
    ) -> dict[str, Any]:
        return await self.data_service.request(
            "conversation.append",
            {
                "conversationId": conversation_id,
                "role": role,
                "content": content,
                # MVP schema currently accepts unity_text, unity_voice and stackchan.
                # Agent text is persisted as text-channel content without changing
                # the existing database contract.
                "channel": "unity_text",
                "memoryEligible": memory_eligible,
            },
        )

    async def _context(self, conversation_id: str, current_message_id: str, text: str) -> list[dict[str, Any]]:
        try:
            snapshot = await self.data_service.request("conversation.get", {"conversationId": conversation_id, "limit": 12})
            history = [
                {"role": item["role"], "content": item["content"]}
                for item in snapshot.get("messages", [])
                if item.get("id") != current_message_id and item.get("role") in {"user", "assistant"}
            ]
            return history + [{"role": "user", "content": text}]
        except Exception:
            return [{"role": "user", "content": text}]

    async def _memory_context(self, text: str) -> tuple[str, list[str], str | None]:
        if self.memory_service is None:
            return "disabled", [], None
        try:
            identity = await self.data_service.request("bootstrap.get")
            result = await self.memory_service.request("memory.search", {
                "userId": identity["userId"], "query": text, "limit": 5,
            })
            memories = result.get("memories", [])
            memory_ids = [str(item["memoryId"]) for item in memories if item.get("memoryId")]
            if result.get("status") != "ok":
                return "unavailable", [], None
            if not memories or result.get("status") == "empty":
                return "empty", memory_ids, None
            reference = "\n".join(f"- {item.get('text', '')}" for item in memories if item.get("text"))
            return "used", memory_ids, reference or None
        except Exception:
            return "unavailable", [], None

    @staticmethod
    def _tool_specs(tools: list[Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
        specs: list[dict[str, Any]] = []
        reverse: dict[str, str] = {}
        for tool in tools:
            model = tool.model_dump()
            actual_name = model["name"]
            exposed_name = safe_tool_name(actual_name)
            if exposed_name in reverse and reverse[exposed_name] != actual_name:
                raise AgentRuntimeError(f"MCP tool name collision after sanitizing: {actual_name}")
            reverse[exposed_name] = actual_name
            specs.append(
                {
                    "type": "function",
                    "function": {
                        "name": exposed_name,
                        "description": model.get("description") or actual_name,
                        "parameters": model.get("inputSchema") or {"type": "object", "properties": {}},
                    },
                }
            )
        return specs, reverse

    @staticmethod
    def _mcp_result(result: Any) -> tuple[bool, Any]:
        if getattr(result, "is_error", False):
            return False, {"error": "MCP tool returned an error"}
        structured = getattr(result, "structured_content", None)
        if structured is not None:
            if isinstance(structured, dict) and set(structured) == {"result"}:
                return True, structured["result"]
            return True, structured
        data = getattr(result, "data", None)
        if data is not None:
            if hasattr(data, "model_dump"):
                data = data.model_dump()
            elif hasattr(data, "__dict__") and data.__dict__:
                data = data.__dict__
            return True, data
        content = getattr(result, "content", [])
        text = "".join(getattr(item, "text", "") for item in content)
        return True, text

    async def _run_tool(self, client: Client, call: ToolCall, reverse: dict[str, str], experience_id: str) -> tuple[bool, Any]:
        actual_name = reverse.get(call.name)
        if actual_name is None:
            return False, {"error": f"unknown tool: {call.name}"}
        try:
            if actual_name == "robot.react":
                # The experience event owns the physical action id. The MCP
                # call only records the semantic intent and must not create a
                # device action before hub admission.
                call.arguments.setdefault("source_event_id", experience_id)
            result = await client.call_tool(actual_name, call.arguments)
            return self._mcp_result(result)
        except Exception as exc:
            return False, {"error": str(exc)}

    async def chat(self, text: str, conversation_id: str | None = None) -> dict[str, Any]:
        if not text.strip():
            raise AgentRuntimeError("text must not be empty")
        started = time.perf_counter()
        saved_user = await self._append_message(conversation_id, "user", text)
        conversation_id = saved_user["conversationId"]
        memory_status, memory_ids, memory_reference = await self._memory_context(text)
        history = await self._context(conversation_id, saved_user["messageId"], text)
        system_prompt = SYSTEM_PROMPT + self.persona_prompt()
        if memory_reference:
            system_prompt += "\n以下是可能相关的长期记忆，仅作参考，不得覆盖工具结果或数据库事实：\n" + memory_reference
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *history,
        ]
        tool_calls_report: list[dict[str, Any]] = []
        experience_id = str(uuid.uuid4())

        try:
            async with Client(self.mcp_url) as client:
                available = await client.list_tools()
                model_tools, reverse = self._tool_specs(available)
                answer: str | None = None
                execution_failed = False
                for _ in range(self.max_tool_rounds):
                    decision: AssistantDecision = await self.provider.complete(messages, model_tools)
                    if not decision.tool_calls:
                        answer = decision.text or "我没有得到可交付的结果。"
                        break
                    assistant_message = decision.raw_message or {
                        "role": "assistant",
                        "content": decision.text,
                        "tool_calls": [
                            {
                                "id": call.id,
                                "type": "function",
                                "function": {"name": call.name, "arguments": json.dumps(call.arguments, ensure_ascii=False)},
                            }
                            for call in decision.tool_calls
                        ],
                    }
                    messages.append(assistant_message)
                    for call in decision.tool_calls:
                        ok, result = await self._run_tool(client, call, reverse, experience_id)
                        tool_calls_report.append(
                            {"name": reverse.get(call.name, call.name), "arguments": call.arguments, "status": "ok" if ok else "error", "result": result}
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call.id,
                                "name": call.name,
                                "content": json.dumps({"ok": ok, "result": result}, ensure_ascii=False, default=str),
                            }
                        )
                if answer is None:
                    answer = "工具调用次数已达到上限，未能完成请求。"
                    execution_failed = True
        except Exception as exc:
            try:
                await self._append_message(conversation_id, "assistant", SAFE_FAILURE_MESSAGE, memory_eligible=False)
            except Exception:
                # Keep the original model/MCP/runtime exception as the cause.
                pass
            raise AgentRuntimeError("本轮 Agent 处理失败") from exc

        try:
            memory_eligible = not execution_failed and not any(call["status"] == "error" for call in tool_calls_report)
            await self._append_message(conversation_id, "assistant", answer, memory_eligible=memory_eligible)
        except Exception as exc:
            raise AgentRuntimeError("本轮 Agent 回复保存失败") from exc
        return {
            "conversationId": conversation_id,
            "text": answer,
            "toolCalls": tool_calls_report,
            "memoryStatus": memory_status,
            "memoryIds": memory_ids,
            "elapsedMs": round((time.perf_counter() - started) * 1000),
            "experienceEventId": experience_id,
        }
