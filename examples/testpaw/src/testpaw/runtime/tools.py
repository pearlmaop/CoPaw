from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


ToolFunction = Callable[[dict], str]


@dataclass
class ToolRegistry:
    _tools: dict[str, ToolFunction]

    def has(self, name: str) -> bool:
        return name in self._tools

    def run(self, name: str, args: dict) -> str:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name](args)


def _tool_get_time(_: dict) -> str:
    now = datetime.now(timezone.utc).isoformat()
    return f"UTC time is {now}"


def _tool_calc(args: dict) -> str:
    expr = str(args.get("expr", "")).strip()
    if not expr:
        return "No expression provided"
    allowed = set("0123456789+-*/(). ")
    if any(ch not in allowed for ch in expr):
        return "Expression contains unsupported characters"
    try:
        value = eval(expr, {"__builtins__": {}}, {})
    except Exception:
        return "Expression evaluation failed"
    return f"Result: {value}"


def build_default_tool_registry() -> ToolRegistry:
    return ToolRegistry(
        _tools={
            "get_time": _tool_get_time,
            "calc": _tool_calc,
        },
    )
