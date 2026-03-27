# -*- coding: utf-8 -*-
"""Agent state definition for CoPaw LangGraph agent."""
from __future__ import annotations

from typing import Annotated, Optional

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class CoPawAgentState(TypedDict):
    """State for the CoPaw LangGraph ReAct agent.

    Attributes:
        messages: Conversation history with reducer that appends new messages.
        session_id: Optional session identifier for conversation continuity.
        agent_id: Optional agent identifier.
    """

    messages: Annotated[list, add_messages]
    session_id: Optional[str]
    agent_id: Optional[str]
