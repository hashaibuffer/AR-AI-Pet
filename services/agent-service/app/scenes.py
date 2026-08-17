from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SceneDefinition:
    scene_id: str
    aliases: tuple[str, ...]
    priority: int
    duration_ms: int
    emotion: str
    voice_before: str
    voice_after: str = ""
    steps: tuple[dict[str, Any], ...] = ()

    def as_payload(self) -> dict[str, Any]:
        return {
            "sceneId": self.scene_id,
            "durationMs": self.duration_ms,
            "emotion": self.emotion,
            "steps": [dict(step) for step in self.steps],
            "voiceBefore": self.voice_before,
            "voiceAfter": self.voice_after,
        }


SCENES: dict[str, SceneDefinition] = {
    "wake_up": SceneDefinition(
        "wake_up", (), 100, 4800, "happy", "", steps=(
            {"atMs": 0, "target": "display", "action": "emotion", "value": "sleepy"},
            {"atMs": 150, "target": "head", "action": "pose", "value": "raise"},
            {"atMs": 500, "target": "led", "action": "effect", "value": "warm_fade_in"},
            {"atMs": 700, "target": "head", "action": "pose", "value": "look_left"},
            {"atMs": 1100, "target": "head", "action": "pose", "value": "look_right"},
            {"atMs": 1500, "target": "head", "action": "pose", "value": "user"},
            {"atMs": 1900, "target": "display", "action": "emotion", "value": "surprised"},
            {"atMs": 2500, "target": "display", "action": "emotion", "value": "happy"},
            {"atMs": 3200, "target": "head", "action": "pose", "value": "nod"},
            {"atMs": 3900, "target": "display", "action": "emotion", "value": "winking"},
            {"atMs": 4400, "target": "led", "action": "effect", "value": "off"},
        ),
    ),
    "good_night": SceneDefinition(
        "good_night", ("晚安", "我要睡了", "睡觉了", "晚安啦"), 90, 7200, "sleepy",
        "晚安，明天见。我也要休息啦。", steps=(
            {"atMs": 0, "target": "display", "action": "emotion", "value": "relaxed"},
            {"atMs": 300, "target": "head", "action": "pose", "value": "nod"},
            {"atMs": 900, "target": "display", "action": "emotion", "value": "sleepy"},
            {"atMs": 1200, "target": "head", "action": "pose", "value": "tilt"},
            {"atMs": 1800, "target": "led", "action": "effect", "value": "amber_breathe_2"},
            {"atMs": 2700, "target": "display", "action": "emotion", "value": "kissy"},
            {"atMs": 3300, "target": "head", "action": "pose", "value": "down"},
            {"atMs": 4300, "target": "display", "action": "emotion", "value": "sleepy"},
            {"atMs": 5000, "target": "head", "action": "pose", "value": "down"},
            {"atMs": 6100, "target": "display", "action": "emotion", "value": "relaxed"},
            {"atMs": 6800, "target": "led", "action": "effect", "value": "off"},
        ),
    ),
    "play": SceneDefinition(
        "play", ("陪我玩", "玩一下", "玩起来", "玩乐", "和我玩"), 100, 8500, "silly",
        "好呀，来玩一下！", steps=(
            {"atMs": 0, "target": "display", "action": "emotion", "value": "silly"},
            {"atMs": 0, "target": "led", "action": "effect", "value": "color_cycle"},
            {"atMs": 300, "target": "head", "action": "pose", "value": "left"},
            {"atMs": 700, "target": "head", "action": "pose", "value": "right"},
            {"atMs": 1100, "target": "head", "action": "pose", "value": "nod"},
            {"atMs": 1300, "target": "base", "action": "move", "value": "turn_left_short"},
            {"atMs": 2400, "target": "base", "action": "stop", "value": "immediate"},
            {"atMs": 2700, "target": "display", "action": "emotion", "value": "happy"},
            {"atMs": 3100, "target": "base", "action": "move", "value": "turn_right_short"},
            {"atMs": 4200, "target": "base", "action": "stop", "value": "immediate"},
            {"atMs": 4500, "target": "head", "action": "pose", "value": "nod_twice"},
            {"atMs": 5400, "target": "display", "action": "emotion", "value": "laughing"},
            {"atMs": 6500, "target": "display", "action": "emotion", "value": "winking"},
            {"atMs": 7600, "target": "led", "action": "effect", "value": "off"},
        ),
    ),
    "welcome_home": SceneDefinition(
        "welcome_home", ("我回来了", "我到家了", "回家了"), 100, 6500, "loving",
        "欢迎回家！我等你好久啦。", steps=(
            {"atMs": 0, "target": "display", "action": "emotion", "value": "surprised"},
            {"atMs": 0, "target": "led", "action": "effect", "value": "warm_fade_in"},
            {"atMs": 300, "target": "head", "action": "pose", "value": "look_left"},
            {"atMs": 700, "target": "head", "action": "pose", "value": "look_right"},
            {"atMs": 1100, "target": "head", "action": "pose", "value": "user"},
            {"atMs": 1300, "target": "display", "action": "emotion", "value": "happy"},
            {"atMs": 1500, "target": "base", "action": "move", "value": "forward_short"},
            {"atMs": 2500, "target": "base", "action": "stop", "value": "immediate"},
            {"atMs": 2900, "target": "head", "action": "pose", "value": "nod_twice"},
            {"atMs": 3900, "target": "display", "action": "emotion", "value": "loving"},
            {"atMs": 4700, "target": "head", "action": "pose", "value": "tilt"},
            {"atMs": 5700, "target": "led", "action": "effect", "value": "off"},
        ),
    ),
    "reminder": SceneDefinition(
        "reminder", ("提醒我", "喝水提醒", "休息提醒", "提醒喝水", "提醒休息", "工作提醒", "日程提醒"), 80, 5200, "thinking", "", steps=(
            {"atMs": 0, "target": "display", "action": "icon", "value": "clock"},
            {"atMs": 0, "target": "led", "action": "effect", "value": "blue_pulse"},
            {"atMs": 400, "target": "head", "action": "pose", "value": "user"},
            {"atMs": 1700, "target": "display", "action": "emotion", "value": "thinking"},
            {"atMs": 2200, "target": "head", "action": "pose", "value": "nod_twice"},
            {"atMs": 3300, "target": "display", "action": "emotion", "value": "surprised"},
            {"atMs": 4000, "target": "head", "action": "pose", "value": "tilt"},
            {"atMs": 4700, "target": "led", "action": "effect", "value": "off"},
        ),
    ),
    "comfort": SceneDefinition(
        "comfort", ("安慰我", "我有点难过", "陪陪我"), 100, 7600, "loving",
        "没关系，我在这里。你可以慢慢来。", steps=(
            {"atMs": 0, "target": "display", "action": "emotion", "value": "sad"},
            {"atMs": 400, "target": "head", "action": "pose", "value": "tilt"},
            {"atMs": 1000, "target": "led", "action": "effect", "value": "amber_breathe"},
            {"atMs": 1500, "target": "base", "action": "move", "value": "forward_gentle"},
            {"atMs": 2400, "target": "base", "action": "stop", "value": "immediate"},
            {"atMs": 2800, "target": "display", "action": "emotion", "value": "relaxed"},
            {"atMs": 3500, "target": "head", "action": "pose", "value": "nod"},
            {"atMs": 4300, "target": "display", "action": "emotion", "value": "loving"},
            {"atMs": 5200, "target": "head", "action": "pose", "value": "user"},
            {"atMs": 6500, "target": "led", "action": "effect", "value": "off"},
        ),
    ),
    "dance": SceneDefinition(
        "dance", ("跳舞", "跳个舞", "给我跳舞", "跳舞吧", "跳一段"), 100, 12000, "laughing",
        "看我的！", "怎么样，我跳得不错吧？", steps=(
            {"atMs": 0, "target": "display", "action": "icon", "value": "music"},
            {"atMs": 0, "target": "led", "action": "effect", "value": "color_cycle_fast"},
            {"atMs": 400, "target": "head", "action": "pose", "value": "left"},
            {"atMs": 800, "target": "head", "action": "pose", "value": "right"},
            {"atMs": 1200, "target": "head", "action": "pose", "value": "nod"},
            {"atMs": 1400, "target": "base", "action": "move", "value": "turn_left_short"},
            {"atMs": 2500, "target": "base", "action": "stop", "value": "immediate"},
            {"atMs": 2700, "target": "display", "action": "emotion", "value": "silly"},
            {"atMs": 3000, "target": "base", "action": "move", "value": "turn_right_short"},
            {"atMs": 4100, "target": "base", "action": "stop", "value": "immediate"},
            {"atMs": 4400, "target": "head", "action": "pose", "value": "left_right_left"},
            {"atMs": 5700, "target": "head", "action": "pose", "value": "nod_twice"},
            {"atMs": 6900, "target": "display", "action": "emotion", "value": "laughing"},
            {"atMs": 8000, "target": "led", "action": "effect", "value": "color_cycle_fast"},
            {"atMs": 9400, "target": "head", "action": "pose", "value": "user"},
            {"atMs": 10100, "target": "display", "action": "emotion", "value": "cool"},
            {"atMs": 11200, "target": "led", "action": "effect", "value": "off"},
        ),
    ),
}


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", str(text)).lower()
    value = re.sub(r"[\s\u3000,，。！？!?、；;：:‘’“”\"'（）()【】\[\]{}]+", "", value)
    return value


_SCHEDULE_TIME_PATTERN = re.compile(
    r"(?:今天|明天|后天|今晚|明早|上午|中午|下午|晚上|凌晨|"
    r"周[一二三四五六日天]|星期[一二三四五六日天]|"
    r"每天|每日|每周|每月|稍后|一会儿|"
    r"(?:\d{1,2}|[一二三四五六七八九十两]+)(?:点|时)|\d{1,2}[:：]|"
    r"(?:\d+|半|[一二三四五六七八九十两]+)(?:分钟|小时|天)后|"
    r"\d{4}(?:年|[-/])\d{1,2})"
)


def _looks_like_schedule_request(text: str) -> bool:
    """Keep time-bearing reminder requests on the Agent scheduling path."""

    return bool(_SCHEDULE_TIME_PATTERN.search(unicodedata.normalize("NFKC", str(text))))


class ExactSceneRouter:
    """Match only an allow-listed phrase; everything else goes to the Agent."""

    _prefixes = ("小智", "小陈", "宝贝", "宝宝", "小可爱")
    _negations = ("不想", "不要", "别", "不用", "不需要")

    def match(self, text: str) -> SceneDefinition | None:
        compact = normalize_text(text)
        if not compact or any(word in compact for word in self._negations):
            return None
        candidates = [compact]
        for prefix in self._prefixes:
            if compact.startswith(prefix):
                candidates.append(compact[len(prefix):])
        for candidate in candidates:
            for scene in sorted(SCENES.values(), key=lambda item: item.priority, reverse=True):
                aliases = sorted((normalize_text(alias) for alias in scene.aliases), key=len, reverse=True)
                if any(alias and alias in candidate for alias in aliases):
                    if scene.scene_id == "reminder" and _looks_like_schedule_request(text):
                        continue
                    return scene
        return None


def get_scene(scene_id: str) -> SceneDefinition:
    try:
        return SCENES[scene_id]
    except KeyError as exc:
        raise ValueError(f"unknown scene: {scene_id}") from exc
