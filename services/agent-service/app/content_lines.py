from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ContentCatalog:
    """读取可审阅的固定文案；缺少目录时回退到行为规则中的模板。"""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._catalogs: dict[str, dict[str, Any]] = {}

    def _read(self, kind: str) -> dict[str, Any]:
        if kind in self._catalogs:
            return self._catalogs[kind]
        filename = {"dialogue": "dialogue-lines.json", "innerOs": "inner-os-lines.json"}.get(kind)
        if not filename:
            return {}
        try:
            value = json.loads((self.root / filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            value = {}
        self._catalogs[kind] = value if isinstance(value, dict) else {}
        return self._catalogs[kind]

    @staticmethod
    def _render(template: str, context: dict[str, Any]) -> str:
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace("{" + str(key) + "}", str(value or ""))
        return rendered

    def resolve(
        self,
        kind: str,
        key: str | None,
        persona_id: str | None,
        context: dict[str, Any],
        fallback: str,
    ) -> str:
        if not key:
            return fallback
        entry = (self._read(kind).get("lines") or {}).get(key)
        if not isinstance(entry, dict):
            return fallback
        variants = entry.get("variants") or {}
        value = variants.get(persona_id) or variants.get("default")
        return self._render(value, context) if isinstance(value, str) else fallback
