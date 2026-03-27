# -*- coding: utf-8 -*-
"""LangGraph graph builder for the CoPaw ReAct agent.

The graph implements the classic ReAct loop:

.. code-block:: text

    [START] ──► agent ──► tool_guard ──► tools ──► agent
                  │                        │
                  └─ (no tool calls) ──► [END]

``tool_guard`` is inserted between the agent reasoning step and the tool
execution step.  It inspects each requested tool call and either:

* **allows** it through to ``tools``,
* **blocks** it immediately (for permanently denied tools), or
* **pauses** the graph via :func:`langgraph.types.interrupt` to ask for
  human approval (human-in-the-loop).

When the graph is resumed after an interrupt, the ``tool_guard`` node
receives the human's decision (``"approve"`` or anything else to deny) and
acts accordingly.
"""
from __future__ import annotations

import logging
from typing import Any, Optional, TYPE_CHECKING

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt

from .state import CoPawAgentState

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


def create_copaw_graph(
    llm: "BaseChatModel",
    tools: "list[BaseTool]",
    system_prompt: str = "",
    tool_guard_engine: Any = None,
    checkpointer: Any = None,
    max_iterations: int = 30,
) -> Any:
    """Build and compile the CoPaw LangGraph ReAct agent graph.

    Args:
        llm: A LangChain ``BaseChatModel`` instance (not yet bound to tools).
        tools: List of ``BaseTool`` objects the agent can call.
        system_prompt: System instructions prepended to every conversation.
        tool_guard_engine: Optional :class:`ToolGuardEngine` instance; ``None``
            disables security guarding.
        checkpointer: LangGraph checkpointer for persistent session memory.
            Defaults to ``None`` (no persistence).
        max_iterations: Maximum number of agent-tool cycles before the graph
            raises a recursion error.  Passed to
            :meth:`StateGraph.compile` via ``recursion_limit``.

    Returns:
        A compiled :class:`langgraph.graph.CompiledGraph`.
    """
    llm_with_tools = llm.bind_tools(tools) if tools else llm
    tool_node = ToolNode(tools) if tools else None

    # ------------------------------------------------------------------
    # Graph nodes
    # ------------------------------------------------------------------

    def call_model(state: CoPawAgentState) -> dict:
        """Reasoning node: ask the LLM what to do next."""
        messages = list(state["messages"])
        if system_prompt:
            messages = [SystemMessage(content=system_prompt)] + messages
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def tool_guard_node(state: CoPawAgentState) -> dict:
        """Security guard node: inspect tool calls before execution.

        For permanently-denied tools, a ``ToolMessage`` refusal is injected
        directly.  For guarded (potentially-risky) tools, the graph is
        paused via :func:`langgraph.types.interrupt` until a human resumes
        it with ``"approve"`` or a denial value.
        """
        if tool_guard_engine is None or not getattr(
            tool_guard_engine, "_enabled", True
        ):
            return state

        messages = state["messages"]

        # Find the last AIMessage that contains tool calls
        last_ai_msg: Optional[AIMessage] = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                last_ai_msg = msg
                break

        if last_ai_msg is None:
            return state

        denied_messages: list[ToolMessage] = []
        approved_tool_calls: list[dict] = []

        for tool_call in last_ai_msg.tool_calls:
            tool_name: str = tool_call["name"]
            tool_args: dict = tool_call["args"]
            tool_call_id: str = tool_call["id"]

            # --- Run the guard engine ---
            try:
                guard_result = tool_guard_engine.guard(tool_name, tool_args)
            except Exception as exc:
                logger.warning(
                    "Tool guard check failed for '%s': %s – allowing through.",
                    tool_name,
                    exc,
                )
                approved_tool_calls.append(tool_call)
                continue

            # No findings → safe to execute
            if guard_result is None or not getattr(guard_result, "findings", None):
                approved_tool_calls.append(tool_call)
                continue

            # Permanently denied tool
            if getattr(tool_guard_engine, "is_denied", lambda _: False)(tool_name):
                severity = getattr(
                    getattr(guard_result, "max_severity", None), "value", "high"
                )
                denied_messages.append(
                    ToolMessage(
                        content=(
                            f"⛔ Tool `{tool_name}` is permanently blocked "
                            f"(severity: {severity})."
                        ),
                        tool_call_id=tool_call_id,
                    )
                )
                continue

            # Guarded tool: pause and ask for human approval
            findings = [
                getattr(f, "description", str(f))
                for f in getattr(guard_result, "findings", [])[:3]
            ]
            severity = getattr(
                getattr(guard_result, "max_severity", None), "value", "unknown"
            )

            decision: str = interrupt(
                {
                    "type": "tool_guard",
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "severity": severity,
                    "findings": findings,
                }
            )

            if decision == "approve":
                approved_tool_calls.append(tool_call)
            else:
                denied_messages.append(
                    ToolMessage(
                        content=f"⛔ Tool `{tool_name}` was denied.",
                        tool_call_id=tool_call_id,
                    )
                )

        # --- Synthesize result ---
        if not denied_messages:
            # Nothing denied – pass through unchanged
            return state

        if not approved_tool_calls:
            # All tools denied – skip tool execution entirely
            return {"messages": denied_messages}

        # Mixed: rebuild AI message with only approved calls + inject denials
        new_ai_msg = AIMessage(
            content=last_ai_msg.content,
            tool_calls=approved_tool_calls,
        )
        # Replace last_ai_msg in messages list
        updated: list = [m for m in messages if m is not last_ai_msg]
        updated.append(new_ai_msg)
        updated.extend(denied_messages)
        return {"messages": updated}

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def route_after_guard(state: CoPawAgentState) -> str:
        """After the guard node, route to ``tools`` or back to ``agent``.

        If the guard denied *all* tools (injected only ToolMessages with no
        remaining AIMessage containing tool_calls), we skip the tools node
        and send control back to the agent so it can react to the denials.
        """
        messages = state["messages"]
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                return "tools"
            # Hit a ToolMessage before finding an AIMessage with calls
            if isinstance(msg, ToolMessage):
                break
        return "agent"

    # ------------------------------------------------------------------
    # Build graph
    # ------------------------------------------------------------------

    graph: StateGraph = StateGraph(CoPawAgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tool_guard", tool_guard_node)

    if tool_node is not None:
        graph.add_node("tools", tool_node)
    else:
        # No tools registered: add a no-op node to keep the graph valid
        graph.add_node("tools", lambda state: state)

    graph.set_entry_point("agent")

    # agent → tool_guard (if tool calls) or END
    graph.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tool_guard", "__end__": END},
    )

    # tool_guard → tools or back to agent
    graph.add_conditional_edges(
        "tool_guard",
        route_after_guard,
        {"tools": "tools", "agent": "agent"},
    )

    # tools → agent
    graph.add_edge("tools", "agent")

    compile_kwargs: dict = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer

    compiled = graph.compile(**compile_kwargs)

    # Store max_iterations so callers can pass it in the RunnableConfig
    compiled._copaw_recursion_limit = max_iterations * 2 + 10

    return compiled
