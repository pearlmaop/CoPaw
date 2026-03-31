from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    input_text: str
    normalized_text: str
    blocked: bool
    block_reason: str
    tool_name: str
    tool_args: dict
    tool_result: str
    response: str
    trace: list[str]
