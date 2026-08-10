"""
扫雷游戏插件 - QwenPaw
HTML5 Canvas 版本，直接在浏览器中运行。
游戏逻辑在前端实现；后端提供状态查询与「本地参谋智能体」建议接口。

v1.2.0 新增：安装插件时自动安装「扫雷参谋」智能体（minesweeper-sage）。
安装 / 重装插件时通过本机 API 幂等创建参谋 agent，并把打包的参谋模板
（PROFILE.md / SOUL.md / AGENTS.md / MEMORY.md 等）复制到其工作区。
"""
import json
import logging
import re
import shutil
import time
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from pydantic import BaseModel

try:
    from qwenpaw.plugins.api import PluginApi
except ImportError:
    PluginApi = None

logger = logging.getLogger(__name__)

router = APIRouter()

# ============ 本地参谋智能体 ============
SAGE_AGENT_ID = "minesweeper-sage"
SAGE_FROM_AGENT = "cloud-orchestrator"
SAGE_HTTP_TIMEOUT = 180.0  # 参谋推理可能较慢，放宽读取超时


class AdviceRequest(BaseModel):
    rows: int
    cols: int
    mines: int
    revealed_count: int = 0
    flags_count: int = 0
    status: str = "ready"
    timer: int = 0
    board_text: str = ""


def _extract_reply(data: dict) -> str:
    """从 `/console/chat` SSE 的最终 payload 中提取参谋回复文本。"""
    outputs = data.get("output", [])
    # 优先取最后一个 type=message 的 assistant 消息
    for msg in reversed(outputs):
        if msg.get("type") == "message" and msg.get("role") == "assistant":
            parts = [
                c.get("text")
                for c in msg.get("content", [])
                if c.get("type") == "text" and c.get("text")
            ]
            if parts:
                return "\n".join(parts)
    # 兜底：任意最后一条带文本的输出
    for msg in reversed(outputs):
        parts = [
            c.get("text")
            for c in msg.get("content", [])
            if c.get("type") == "text" and c.get("text")
        ]
        if parts:
            return "\n".join(parts)
    # 顶层直接带文本（部分版本结构）
    top_parts = [
        c.get("text")
        for c in data.get("content", [])
        if isinstance(c, dict) and c.get("type") == "text" and c.get("text")
    ]
    if top_parts:
        return "\n".join(top_parts)
    return "(参谋暂无回复)"


def _clean_advice(reply: str) -> str:
    """清理建议文本中的杂讯（HTML 注释等），并去掉首尾空行。"""
    cleaned = re.sub(r"<!--.*?-->", "", reply, flags=re.S)
    return cleaned.strip()

# 难度定义（与前端 ui/index.js 保持一致）
DIFFICULTIES = {
    "easy": {"label": "简单", "rows": 9, "cols": 9, "mines": 10},
    "medium": {"label": "中等", "rows": 16, "cols": 16, "mines": 40},
    "hard": {"label": "困难", "rows": 16, "cols": 30, "mines": 99},
}


@router.get("/status")
async def get_status():
    """获取游戏状态与难度配置"""
    return {
        "status": "ready",
        "version": "1.2.1",
        "type": "html5_canvas",
        "difficulties": DIFFICULTIES,
        "sage_agent": SAGE_AGENT_ID,
    }


async def _call_sage(api_base: str, prompt: str) -> dict:
    """通过本机 API 的 /console/chat 接口调用参谋智能体（SSE 收集最终响应）。

    注意：必须用异步客户端——插件路由与 /console/chat 共用同一事件循环，
    若用同步 httpx 会阻塞事件循环导致参谋请求永远无法被处理（死锁）。
    """
    caller = SAGE_FROM_AGENT
    to_agent = SAGE_AGENT_ID
    session_id = f"{caller}:to:{to_agent}:{int(time.time() * 1000)}:{uuid4().hex[:8]}"
    payload = {
        "session_id": session_id,
        "user_id": caller,
        "input": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            },
        ],
        "request_context": {"root_agent_id": caller},
    }
    normalized = api_base.rstrip("/") + "/api"
    last_data = None
    async with httpx.AsyncClient(
        base_url=normalized,
        timeout=SAGE_HTTP_TIMEOUT,
        trust_env=False,
    ) as client:
        async with client.stream(
            "POST",
            "/console/chat",
            json=payload,
            headers={"X-Agent-Id": to_agent},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                stripped = (line or "").strip()
                if stripped.startswith("data: "):
                    try:
                        parsed = json.loads(stripped[6:])
                    except Exception:
                        continue
                    if parsed and parsed.get("type") != "turn_usage":
                        last_data = parsed
    if last_data is None:
        raise RuntimeError("参谋未返回有效响应（SSE 为空）")
    return last_data


@router.post("/advice")
async def get_advice(req: AdviceRequest, request: Request):
    """调用本地参谋智能体（minesweeper-sage）分析盘面并返回建议。"""
    if not req.board_text.strip():
        return {"ok": False, "error": "盘面为空，无法分析"}
    prompt = (
        "你是扫雷参谋。以下是当前扫雷盘面"
        "（?=未翻开，数字=已翻开且周围雷数，.=已翻开的空白，F=插旗（认为是雷），Q=问号）：\n"
        f"盘面 {req.rows}x{req.cols}，共 {req.mines} 雷，已翻开 {req.revealed_count} 格，"
        f"已插旗 {req.flags_count} 个，用时 {req.timer} 秒。\n\n"
        f"{req.board_text}\n\n"
        "请直接按你的输出格式给出下一步建议；不要调用任何工具。"
    )
    try:
        api_base = str(request.base_url).rstrip("/")
        reply_data = await _call_sage(api_base, prompt)
        reply = _clean_advice(_extract_reply(reply_data))
        return {"ok": True, "advice": reply}
    except httpx.HTTPStatusError as exc:
        return {"ok": False, "error": f"参谋接口返回 {exc.response.status_code}: {exc.response.text[:300]}"}
    except httpx.TimeoutException:
        return {"ok": False, "error": f"参谋响应超时（{int(SAGE_HTTP_TIMEOUT)} 秒），请稍后重试"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("[minesweeper-game] advice failed")
        return {"ok": False, "error": f"调用参谋失败: {exc}"}


class MinesweeperGamePlugin:
    """扫雷游戏插件"""

    def __init__(self):
        self.name = "扫雷"
        self.version = "1.2.1"
        self.id = "minesweeper-game"
        self.router = router

    def register(self, api) -> None:
        """注册插件"""
        if hasattr(api, "register_http_router"):
            api.register_http_router(
                self.router,
                prefix="/minesweeper-game",
                tags=["minesweeper-game"],
            )
            logger.info("[minesweeper-game] HTTP router registered")

        if hasattr(api, "register_startup_hook"):
            # 安装 / 启动插件时自动安装「扫雷参谋」智能体
            api.register_startup_hook(
                "minesweeper_ensure_sage",
                self._ensure_sage_agent,
                priority=40,
            )
            api.register_startup_hook("minesweeper_startup", self._startup)

        if hasattr(api, "register_shutdown_hook"):
            api.register_shutdown_hook("minesweeper_shutdown", self._shutdown)

    # ---------- 自动安装扫雷参谋智能体 ----------
    async def _ensure_sage_agent(self) -> None:
        """安装插件时自动安装「扫雷参谋」智能体（幂等）。

        通过本机 API 的 POST /api/agents 创建 minesweeper-sage，
        再把随插件打包的参谋模板复制到其工作区。
        任一步失败都不影响插件本身运行，仅记录日志。
        """
        try:
            # 1) 幂等：参谋已注册则跳过
            from qwenpaw.config import load_config

            config = load_config()
            if SAGE_AGENT_ID in config.agents.profiles:
                logger.info(
                    "[minesweeper-game] 参谋智能体 %s 已存在，跳过自动安装",
                    SAGE_AGENT_ID,
                )
                return

            # 2) 解析本机 API 地址
            api_base = "http://127.0.0.1:8088"
            try:
                from qwenpaw.config.utils import read_last_api

                addr = read_last_api()
                if addr and addr[0] and addr[1]:
                    api_base = f"http://{addr[0]}:{addr[1]}"
            except Exception:  # noqa: BLE001
                pass

            # 3) 通过官方 API 创建参谋 agent（创建成功会自动调度启动）
            payload = {
                "id": SAGE_AGENT_ID,
                "name": "扫雷参谋",
                "description": (
                    "扫雷专家智能体：分析扫雷盘面、推导安全格子、识别雷区，"
                    "给出下一步落子建议与理由。只做分析与建议，不执行任何外部操作。"
                ),
                "language": "zh-CN",
                "skill_names": [],
            }
            agent_ref = {}
            async with httpx.AsyncClient(
                base_url=api_base,
                timeout=60.0,
                trust_env=False,
            ) as client:
                resp = await client.post("/api/agents", json=payload)
                resp.raise_for_status()
                agent_ref = resp.json()

            workspace_dir = (agent_ref or {}).get("workspace_dir") or ""
            # 4) 复制打包的参谋模板（覆盖默认生成的 MD 文件）
            self._copy_sage_templates(Path(workspace_dir) if workspace_dir else None)
            logger.info(
                "[minesweeper-game] 参谋智能体 %s 自动安装完成: %s",
                SAGE_AGENT_ID,
                workspace_dir or api_base,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "[minesweeper-game] 自动安装参谋智能体失败（不影响插件运行）"
            )

    @staticmethod
    def _copy_sage_templates(workspace_dir: Path | None) -> None:
        """把随插件打包的参谋模板文件复制到参谋工作区。"""
        if workspace_dir is None or not workspace_dir.is_dir():
            logger.warning(
                "[minesweeper-game] 参谋工作区不存在，跳过模板复制: %s",
                workspace_dir,
            )
            return
        template_dir = (
            Path(__file__).resolve().parent / "agents" / SAGE_AGENT_ID
        )
        if not template_dir.is_dir():
            logger.warning(
                "[minesweeper-game] 参谋模板目录不存在: %s", template_dir
            )
            return
        copied = []
        for item in template_dir.iterdir():
            if item.is_file():
                try:
                    shutil.copy2(item, workspace_dir / item.name)
                    copied.append(item.name)
                except OSError as exc:  # noqa: PERF203
                    logger.warning(
                        "[minesweeper-game] 复制模板 %s 失败: %s", item.name, exc
                    )
        logger.info(
            "[minesweeper-game] 参谋模板已复制到 %s: %s",
            workspace_dir,
            ", ".join(copied) or "(无)",
        )

    async def _startup(self) -> None:
        logger.info("[minesweeper-game] Plugin started - HTML5 Canvas version")

    async def _shutdown(self) -> None:
        logger.info("[minesweeper-game] Plugin stopped")


# REQUIRED: 模块级 plugin 实例
plugin = MinesweeperGamePlugin()
