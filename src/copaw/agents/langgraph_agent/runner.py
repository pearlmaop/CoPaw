# -*- coding: utf-8 -*-
"""LangGraph-based AgentRunner for CoPaw.

:class:`LangGraphAgentRunner` drives the :class:`~.agent.CoPawLangGraphAgent`
and exposes the same ``query_handler`` async-generator interface used by the
rest of the CoPaw application layer.

It replaces (and is a drop-in for) the AgentScope-based ``AgentRunner``
when the LangGraph backend is selected.

Approval workflow
-----------------
When the ToolGuard pauses the graph via a LangGraph interrupt, the runner
stores the pending session and waits for the user to reply with ``"approve"``
(or ``"/approve"``).  On the next request with the same ``session_id`` the
runner checks for a pending approval and, if found, resumes the graph.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncIterator, Optional, TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage

if TYPE_CHECKING:
    from copaw.agents.memory import BaseMemoryManager
    from copaw.config.config import AgentProfileConfig

logger = logging.getLogger(__name__)

_APPROVE_EXACT = frozenset({"approve", "/approve", "/daemon approve"})


def _is_approval(text: str) -> bool:
    """Return ``True`` when *text* is exactly an approval command."""
    return " ".join(text.split()).lower() in _APPROVE_EXACT


class LangGraphAgentRunner:
    """Async runner that drives a :class:`~.agent.CoPawLangGraphAgent`.

    Args:
        agent_id: CoPaw agent identifier.
        workspace_dir: Optional path to the agent's workspace.
        memory_manager: Optional long-term memory manager.
    """

    def __init__(
        self,
        agent_id: str = "default",
        workspace_dir: Optional[Path] = None,
        memory_manager: "BaseMemoryManager | None" = None,
    ) -> None:
        self.agent_id = agent_id
        self.workspace_dir = workspace_dir
        self.memory_manager = memory_manager

        # Lazily-created LangGraph agent (one per runner instance)
        self._agent: Any = None

        # Track sessions that have an active ToolGuard interrupt
        # Mapping: session_id → True (pending approval)
        self._pending_approvals: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------

    def _get_or_create_agent(self, llm: Any = None) -> Any:
        """Return the shared agent, creating it on first call."""
        if self._agent is None:
            self._agent = self._build_agent(llm=llm)
        return self._agent

    def _build_agent(self, llm: Any = None) -> Any:
        """Instantiate a fresh :class:`~.agent.CoPawLangGraphAgent`."""
        from copaw.config.config import load_agent_config
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent_config: "AgentProfileConfig" = load_agent_config(self.agent_id)

        return CoPawLangGraphAgent(
            agent_config=agent_config,
            memory_manager=self.memory_manager,
            workspace_dir=self.workspace_dir,
            llm=llm,
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def query_handler(
        self,
        query: str,
        session_id: Optional[str] = None,
        llm: Any = None,
    ) -> AsyncIterator[str]:
        """Handle an incoming user query and yield text response chunks.

        The caller should iterate over the yielded strings to stream the
        response to the end user.

        Args:
            query: Raw user input text.
            session_id: Conversation session ID for memory continuity.
            llm: Optional LLM override (useful for testing).

        Yields:
            Text chunks of the agent's response.
        """
        agent = self._get_or_create_agent(llm=llm)

        # Check if this session has a pending ToolGuard approval
        if session_id and session_id in self._pending_approvals:
            if _is_approval(query):
                # Resume the paused graph with "approve"
                logger.info(
                    "Resuming paused agent for session '%s' (approved).",
                    session_id,
                )
                del self._pending_approvals[session_id]
                response = await agent.approve_tool_call(session_id, "approve")
                if response:
                    yield response
                return
            else:
                # User denied: resume with denial
                logger.info(
                    "Resuming paused agent for session '%s' (denied).",
                    session_id,
                )
                del self._pending_approvals[session_id]
                response = await agent.approve_tool_call(session_id, "deny")
                if response:
                    yield response
                else:
                    yield "❌ Tool call denied."
                return

        # Normal query: stream the agent response
        try:
            async for snapshot in agent.astream(query, session_id=session_id):
                messages = snapshot.get("messages", [])
                # Yield the content of the latest AIMessage if it has text
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage):
                        text = CoPawLangGraphAgentRunnerHelper.extract_text(
                            msg
                        )
                        if text:
                            yield text
                        break

        except Exception as exc:
            # Check whether a ToolGuard interrupt paused the graph
            if session_id and _is_interrupt_exception(exc):
                self._pending_approvals[session_id] = True
                interrupt_value = _extract_interrupt_value(exc)
                yield _format_approval_request(interrupt_value)
            else:
                logger.exception(
                    "Agent query failed for session '%s': %s", session_id, exc
                )
                yield f"❌ Agent error: {exc}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


class CoPawLangGraphAgentRunnerHelper:
    """Static helpers to avoid code duplication."""

    @staticmethod
    def extract_text(msg: Any) -> str:
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            return "\n".join(p for p in parts if p)
        return ""


def _is_interrupt_exception(exc: BaseException) -> bool:
    """Return ``True`` when *exc* signals a LangGraph ``interrupt``."""
    # LangGraph raises ``langgraph.errors.GraphInterrupt`` which wraps the
    # interrupt value.  We check the class name to avoid a hard import.
    return type(exc).__name__ in (
        "GraphInterrupt",
        "Interrupt",
        "NodeInterrupt",
    )


def _extract_interrupt_value(exc: BaseException) -> dict:
    """Extract the interrupt payload dict from a LangGraph interrupt error."""
    # GraphInterrupt stores the value in ``.interrupts[0].value``
    interrupts = getattr(exc, "interrupts", None)
    if interrupts:
        return getattr(interrupts[0], "value", {})
    return {}


def _format_approval_request(value: dict) -> str:
    """Format a human-readable approval request message."""
    tool_name = value.get("tool_name", "unknown")
    severity = value.get("severity", "unknown")
    findings = value.get("findings", [])

    lines = [
        f"⚠️ **Tool Guard Alert**",
        f"- Tool: `{tool_name}`",
        f"- Severity: **{severity}**",
    ]
    if findings:
        lines.append("- Findings:")
        for finding in findings[:3]:
            lines.append(f"  - {finding}")

    lines.append("\nType **approve** to allow, or anything else to deny.")
    return "\n".join(lines)
