from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MemoryDecision:
    eligible: bool
    bucket: str = "profile"
    reason: str = ""


class MemoryPolicy:
    allowed_buckets = {"profile", "preference", "habit", "relationship", "goal", "milestone"}

    def evaluate(self, messages: list[dict[str, Any]]) -> MemoryDecision:
        text = " ".join(str(item.get("content", "")) for item in messages if item.get("role") in {"user", "assistant"}).strip()
        if not text:
            return MemoryDecision(False, reason="empty")
        if re.fullmatch(r"[\s\u3000]*(你好|嗨|hi|hello|谢谢|谢了|好的|ok|嗯)[！!。.?？\s]*", text, re.IGNORECASE):
            return MemoryDecision(False, reason="small_talk")
        if re.search(r"日程|提醒|明天|后天|今天|上午|下午|几点|点钟|会议|开会|游戏|骰子|农场|种菜|设备|机器人|舵机|地址|token|密钥|密码", text, re.IGNORECASE):
            return MemoryDecision(False, reason="temporary_or_sensitive")
        bucket = "profile"
        for candidate, words in {
            "preference": ("喜欢", "不喜欢", "偏好", "爱吃"),
            "habit": ("习惯", "通常", "每天"),
            "relationship": ("家人", "朋友", "同事", "关系"),
            "goal": ("目标", "想要", "计划", "打算"),
            "milestone": ("完成", "毕业", "里程碑", "第一次"),
        }.items():
            if any(word in text for word in words):
                bucket = candidate
                break
        return MemoryDecision(True, bucket=bucket)
