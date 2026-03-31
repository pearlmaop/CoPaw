from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ToolGuardResult:
    blocked: bool
    reason: str = ""


class ToolGuardEngine:
    """Minimal policy engine with extension point for rule packs."""

    def guard(self, tool_name: str, params: dict) -> ToolGuardResult:
        text = str(params.get("text", "")).lower()
        deny_keywords = ["rm -rf", "drop table", "shutdown -h"]
        for keyword in deny_keywords:
            if keyword in text:
                return ToolGuardResult(blocked=True, reason=f"hit: {keyword}")
        return ToolGuardResult(blocked=False)
