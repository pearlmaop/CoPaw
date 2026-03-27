# -*- coding: utf-8 -*-
"""CoPaw LangGraph Agent – main agent class.

:class:`CoPawLangGraphAgent` is a drop-in replacement for the AgentScope-based
``CoPawAgent``.  It drives the ReAct reasoning loop via LangGraph instead of
AgentScope's ``ReActAgent``.

Key capabilities:

* **Tool execution** via LangGraph's :class:`~langgraph.prebuilt.ToolNode`.
* **Security guarding** via CoPaw's :class:`~copaw.security.tool_guard.engine.ToolGuardEngine`
  and LangGraph's native :func:`~langgraph.types.interrupt` for human-in-the-loop approval.
* **Session memory** via LangGraph's :class:`~langgraph.checkpoint.memory.MemorySaver`.
* **Skill instructions** injected into the system prompt from SKILL.md files.
* **Provider-agnostic LLM** created from CoPaw's existing provider config.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncIterator, Optional, TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from .graph import create_copaw_graph
from .llm_factory import create_langchain_llm
from .tools_adapter import adapt_tools

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from copaw.config.config import AgentProfileConfig
    from copaw.agents.memory import BaseMemoryManager

logger = logging.getLogger(__name__)


class CoPawLangGraphAgent:
    """CoPaw agent powered by LangGraph's ReAct graph.

    This class provides the same high-level interface as the AgentScope-based
    ``CoPawAgent`` but uses LangGraph as the underlying execution framework.

    Args:
        agent_config: Agent profile configuration (from ``agent.json``).
        env_context: Optional environment context string prepended to the
            system prompt (e.g., OS info, current time).
        memory_manager: Optional long-term memory manager backend.
        request_context: Optional request metadata (``session_id``,
            ``user_id``, ``channel``, ``agent_id``).
        workspace_dir: Path to the agent's workspace directory.  Falls back
            to ``WORKING_DIR`` when ``None``.
        checkpointer: LangGraph checkpointer for session persistence.  A fresh
            :class:`~langgraph.checkpoint.memory.MemorySaver` is created when
            ``None``.
        llm: Optional pre-built :class:`~langchain_core.language_models.BaseChatModel`.
            Useful for testing without real API keys.
    """

    def __init__(
        self,
        agent_config: "AgentProfileConfig",
        env_context: Optional[str] = None,
        memory_manager: "BaseMemoryManager | None" = None,
        request_context: Optional[dict[str, str]] = None,
        workspace_dir: Optional[Path] = None,
        checkpointer: Any = None,
        llm: Any = None,
    ) -> None:
        self._agent_config = agent_config
        self._env_context = env_context
        self._memory_manager = memory_manager
        self._request_context = dict(request_context or {})
        self._workspace_dir = workspace_dir

        # Build LangChain tools from CoPaw tool functions
        self._tools = self._build_tools()

        # Build the system prompt (workspace markdown + skills)
        self._system_prompt = self._build_system_prompt()

        # Resolve LLM
        if llm is not None:
            self._llm: "BaseChatModel" = llm
        else:
            self._llm = create_langchain_llm(agent_id=agent_config.id)

        # Checkpointer (in-memory by default)
        self._checkpointer = checkpointer if checkpointer is not None else MemorySaver()

        # Tool guard engine
        self._tool_guard_engine = self._get_tool_guard_engine()

        # Compile the LangGraph graph
        self._graph = create_copaw_graph(
            llm=self._llm,
            tools=self._tools,
            system_prompt=self._system_prompt,
            tool_guard_engine=self._tool_guard_engine,
            checkpointer=self._checkpointer,
            max_iterations=agent_config.running.max_iters,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def reply(
        self,
        query: str,
        session_id: Optional[str] = None,
    ) -> str:
        """Process a user query and return the agent's final text response.

        Args:
            query: User input text.
            session_id: Conversation session ID for memory continuity.
                Defaults to the ``session_id`` in ``request_context``.

        Returns:
            The agent's final text response as a plain string.
        """
        config = self._get_thread_config(session_id)
        input_state = {
            "messages": [HumanMessage(content=query)],
            "session_id": session_id
            or self._request_context.get("session_id")
            or "",
            "agent_id": self._agent_config.id,
        }

        final_state = await self._graph.ainvoke(input_state, config=config)
        return self._extract_last_ai_text(final_state.get("messages", []))

    async def astream(
        self,
        query: str,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[dict]:
        """Stream agent state snapshots as the graph executes.

        Each yielded dict represents a complete ``CoPawAgentState`` snapshot
        after the most recent node update.

        Args:
            query: User input text.
            session_id: Conversation session ID.

        Yields:
            State snapshots (``dict`` matching :class:`~.state.CoPawAgentState`).
        """
        config = self._get_thread_config(session_id)
        input_state = {
            "messages": [HumanMessage(content=query)],
            "session_id": session_id
            or self._request_context.get("session_id")
            or "",
            "agent_id": self._agent_config.id,
        }

        async for snapshot in self._graph.astream(
            input_state,
            config=config,
            stream_mode="values",
        ):
            yield snapshot

    def get_state(self, session_id: Optional[str] = None) -> Any:
        """Return the current LangGraph state snapshot for a session.

        Args:
            session_id: Conversation session ID.

        Returns:
            A :class:`~langgraph.pregel.StateSnapshot` or ``None`` if no
            state exists for the given session.
        """
        config = self._get_thread_config(session_id)
        return self._graph.get_state(config)

    async def approve_tool_call(
        self,
        session_id: str,
        decision: str = "approve",
    ) -> Optional[str]:
        """Resume an agent that is paused at a tool-guard approval interrupt.

        Args:
            session_id: Session ID of the paused agent.
            decision: ``"approve"`` to allow the tool; any other value denies it.

        Returns:
            The agent's text response after resumption, or ``None`` if there
            was no pending interrupt.
        """
        config = self._get_thread_config(session_id)
        state = self._graph.get_state(config)

        if not state or not state.next:
            logger.debug(
                "No pending interrupt for session '%s'; ignoring approve_tool_call.",
                session_id,
            )
            return None

        final_state = await self._graph.ainvoke(
            Command(resume=decision),
            config=config,
        )
        return self._extract_last_ai_text(final_state.get("messages", []))

    @property
    def tools(self) -> list:
        """Return the list of LangChain tools registered with this agent."""
        return list(self._tools)

    @property
    def system_prompt(self) -> str:
        """Return the current system prompt."""
        return self._system_prompt

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _build_tools(self) -> list:
        """Build LangChain tools from enabled CoPaw built-in tool functions."""
        from copaw.agents.tools import (
            execute_shell_command,
            read_file,
            write_file,
            edit_file,
            grep_search,
            glob_search,
            browser_use,
            desktop_screenshot,
            send_file_to_user,
            get_current_time,
            set_user_timezone,
            get_token_usage,
        )
        from copaw.agents.prompt import get_active_model_supports_multimodal

        all_tool_functions = [
            execute_shell_command,
            read_file,
            write_file,
            edit_file,
            grep_search,
            glob_search,
            browser_use,
            desktop_screenshot,
            send_file_to_user,
            get_current_time,
            set_user_timezone,
            get_token_usage,
        ]

        # Respect per-tool enable/disable flags from agent config
        enabled_map: dict[str, bool] = {}
        try:
            if hasattr(self._agent_config, "tools") and hasattr(
                self._agent_config.tools, "builtin_tools"
            ):
                enabled_map = {
                    name: tool.enabled
                    for name, tool in self._agent_config.tools.builtin_tools.items()
                }
        except Exception as exc:
            logger.warning("Failed to read tool config: %s – all tools enabled.", exc)

        multimodal: bool = get_active_model_supports_multimodal()

        # Tools that require multimodal (vision) model support
        _MULTIMODAL_ONLY_TOOLS = frozenset({"view_image"})

        filtered = [
            fn
            for fn in all_tool_functions
            if enabled_map.get(fn.__name__, True)
            and not (fn.__name__ in _MULTIMODAL_ONLY_TOOLS and not multimodal)
        ]

        return adapt_tools(filtered)

    def _build_system_prompt(self) -> str:
        """Construct the system prompt from workspace markdown files and skills."""
        from copaw.agents.prompt import build_system_prompt_from_working_dir
        from copaw.constant import WORKING_DIR

        workspace_dir = self._workspace_dir or WORKING_DIR

        sys_prompt = build_system_prompt_from_working_dir(
            working_dir=workspace_dir,
            agent_id=self._agent_config.id,
        )

        # Append skill instructions so the agent knows about available skills
        skills_section = self._build_skills_prompt()
        if skills_section:
            sys_prompt = f"{sys_prompt}\n\n{skills_section}"

        if self._env_context:
            sys_prompt = f"{sys_prompt}\n\n{self._env_context}"

        return sys_prompt

    def _build_skills_prompt(self) -> str:
        """Build a skills section for the system prompt from SKILL.md files."""
        from copaw.agents.skills_manager import (
            ensure_skills_initialized,
            list_available_skills,
            get_working_skills_dir,
        )
        from copaw.constant import WORKING_DIR

        workspace_dir = self._workspace_dir or WORKING_DIR

        try:
            ensure_skills_initialized(workspace_dir)
            available_skills = list_available_skills(workspace_dir)
            if not available_skills:
                return ""

            skills_dir = get_working_skills_dir(workspace_dir)
            sections: list[str] = []

            for skill_name in available_skills:
                skill_md_path = skills_dir / skill_name / "SKILL.md"
                if skill_md_path.exists():
                    content = skill_md_path.read_text(encoding="utf-8")
                    sections.append(f"## Skill: {skill_name}\n\n{content}")

            if sections:
                return "# Available Skills\n\n" + "\n\n---\n\n".join(sections)

        except Exception as exc:
            logger.warning("Could not load skills: %s", exc)

        return ""

    def _get_tool_guard_engine(self) -> Any:
        """Return the singleton :class:`ToolGuardEngine`, or ``None`` on error."""
        try:
            from copaw.security.tool_guard.engine import get_guard_engine

            return get_guard_engine()
        except Exception as exc:
            logger.warning(
                "Could not initialise tool guard engine: %s – guards disabled.",
                exc,
            )
            return None

    def _get_thread_config(self, session_id: Optional[str] = None) -> dict:
        """Build the LangGraph thread config for session isolation."""
        thread_id = (
            session_id
            or self._request_context.get("session_id")
            or "default"
        )
        config: dict = {"configurable": {"thread_id": thread_id}}
        # Pass the recursion_limit from the compiled graph if set
        recursion_limit = getattr(self._graph, "_copaw_recursion_limit", None)
        if recursion_limit is not None:
            config["recursion_limit"] = recursion_limit
        return config

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_last_ai_text(messages: list) -> str:
        """Return the text content of the last ``AIMessage`` in *messages*."""
        for msg in reversed(messages):
            if not isinstance(msg, AIMessage):
                continue
            content = msg.content
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
