from __future__ import annotations

from typing import Callable

from langgraph.graph import END, START, StateGraph

from testpaw.runtime.state import AgentState
from testpaw.runtime.tools import ToolRegistry
from testpaw.security.tool_guard import ToolGuardEngine


class AgentGraphBuilder:
    def __init__(
        self,
        *,
        tool_guard: ToolGuardEngine,
        tools: ToolRegistry,
        model_reply: Callable[[str], str],
    ) -> None:
        self._tool_guard = tool_guard
        self._tools = tools
        self._model_reply = model_reply

    def compile(self):
        graph = StateGraph(AgentState)

        graph.add_node("normalize", self._normalize)
        graph.add_node("guard", self._guard)
        graph.add_node("plan", self._plan)
        graph.add_node("run_tool", self._run_tool)
        graph.add_node("model_reply", self._model_reply_node)
        graph.add_node("blocked_reply", self._blocked_reply)

        graph.add_edge(START, "normalize")
        graph.add_edge("normalize", "guard")

        graph.add_conditional_edges(
            "guard",
            self._guard_route,
            {
                "blocked": "blocked_reply",
                "ok": "plan",
            },
        )

        graph.add_conditional_edges(
            "plan",
            self._plan_route,
            {
                "tool": "run_tool",
                "model": "model_reply",
            },
        )

        graph.add_edge("run_tool", END)
        graph.add_edge("model_reply", END)
        graph.add_edge("blocked_reply", END)

        return graph.compile()

    @staticmethod
    def _append_trace(state: AgentState, item: str) -> list[str]:
        trace = list(state.get("trace", []))
        trace.append(item)
        return trace

    def _normalize(self, state: AgentState) -> AgentState:
        text = str(state.get("input_text", ""))
        normalized = " ".join(text.split())
        return {
            "normalized_text": normalized,
            "trace": self._append_trace(state, "normalize"),
        }

    def _guard(self, state: AgentState) -> AgentState:
        text = state.get("normalized_text", "")
        result = self._tool_guard.guard("chat_input", {"text": text})
        return {
            "blocked": result.blocked,
            "block_reason": result.reason,
            "trace": self._append_trace(state, "guard"),
        }

    @staticmethod
    def _guard_route(state: AgentState) -> str:
        return "blocked" if state.get("blocked", False) else "ok"

    def _plan(self, state: AgentState) -> AgentState:
        text = state.get("normalized_text", "")
        tool_name = ""
        tool_args: dict = {}

        lower = text.lower()
        if lower in {"/time", "time", "what time is it"}:
            tool_name = "get_time"
        elif lower.startswith("/calc "):
            tool_name = "calc"
            tool_args = {"expr": text[6:].strip()}

        return {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "trace": self._append_trace(state, "plan"),
        }

    @staticmethod
    def _plan_route(state: AgentState) -> str:
        return "tool" if state.get("tool_name") else "model"

    def _run_tool(self, state: AgentState) -> AgentState:
        tool_name = str(state.get("tool_name", ""))
        args = dict(state.get("tool_args", {}))
        if not self._tools.has(tool_name):
            return {
                "response": f"Tool '{tool_name}' not available",
                "trace": self._append_trace(state, "run_tool"),
            }
        tool_result = self._tools.run(tool_name, args)
        return {
            "tool_result": tool_result,
            "response": tool_result,
            "trace": self._append_trace(state, "run_tool"),
        }

    def _model_reply_node(self, state: AgentState) -> AgentState:
        text = state.get("normalized_text", "")
        reply = self._model_reply(text)
        return {
            "response": reply,
            "trace": self._append_trace(state, "model_reply"),
        }

    def _blocked_reply(self, state: AgentState) -> AgentState:
        reason = state.get("block_reason", "policy denied")
        return {
            "response": f"Request blocked by policy: {reason}",
            "trace": self._append_trace(state, "blocked_reply"),
        }
